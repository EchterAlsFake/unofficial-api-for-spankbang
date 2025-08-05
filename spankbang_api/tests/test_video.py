import httpx

from spankbang_api.spankbang_api import Client

url = "https://spankbang.com/9qfxd/video/asian+girl+rides+fuck+machine+to+massive+squirt+no+hands+needed"
video = Client().get_video(url)

def find_error_idk():
    try:
        content = httpx.get(url, headers={"Referer": "https://spankbang.com/",
                                          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"})

        print(f"Status code: {content.status_code}")
        content.raise_for_status()
        assert content.status_code == 200


    except Exception as e:
        print(e)


def test_title():
    assert isinstance(video.title, str) and len(video.title) > 3


def test_author():
    assert isinstance(video.title, str) and len(video.author) > 5


def test_description():
    assert isinstance(video.description, str) and len(video.description) > 20


def test_video_length():
    assert isinstance(video.length, str) and len(video.length) > 0


def test_tags():
    assert isinstance(video.tags, list) and len(video.tags) > 2


def test_qualities():
    assert isinstance(video.video_qualities, list) and len(video.video_qualities) > 2


def test_direct_download_urls():
    assert isinstance(video.direct_download_urls, list) and len(video.direct_download_urls) > 2


def test_thumbnail():
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 3


def test_rating():
    assert isinstance(video.rating, str) and len(video.rating) > 1


def test_segments():
    assert isinstance(video.get_segments("best"), list) and len(video.get_segments("best")) > 25


def test_download_remux():
    assert video.download(quality="worst", downloader="threaded", remux=True) is True

def test_download_raw():
    assert video.download(quality="worst", downloader="threaded") is True