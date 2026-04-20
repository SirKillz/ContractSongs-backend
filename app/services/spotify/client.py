import os

from dotenv import load_dotenv
load_dotenv(".env")

from session import ApiSession

class SpotifyClient:
    def __init__(self, session: ApiSession) -> None:
        self.session = session

    async def get_currently_playing_track(self):
        """
        Get the current playback data
        """

        return await self.session.get(path="/me/player/currently-playing")
    
    async def pause_playback(self):
        """
        Pauses Playback
        """
        return await self.session.put(path="/me/player/pause")
    
    async def resume_playback(self):
        return await self.session.put(path="/me/player/play")