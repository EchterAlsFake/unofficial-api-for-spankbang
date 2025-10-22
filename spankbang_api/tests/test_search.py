from ..spankbang_api import Client

client = Client()
search = client.search(query="fortnite", videos_concurrency=1, pages_concurrency=1)

def test_search():
    for idx, video in enumerate(search):
        assert isinstance(video.title, str)
        if idx == 3:
            return

