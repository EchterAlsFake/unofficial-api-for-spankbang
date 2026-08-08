import pytest
from ..api import Client
from base_api.modules.config import IteratorConfig




@pytest.mark.asyncio
async def test_attributes():
    client = Client()
    channel = await client.get_channel("https://de.spankbang.com/ho/channel/brazzers/")
    assert isinstance(channel.name, str)
    assert isinstance(channel.views_count, str)
    assert isinstance(channel.image, str)
    assert isinstance(channel.video_count, str)

    idx = 0
    iterator_config = IteratorConfig(
        max_item_concurrency=1,
        max_page_concurrency=1,
        load_specific_sources=("html",),
    )
    async for video in channel.videos(iterator_config=iterator_config):
        idx += 1

        assert isinstance(video.unwrap().title, str)
        if idx == 3:
            break
