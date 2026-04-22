import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session_factory import get_db
from app.database.models import ContractSongSession

from app.schemas.session import ReadSession, CreateSession
from app.schemas.player import ReadPlayer
from app.routes.helpers import parse_str_to_datetime, get_new_access_token_expiration

session_router = APIRouter(prefix="/api/v1/session", tags=["Session"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py



@session_router.get("/{session_id}", response_model=ReadSession)
async def get_session(session_id: int, db: Session = Depends(get_db)):

    logger.info(f"Received Request at GET: /api/v1/session{session_id}")

    stmt = select(ContractSongSession).where(ContractSongSession.id == session_id)
    result = db.execute(stmt).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail=f"Session with id: {session_id} not found")

    return result

@session_router.get("/{session_id}/players", response_model=list[ReadPlayer])
async def get_session_players(session_id, db: Session = Depends(get_db)):

    logger.info(f"Received Request at GET: /api/v1/session{session_id}/players")

    stmt = select(ContractSongSession).where(ContractSongSession.id == session_id)
    contract_song_session = db.execute(stmt).scalar_one_or_none()

    if not contract_song_session:
        raise HTTPException(status_code=404, detail=f"Session with id: {session_id} not found")

    players = contract_song_session.players
    return players


@session_router.post("", response_model=ReadSession)
async def create_session(
    session_data: CreateSession,
    db: Session = Depends(get_db), 
):
    logger.info(f"Received Request at POST: /api/v1/session")

    # Dump Payload
    payload = session_data.model_dump()

    contract_song_session = ContractSongSession(**payload)
    db.add(contract_song_session)
    db.commit()
    db.refresh(contract_song_session)

    return contract_song_session
