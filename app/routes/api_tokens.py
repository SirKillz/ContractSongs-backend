import logging

from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.models import CurrentUser

from app.database.database import get_db
from app.database.models import SpotifyApiTokens

from app.schemas.api_keys import ReadSpotifyApiKeys, CreateSpotifyApiKeys, GetSpotifyApiTokens
from app.routes.helpers import parse_str_to_datetime, get_token_expiration

from app.services.spotify.session import request_tokens_with_code

api_key_router = APIRouter(prefix="/api/v1/api-keys", tags=["API KEY Management"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py



@api_key_router.get("", response_model=ReadSpotifyApiKeys)
async def get_api_keys(db: Session = Depends(get_db)):

    logger.info(f"Received Request at GET: /api/v1/api-keys")

    stmt = select(SpotifyApiTokens).where(SpotifyApiTokens.id == 1)
    result = db.execute(stmt).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="Spotify API Tokens have NOT been set")

    return result



@api_key_router.get("/proxy/spotify/get-tokens", response_model=GetSpotifyApiTokens)
async def get_spotify_tokens_with_code(code: str):

    logger.info(f"Received Request at GET: /api/v1/api-keys/proxy/spotify/get-tokens")

    try:
        spotify_tokens = request_tokens_with_code(code)
        expires_at = spotify_tokens.get("expires_at")
        expiration_timestamp = get_token_expiration(expires_at)
        return {
            "access_token": spotify_tokens.get("access_token"),
            "token_type": spotify_tokens.get("token_type"),
            "scope": spotify_tokens.get("scope"),
            "access_token_expires_at": expiration_timestamp,
            "refresh_token": spotify_tokens.get("refresh_token")
        }
    except:
        raise HTTPException(status_code=500, detail="Error retrieving Spotify Tokens")




@api_key_router.post("", response_model=ReadSpotifyApiKeys)
async def create_api_keys(
    api_key_data: CreateSpotifyApiKeys,
    db: Session = Depends(get_db), 
):
    logger.info(f"Received Request at POST: /api/v1/api-keys")

    # Check if a token pair already exists
    stmt = select(SpotifyApiTokens).where(SpotifyApiTokens.id == 1)
    result = db.execute(stmt).scalar_one_or_none()
    if result:
        raise HTTPException(status_code=409, detail="Spotify keys already exist, please update existing")

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

