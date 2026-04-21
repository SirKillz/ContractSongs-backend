import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import SpotifyApiTokens
from app.services.spotify.session import request_token_via_refresh
from app.routes.helpers import get_new_access_token_expiration

spotify_router = APIRouter(prefix="/api/v1/spotify", tags=["Spotify"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

# Helper function to return Spotify API tokens stored in DB
def get_spotify_api_tokens(db: Session) -> SpotifyApiTokens:
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

