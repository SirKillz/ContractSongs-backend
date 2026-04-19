import logging

from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.models import CurrentUser

from app.database.database import get_db
from app.database.models import SpotifyApiTokens

from app.schemas.api_keys import SpotifyApiKeys

api_key_router = APIRouter(prefix="/api/v1/api-keys", tags=["API KEY Management"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

@api_key_router.get("", response_model=SpotifyApiKeys)
async def test(db: Session = Depends(get_db), current_user: CurrentUser = Security(get_current_user)):

    logger.info(f"[User: {current_user.username or current_user.sub}] -  Received Request at /api/v1/")

    stmt = select(SpotifyApiTokens).where(SpotifyApiTokens.id == 1)
    result = db.execute(stmt).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="Spotify API Tokens have NOT been set")

    return result