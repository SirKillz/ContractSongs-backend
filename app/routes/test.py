import logging

from fastapi import APIRouter, Security
from app.auth.current_user import get_current_user
from app.auth.models import CurrentUser

test_router = APIRouter()
logger = logging.getLogger("app_logger") # Configure inside app/__main__.py

@test_router.get("/test")
async def test(current_user: CurrentUser = Security(get_current_user)):

    logger.info(f"[User: {current_user.username or current_user.sub}] -  Received Request at /test")

    return {"message": "Hello World"}