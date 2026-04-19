import os
import sys
import logging

from fastapi import FastAPI
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_CORS")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_router)
app.include_router(users_router)