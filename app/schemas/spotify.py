from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field
from app.services.spotify.types import SpotifyPlaylist

class GetPlaylists(BaseModel):

    count: int
    playlists: List[SpotifyPlaylist]