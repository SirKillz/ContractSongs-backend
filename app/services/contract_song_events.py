import asyncio

# Global Queue (First In, First Out)
# Add to the Queue using .put() or publish_to_queue helper
# Retrieve items from the Queue using .get() which removes them
contract_song_queue = asyncio.Queue()

async def publish_to_queue(event: dict) -> None:
    await contract_song_queue.put(event)