import logging

from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.models import CurrentUser

from app.database.database import get_db
from app.database.models import SpotifyApiTokens

from app.schemas.api_keys import ReadSpotifyApiKeys, CreateSpotifyApiKeys
from app.routes.helpers import parse_str_to_datetime

api_key_router = APIRouter(prefix="/api/v1/api-keys", tags=["API KEY Management"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

@api_key_router.get("", response_model=ReadSpotifyApiKeys)
async def get_api_keys(db: Session = Depends(get_db), current_user: CurrentUser = Security(get_current_user)):

    logger.info(f"[User: {current_user.username or current_user.sub}] -  Received Request at GET: /api/v1/api-keys")

    stmt = select(SpotifyApiTokens).where(SpotifyApiTokens.id == 1)
    result = db.execute(stmt).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="Spotify API Tokens have NOT been set")

    return result

@api_key_router.post("", response_model=ReadSpotifyApiKeys)
async def create_api_keys(
    api_key_data: CreateSpotifyApiKeys,
    db: Session = Depends(get_db), 
    current_user: CurrentUser = Security(get_current_user),
):
    logger.info(f"[User: {current_user.username or current_user.sub}] -  Received Request at POST: /api/v1/api-keys")

    # Convert access_token_expires_at from str -> datetime
    expires_at = parse_str_to_datetime(api_key_data.access_token_expires_at)

    spotify_api_token_pair = SpotifyApiTokens(
        access_token=api_key_data.access_token,
        token_type=api_key_data.token_type,
        scope=api_key_data.scope,
        access_token_expires_at=expires_at,
        refresh_token=api_key_data.refresh_token
    )

    db.add(spotify_api_token_pair)
    db.commit()
    db.refresh(spotify_api_token_pair)

    return spotify_api_token_pair

