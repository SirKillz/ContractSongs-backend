from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SpotifyApiKeys(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    access_token: str
    token_type: str
    scope: str
    access_token_expires_at: datetime
    refresh_token: str