from datetime import datetime
from dataclasses import dataclass, field

from typing import List

@dataclass
class SpotifyTokenSnapshot:
    """
    A snapshot of the database returned tokens
    Used a pythonic data to avoid passing around closed ORM objects
    """
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str

@dataclass
class SpotifySong:
    """
    A small subset of relevant data for capturing Spotify Songs
    """
    id: str
    name: str
    artist: str

@dataclass
class SpotifyPlaylist:
    """
    A small subset of relevant data for capturing Spotify Playlists
    """

    id: str
    name: str
    songs: List[SpotifySong] = field(default_factory=list)