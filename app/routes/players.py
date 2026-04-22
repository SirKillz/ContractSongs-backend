import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session_factory import get_db
from app.database.models import Player

from app.schemas.player import ReadPlayer, CreatePlayer
from app.routes.helpers import parse_str_to_datetime, get_new_access_token_expiration

players_router = APIRouter(prefix="/api/v1/session/{session_id}/players", tags=["Players"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py



@players_router.get("/{player_id}", response_model=ReadPlayer)
async def get_player(session_id: int, player_id: int, db: Session = Depends(get_db)):

    logger.info(f"Received Request at GET: /api/v1/session{session_id}/player/{player_id}")

    stmt = select(Player).where(Player.id == player_id and Player.session_id == session_id)
    player = db.execute(stmt).scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id: {player_id} not found")

    return player



@players_router.post("", response_model=ReadPlayer)
async def create_player(
    session_id: int,
    player_data: CreatePlayer,
    db: Session = Depends(get_db), 
):
    logger.info(f"Received Request at POST: /api/v1/session")

    # Dump Payload
    payload = player_data.model_dump()
    payload['session_id'] = session_id

    player = Player(**payload)
    db.add(player)
    db.commit()
    db.refresh(player)

    return player
