import pytest
from ..spankbang_api import Client




@pytest.mark.asyncio
async def test_attributes():
    client = Client()
    channel = await client.get_channel("https://de.spankbang.com/ho/channel/brazzers/")
    assert isinstance(channel.name, str)
    assert isinstance(channel.views_count, str)
    assert isinstance(channel.image, str)
    assert isinstance(channel.video_count, str)

    idx = 0
    async for video in channel.videos(videos_concurrency=1, pages_concurrency=1):
        idx += 1

        assert isinstance(video.title, str)
        if idx == 3:
            break