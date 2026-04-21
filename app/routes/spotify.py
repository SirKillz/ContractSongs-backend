import os
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database.session_factory import SessionLocal
from app.database.models import SpotifyApiTokens

from app.services.spotify.client import SpotifyClient
from app.services.spotify.types import SpotifyTokenSnapshot, SpotifyPlaylist, SpotifySong
from app.services.spotify.session import ApiSession, request_token_via_refresh
from app.schemas.spotify import GetPlaylists

from app.routes.helpers import get_new_access_token_expiration


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

# GLOBALS DEFINED FOR THE POLLING PROCESS
MONITOR_TASK = None
MONITOR_RUNNING = False

async def spotify_poll_loop(polling_interval: float = 10.0, max_iterations: int | None = None):

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
            song_name = current_track_data.get("item").get("name")
            logger.info(f"The name of the currently playing song is: {song_name}")

            iteration_count += 1
            if max_iterations is not None and iteration_count >= max_iterations:
                MONITOR_RUNNING = False
                break

            await asyncio.sleep(polling_interval)
    finally:
        await session.close()
        MONITOR_RUNNING = False
        MONITOR_TASK = None


@spotify_router.post("/start-contract-song-service")
async def start_contract_song_service():
    global MONITOR_TASK
    if MONITOR_TASK is None:
        MONITOR_TASK = asyncio.create_task(spotify_poll_loop())
        return {"started": True}
    return {"started": False, "reason": "already running"}


@spotify_router.post("/stop-contract-song-service")
async def stop_contract_song_service():
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
    raw_playlists_data = await client.get_current_users_playlists()
    raw_playlists: list[dict] = raw_playlists_data.get("items")

    playlists = []
    for playlist in raw_playlists:
        pl = SpotifyPlaylist(
            id=playlist.get("id"),
            name=playlist.get("name"),
            songs=[]
        )
        playlists.append(pl)
    return {
        "count": len(playlist),
        "playlists": playlists
    }
