from datetime import datetime
from dataclasses import dataclass

@dataclass
class SpotifyTokenSnapshot:
    """
    A snapshot of the database returned tokens
    Used a pythonic data to avoid passing around closed ORM objects
    """
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str