from base_api.modules.errors import BotProtectionDetected
from spankbang_api.spankbang_api import Client
import pytest

@pytest.mark.asyncio
async def test_all():
    client = Client()
    url = "https://spankbang.com/9qfxd/video/asian+girl+rides+fuck+machine+to+massive+squirt+no+hands+needed"
    video = await client.get_video(url)
    assert isinstance(video.title, str) and len(video.title) > 3
    assert isinstance(video.title, str) and len(video.author) > 5
    assert isinstance(video.description, str) and len(video.description) > 20
    assert isinstance(video.length, str) and len(video.length) > 0
    assert isinstance(video.tags, list) and len(video.tags) > 2
    assert isinstance(video.video_qualities, list) and len(video.video_qualities) > 2
    assert isinstance(video.direct_download_urls, list) and len(video.direct_download_urls) > 2
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 3
    assert isinstance(video.rating, str) and len(video.rating) > 1
    assert isinstance(await video.get_segments("best"), list) and len(await video.get_segments("best")) > 25
    stuff = await video.download(quality="worst", remux=True, return_report=True)
    assert stuff["status"] == "completed"
    stuff = await video.download(quality="worst", remux=False, return_report=True)
    assert stuff["status"] == "completed"
