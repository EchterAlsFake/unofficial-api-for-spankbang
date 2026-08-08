from ..api import Client
from base_api.modules.config import IteratorConfig
import pytest


@pytest.mark.asyncio
async def test_search():
    client = Client()
    iterator_config = IteratorConfig(
        max_item_concurrency=1,
        max_page_concurrency=1,
        load_specific_sources=("html",),
    )
    search = client.search(query="fortnite", iterator_config=iterator_config)
    idx = 0
    async for video in search:
        idx += 1
        assert isinstance(video.unwrap().title, str)

        if idx == 3:
            break
