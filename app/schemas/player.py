from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

class ReadPlayer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    name: str

class CreatePlayer(BaseModel):
    
    name: str