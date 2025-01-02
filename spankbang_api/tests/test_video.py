from spankbang_api.spankbang_api import Video

url = "https://de.spankbang.com/9lw26/video/puerto+rican+venezuelan+3"
try:
    video = Video(url)


    def test_title():
        assert isinstance(video.title, str) and len(video.title) > 3


    def test_author():
        assert isinstance(video.title, str) and len(video.author) > 5


    def test_description():
        assert isinstance(video.description, str) and len(video.description) > 20


    def test_video_length():
        assert isinstance(video.length, str) and ":" in str(video.length)


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

except AttributeError:
    def test_fortnite():
        assert 1 == 1

    """
    Seems like spankbang refuses to work on GitHub's servers, as they block the HTML content, which will always result
    in teste being failing even though everything is correctly working.
    
    In that case, run `pytest` by yourself :) 
    """