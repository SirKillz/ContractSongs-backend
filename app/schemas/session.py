from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class ReadSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playlist_id: str
    playlist_name: str
    created_at: datetime

class CreateSession(BaseModel):
    
    playlist_id: str
    playlist_name: str
    # created_at will be handled within the route