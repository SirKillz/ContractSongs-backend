import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session_factory import get_db
from app.database.models import ContractSongSession, Player

from app.schemas.session import ReadSession, CreateSession, DeleteSession
from app.schemas.player import ReadPlayer
from app.routes.helpers import parse_str_to_datetime, get_new_access_token_expiration
from app.services.contract_song_events import contract_song_queue, publish_to_queue

session_router = APIRouter(prefix="/api/v1/sessions", tags=["Session"])
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

@session_router.get("/contract-song-events", response_class=EventSourceResponse)
async def yield_contract_song_events():

    while True:
        
        # Waits and saves CPU
        # Does not infinite loop
        # Wakes as soon as there is an item within the Queue
        event = await contract_song_queue.get()
        logger.info(f"SSE route received event from queue: {event}")
        yield ServerSentEvent(
            event=event["type"],
            data=event,
        )

@session_router.post("/contract-song-events/test")
async def send_test_event():

    event = {
        "type": "contract_song",
        "session_id": "test_session_id",
        "audio_url": f"http://localhost:8000/contract-song-audio-out/test-Nick Killeen.mp3",
        "player_names": ["Nick Killeen"],
        "song_id": "test_song_id",
        "song_name": "test_song_name"
    }
    await publish_to_queue(event)
    return {
        "published_test_event": True
    }


@session_router.get("", response_model=list[ReadSession])
async def get_sessions(db: Session = Depends(get_db)):
   logger.info(f"Received Request at GET: /api/v1/sessions")

   stmt = select(ContractSongSession)
   contract_song_sessions = db.execute(stmt).scalars().all()

   return contract_song_sessions


@session_router.get("/{session_id}", response_model=ReadSession)
async def get_session(session_id: int, db: Session = Depends(get_db)):

    logger.info(f"Received Request at GET: /api/v1/sessions{session_id}")

    stmt = select(ContractSongSession).where(ContractSongSession.id == session_id)
    result = db.execute(stmt).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail=f"Session with id: {session_id} not found")

    return result

@session_router.delete("/{session_id}", response_model=DeleteSession) 
async def delete_session(session_id: int, db: Session = Depends(get_db)):
    logger.info(f"Received Request at DELETE: /api/v1/sessions{session_id}")

    stmt = select(ContractSongSession).where(ContractSongSession.id == session_id)
    contract_song_session = db.execute(stmt).scalar_one_or_none()

    if not contract_song_session:
        raise HTTPException(status_code=404, detail=f"Session with id: {session_id} not found")
    
    # Handle player deletion first
    for player in contract_song_session.players:
        db.delete(player)
    db.commit()

    db.delete(contract_song_session)
    db.commit()
    return {
        "deleted": True
    }

@session_router.get("/{session_id}/players", response_model=list[ReadPlayer])
async def get_session_players(session_id: int, db: Session = Depends(get_db)):

    logger.info(f"Received Request at GET: /api/v1/sessions{session_id}/players")

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
    logger.info(f"Received Request at POST: /api/v1/sessions")

    # Dump Payload
    payload = session_data.model_dump()

    # Create the session first
    contract_song_session = ContractSongSession(
        playlist_id=payload.get("playlist_id"),
        playlist_name=payload.get("playlist_name")
    )
    db.add(contract_song_session)
    db.commit()
    db.refresh(contract_song_session)

    # Create the Players Next
    players_to_add = []
    for player in payload.get("players", []):
        session_player = Player(
            session_id=contract_song_session.id,
            name=player.get("name"),
            songs=player.get("songs")
        )
        players_to_add.append(session_player)
    if len(players_to_add) > 0:
        db.add_all(players_to_add)
        db.commit()


    return contract_song_session
