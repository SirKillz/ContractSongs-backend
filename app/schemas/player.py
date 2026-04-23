from datetime import datetime
from dataclasses import field

from pydantic import BaseModel, ConfigDict, Field

from app.services.spotify.types import SpotifySong

class ReadPlayer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    name: str
    songs: list[SpotifySong] = field(default_factory=list)

class CreatePlayer(BaseModel):
    
    name: str
    songs: list[SpotifySong] = field(default_factory=list)


class UpdatePlayer(BaseModel):
    
    name: str | None = None
    songs: list[SpotifySong] = None