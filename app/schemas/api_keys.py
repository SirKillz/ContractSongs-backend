from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class GetSpotifyApiTokens(BaseModel):

    access_token: str
    token_type: str
    scope: str
    access_token_expires_at: datetime
    refresh_token: str

class ReadSpotifyApiKeys(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    access_token: str
    token_type: str
    scope: str
    access_token_expires_at: datetime
    refresh_token: str

class CreateSpotifyApiKeys(BaseModel):
    access_token: str
    token_type: str
    scope: str
    access_token_expires_at: str = Field(
        examples=["2026-04-19T18:25:43Z"]
    )
    refresh_token: str