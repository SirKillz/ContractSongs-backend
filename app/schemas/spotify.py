from datetime import datetime
from dataclasses import field

from pydantic import BaseModel, ConfigDict, Field

from app.services.spotify.types import SpotifyPlaylist, SpotifySong

class GetPlaylists(BaseModel):

    count: int
    playlists: list[SpotifyPlaylist] = field(default_factory=list)

class GetPlayListSongs(BaseModel):

    id: str
    song_count: int
    songs: list[SpotifySong] = field(default_factory=list)