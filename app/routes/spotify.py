import os
import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.database.session_factory import get_db
from app.database.models import SpotifyApiTokens
from app.services.spotify.session import ApiSession, request_token_via_refresh
from app.routes.helpers import get_new_access_token_expiration
from app.services.spotify.client import SpotifyClient

spotify_router = APIRouter(prefix="/api/v1/spotify", tags=["Spotify"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

# Helper function to return Spotify API tokens stored in DB
def get_spotify_api_tokens_from_db(db: Session) -> SpotifyApiTokens:
    """
    Requests the Spotify API Tokens which are stored within the DB
    """

    stmt = select(SpotifyApiTokens)
    result = db.execute(stmt).scalar_one()
    return result

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
def refresh_access_token(expired_tokens: SpotifyApiTokens, db: Session) -> SpotifyApiTokens:
    """
    Takes in the expired tokens and db session 
    Requests new access token from spotify
    Updates and return ORM object in Database
    """

    refreshed_tokens = request_token_via_refresh(expired_tokens.refresh_token)
    new_expiration_timestamp = get_new_access_token_expiration(3600)

    stmt = (
        update(SpotifyApiTokens)
        .where(SpotifyApiTokens.id == expired_tokens.id)
        .values(
            access_token=refreshed_tokens.get("access_token"),
            access_token_expires_at=new_expiration_timestamp
        )
        .returning(SpotifyApiTokens)
    )
    result = db.execute(stmt).scalar_one()
    db.commit()
    return result

# GLOBALS DEFINED FOR THE POLLING PROCESS
MONITOR_TASK = None
MONITOR_RUNNING = False

async def spotify_poll_loop(db: Session, polling_interval: float = 10.0):

    # Globals
    global MONITOR_TASK, MONITOR_RUNNING

    # Grab stored tokens and refresh if necessary
    stored_spotify_tokens = get_spotify_api_tokens_from_db(db)
    if access_token_expired(stored_spotify_tokens.access_token_expires_at):
        stored_spotify_tokens = refresh_access_token(stored_spotify_tokens, db)

    # API Session Setup
    session = ApiSession(
        base_url=os.getenv("SPOTIFY_BASE_API_URL"),
        access_token=stored_spotify_tokens.access_token
    )
    client = SpotifyClient(session)

    # Start the monitor:
    MONITOR_RUNNING = True
    while MONITOR_RUNNING:
        try: 
            current_track_data = await client.get_currently_playing_track()
            song_name = current_track_data.get("item").get("name")
            logger.info(f"The name of the currently playing song is: {song_name}")
            await asyncio.sleep(polling_interval)
        finally:
            MONITOR_RUNNING = False
            MONITOR_TASK = None


@spotify_router.post("/start-contract-song-service")
async def start_contract_song_service(db: Session = Depends(get_db)):
    global MONITOR_TASK
    if MONITOR_TASK is None:
        MONITOR_TASK = asyncio.create_task(spotify_poll_loop(db))
        return {"started": True}
    return {"started": False, "reason": "already running"}


@spotify_router.post("/stop-contract-song-service")
async def stop_contract_song_service(db: Session = Depends(get_db)):
    global MONITOR_RUNNING
    MONITOR_RUNNING = False
    return {"stopping": True}
