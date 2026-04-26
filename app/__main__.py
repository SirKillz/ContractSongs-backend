import os
import sys
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.routes import *

# Configure the root Logger
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)  # Set logging level

# Check if handlers are already set (prevents duplicate logs in AWS Lambda)
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)  # Set logging level

    handler = logging.StreamHandler(sys.stdout)  # Send logs to stdout
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)  # Attach handler

app = FastAPI()
handler = Mangum(app)

BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "contract-song-audio-out"

AUDIO_DIR.mkdir(exist_ok=True)

app.mount(
    "/contract-song-audio-out",
    StaticFiles(directory=AUDIO_DIR),
    name="contract-song-audio-out",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_key_router)
app.include_router(spotify_router)
app.include_router(session_router)
app.include_router(players_router)
