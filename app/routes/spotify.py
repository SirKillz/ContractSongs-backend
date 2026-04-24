import os
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database.session_factory import SessionLocal
from app.database.models import SpotifyApiTokens, ContractSongSession

from app.services.spotify.client import SpotifyClient
from app.services.spotify.types import SpotifyTokenSnapshot, SpotifyPlaylist, SpotifySong
from app.services.spotify.session import ApiSession, request_token_via_refresh
from app.schemas.spotify import GetPlaylists

from app.routes.helpers import get_new_access_token_expiration

from app.services.contract_song_events import publish_to_queue, contract_song_queue


spotify_router = APIRouter(prefix="/api/v1/spotify", tags=["Spotify"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

# Helper function to return Spotify API tokens stored in DB
def get_spotify_api_tokens_from_db() -> SpotifyTokenSnapshot:
    """
    Requests the Spotify API Tokens which are stored within the DB
    """

    with SessionLocal() as db:
        stmt = select(SpotifyApiTokens)
        result = db.execute(stmt).scalar_one()
        return SpotifyTokenSnapshot(
            access_token=result.access_token,
            access_token_expires_at=result.access_token_expires_at,
            refresh_token=result.refresh_token,
        )

# Helper function to evaluate token expiration
def access_token_expired(expires_timestamp: datetime) -> bool:
    """
    Checks to see if the access token is expired
    Returns True if expired
    Returns False if NOT expired
    """

    now = datetime.now(timezone.utc)
    if now > expires_timestamp:
        return True
    
    return False

# Helper function to request new access token from spotify and update stored DB values
def refresh_access_token(expired_tokens: SpotifyTokenSnapshot) -> SpotifyTokenSnapshot:
    """
    Takes in the expired tokens and db session 
    Requests new access token from spotify
    Updates and return ORM object in Database
    """

    with SessionLocal() as db:

        refreshed_tokens = request_token_via_refresh(expired_tokens.refresh_token)
        new_expiration_timestamp = get_new_access_token_expiration(3600)

        stmt = (
            update(SpotifyApiTokens)
            .where(SpotifyApiTokens.id == 1)
            .values(
                access_token=refreshed_tokens.get("access_token"),
                access_token_expires_at=new_expiration_timestamp
            )
        )
        db.execute(stmt)
        db.commit()
        return SpotifyTokenSnapshot(
            access_token=refreshed_tokens.get("access_token"),
            access_token_expires_at=new_expiration_timestamp,
            refresh_token=expired_tokens.refresh_token,
        )

def get_players_for_currently_playing_song(current_session_id: int, current_song_id: str, current_song_name: str) -> list[str]:
    with SessionLocal() as db:
        stmt = select(ContractSongSession).where(ContractSongSession.id == current_session_id)
        contract_song_session = db.execute(stmt).scalar_one_or_none()
        if not contract_song_session:
            return # to do figure out how to handle this
        
        players_for_this_song = []
        for player in contract_song_session.players:
            updated_songs = []
            for song in player.songs:
                # Current songs needs to NOT have already been contracted AND match the current song ID or Name
                if (
                    song.get("been_contracted") == False
                    and (song.get("id") == current_song_id or song.get("name") == current_song_name)
                ):
                    player.contract_count += 1
                    if player.name not in players_for_this_song:
                        players_for_this_song.append(player.name)
                    
                    # Update to indicate that the song has now been contracted so it gets skipped next time
                    updated_songs.append({
                        "id": song.get("id"),
                        "name": song.get("name"),
                        "artist": song.get("artist"),
                        "been_contracted": True
                    })
                else:
                    updated_songs.append(song)
            player.songs = updated_songs
        db.commit()
        return players_for_this_song



# GLOBALS DEFINED FOR THE POLLING PROCESS
MONITOR_TASK = None
MONITOR_RUNNING = False

async def spotify_poll_loop(session_id: int, polling_interval: float = 10.0, max_iterations: int | None = None):

    # Globals
    global MONITOR_TASK, MONITOR_RUNNING

    # Grab stored tokens and refresh if necessary
    stored_spotify_tokens = get_spotify_api_tokens_from_db()
    if access_token_expired(stored_spotify_tokens.access_token_expires_at):
        stored_spotify_tokens = refresh_access_token(stored_spotify_tokens)

    # API Session Setup
    session = ApiSession(
        base_url=os.getenv("SPOTIFY_BASE_API_URL"),
        access_token=stored_spotify_tokens.access_token
    )
    client = SpotifyClient(session)

    # Start the monitor:
    MONITOR_RUNNING = True
    iteration_count = 0
    try:
        while MONITOR_RUNNING:
            current_track_data = await client.get_currently_playing_track()
            song_id = current_track_data.get("item").get("id")
            song_name = current_track_data.get("item").get("name")

            players_for_this_song = get_players_for_currently_playing_song(session_id, song_id, song_name)
            logger.info(f"The name of the currently playing song is: {song_name}")
            if len(players_for_this_song) > 0:
                logger.info(f"WE HAVE A CONTRACT SONG MATCH FOR {', '.join(players_for_this_song)}")
                await publish_to_queue(event={
                        "type": "contract_song",
                        "session_id": session_id,
                        "audio_url": "http://localhost:8000/contract-song-audio/test-song-1-Nick.mp3",
                        "player_names": players_for_this_song,
                        "song_id": song_id,
                        "song_name": song_name
                    }
                )
            else:
                logger.info("No matching players")

            iteration_count += 1
            if max_iterations is not None and iteration_count >= max_iterations:
                MONITOR_RUNNING = False
                break

            await asyncio.sleep(polling_interval)
    finally:
        await session.close()
        MONITOR_RUNNING = False
        MONITOR_TASK = None


@spotify_router.post("/session/{session_id}/start-contract-song-service")
async def start_contract_song_service(session_id: int):
    global MONITOR_TASK
    if MONITOR_TASK is None:
        MONITOR_TASK = asyncio.create_task(spotify_poll_loop(session_id))
        return {"started": True}
    return {"started": False, "reason": "already running"}


@spotify_router.post("/session/{session_id}/stop-contract-song-service")
async def stop_contract_song_service(session_id):
    global MONITOR_RUNNING
    MONITOR_RUNNING = False
    return {"stopping": True}

@spotify_router.get("/playlists", response_model=GetPlaylists)
async def get_playlists():

    # Initial token handling on the backend
    current_tokens = get_spotify_api_tokens_from_db()
    if access_token_expired(current_tokens.access_token_expires_at):
        current_tokens = refresh_access_token(current_tokens)

    api_session = ApiSession(
        base_url=os.getenv("SPOTIFY_BASE_API_URL"),
        access_token=current_tokens.access_token
    )
    client = SpotifyClient(api_session)

    # Params
    params = {
        "limit": 50,
        "offset": 0
    }

    total_playlists = []
    total_user_playlists = 0 # initially set at 0

    while (len(total_playlists) == 0 or len(total_playlists) < total_user_playlists):
        raw_playlists_data = await client.get_current_users_playlists(params=params)
        total_user_playlists = raw_playlists_data.get("total")
        raw_playlists: list[dict] = raw_playlists_data.get("items")

        for playlist in raw_playlists:
            pl = SpotifyPlaylist(
                id=playlist.get("id"),
                name=playlist.get("name"),
                songs=[]
            )
            total_playlists.append(pl)

        params['offset'] = len(total_playlists)
    return {
        "count": total_user_playlists,
        "playlists": total_playlists
    }

@spotify_router.get("/playlists/{playlist_id}/songs", response_model=list[SpotifySong])
async def get_playlist_songs(playlist_id: str):

    # Initial token handling on the backend
    current_tokens = get_spotify_api_tokens_from_db()
    if access_token_expired(current_tokens.access_token_expires_at):
        current_tokens = refresh_access_token(current_tokens)

    session = ApiSession(base_url=os.getenv("SPOTIFY_BASE_API_URL"), access_token=current_tokens.access_token)
    client = SpotifyClient(session)

    # Limit Returned Data
    fields=f"total,limit,items(item(id,name,artists))"
    params = {
        "fields": fields,
        "limit": 100,
        "offset": 0
    }

    full_playlist_songs = []
    total_songs_in_playlist = 0 # initial set

    while (len(full_playlist_songs) == 0 or len(full_playlist_songs) < total_songs_in_playlist):
        
        raw_playlist_items = await client.get_playlist_songs(playlist_id, params=params)
        total_songs_in_playlist = raw_playlist_items.get("total")
        
        # Break loop if there are no songs in the playlist
        if total_songs_in_playlist == 0:
            break
        
        for item in raw_playlist_items.get("items"):
            item = item.get("item")
            artists = item.get("artists")
            if len(artists) > 0:
                artist = artists[0].get("name")
            else:
                artist = ""

            id = item.get("id")
            name = item.get("name")

            playlist_song = {
                "id": id,
                "name": name,
                "artist": artist 
            }
            full_playlist_songs.append(playlist_song)
        
        params['offset'] = len(full_playlist_songs)
        
        
    return full_playlist_songs
