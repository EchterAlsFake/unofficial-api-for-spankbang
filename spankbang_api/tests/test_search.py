from ..api import Client
import pytest


@pytest.mark.asyncio
async def test_search():
    client = Client()
    search = client.search(query="fortnite", videos_concurrency=1, pages_concurrency=1)
    idx = 0
    async for video in search:
        idx += 1
        assert isinstance(video.video.title, str)

        if idx == 3:
            break

