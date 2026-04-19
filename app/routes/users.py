import logging

from fastapi import APIRouter, Security, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.auth.current_user import get_current_user
from app.auth.models import CurrentUser

from app.database.database import get_db
from app.database.models import User

from app.schemas.user import UserRead

users_router = APIRouter()
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

@users_router.get("/users/{user_id}", response_model=UserRead)
async def test(user_id: int, db: Session = Depends(get_db), current_user: CurrentUser = Security(get_current_user)):

    logger.info(f"[User: {current_user.username or current_user.sub}] -  Received Request at /users/{id}")

    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt).scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return result