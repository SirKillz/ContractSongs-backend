from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.player import CreatePlayer, ReadPlayer

class ReadSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playlist_id: str
    playlist_name: str
    created_at: datetime
    players: list[ReadPlayer]

class CreateSession(BaseModel):
    
    playlist_id: str
    playlist_name: str
    players: list[CreatePlayer] = Field(default_factory=list)
    # created_at will be handled within the route

class DeleteSession(BaseModel):
    deleted: bool

class UpdateSession(BaseModel):
    players: list[CreatePlayer] | list[ReadPlayer]