from ..spankbang_api import Client


client = Client()
channel = client.get_channel("https://de.spankbang.com/7u/channel/21+naturals/2/")


def test_attributes():
    assert isinstance(channel.name, str)
    assert isinstance(channel.views_count, str)
    assert isinstance(channel.image, str)
    assert isinstance(channel.video_count, str)

def test_videos():
    for idx, video in enumerate(channel.videos(videos_concurrency=1, pages_concurrency=1)):
        assert isinstance(video.title, str)
        if idx == 3:
            return