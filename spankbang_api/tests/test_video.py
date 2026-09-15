import tempfile
import pytest
from base_api import DownloadConfigHLS
from spankbang_api.api import Client, Video

HTML_FIXTURE = """<div id="video" data-videoid="14228352" data-streamkey="MTQyMjgzNTI.H6GcPkvKoHrrxDCyEcjyR_wC3pU" x-data="toggleMoreVideos">
    <div class="left">
        <div class="mb-1 flex items-start gap-2 lg:mb-4">
            <h1 class="text-primary text-body-lg  font-bold line-clamp-2" data-testid="video-title">Brazzers - Tattooed redhead , Tana Lea deepthroats cock</h1>
        </div>
        <div class="relative z-0" x-data="horizontalScroller('', '', undefined)" data-testid="video-tags">
            <div class="flex gap-x-2 mb-2 lg:mb-4 scrollbar-none overflow-x-auto overflow-y-hidden cursor-grab">
                <a href="/ho/channel/brazzers/"><img src="//spankbang.com/avatar/90/channel_1818.jpg" alt="BRAZZERS">BRAZZERS</a>
                <a href="/hrx/pornstar/tana+lea/"><span></span>Tana Lea</a>
                <a href="/s/butt/">Butt</a>
                <a href="/s/young/">Young</a>
                <a href="/s/inked/">inked</a>
                <a href="/s/tattoo/">Tattoo</a>
                <a href="/s/big+ass/">Big Ass</a>
                <a href="/s/blowjob/">Blowjob</a>
                <a href="/s/cowgirl/">Cowgirl</a>
                <a href="/s/hd+porn/">HD Porn</a>
                <a href="/s/redhead/">Redhead</a>
                <a href="/s/cheater/">cheater</a>
                <a href="/s/teen+18/">teen 18</a>
                <a href="/s/big+tits/">Big Tits</a>
                <a href="/s/hardcore/">Hardcore</a>
                <a href="/s/pornstar/">Pornstar</a>
                <a href="/s/spooning/">Spooning</a>
                <a href="/s/teenager/">Teenager</a>
                <a href="/s/red+head/">red head</a>
                <a href="/s/big+boobs/">Big Boobs</a>
                <a href="/s/missonary/">missonary</a>
                <a href="/s/professional/">Professional</a>
                <a href="/s/wife+fantasy/">Wife fantasy</a>
                <a href="/s/brazzers+free/">Brazzers free</a>
                <a href="/s/tattooed+women/">Tattooed Women</a>
                <a href="/s/brazzers+gratis/">brazzers gratis</a>
                <a href="/s/brazzers+network/">brazzers network</a>
                <a href="/s/teen/">Teen (18+)</a>
            </div>
        </div>
        <script type="text/javascript">
            var ana_video_id = '14228352';
            var stream_data = {'240p': ['https://vdownload-43.sb-cd.com/1/4/14228352-240p.mp4?secure=xlMmANCGgxNsAkuXUXPFOg,1789447413&m=43&d=1&_tid=14228352'], '320p': [], '480p': ['https://vdownload-43.sb-cd.com/1/4/14228352-480p.mp4?secure=xlMmANCGgxNsAkuXUXPFOg,1789447413&m=43&d=1&_tid=14228352'], '720p': ['https://vdownload-43.sb-cd.com/1/4/14228352-720p.mp4?secure=xlMmANCGgxNsAkuXUXPFOg,1789447413&m=43&d=1&_tid=14228352'], '1080p': [], '4k': [], 'mpd': [], 'm3u8': ['https://hls-uranus.sb-cd.com/hls/1/4/14228352-,240p,480p,720p,.mp4.urlset/master.m3u8?secure=xlMmANCGgxNsAkuXUXPFOg,1789447413&m=43&d=1&_tid=14228352'], 'cover_image': 'https://tbi.sb-cd.com/t/14228352/cb/37/w:1280/t6-enh/brazzers-tattooed-redhead.jpg', 'thumbnail': 'https://tbi.sb-cd.com/t/14228352/cb/37/w:300/t6-enh/brazzers-tattooed-redhead.jpg', 'stream_raw_id': 14228352, 'stream_sheet': 'https://tbv.sb-cd.com/t/14228352/cb/37/t9999.jpg', 'length': 481, 'main': ['https://vdownload-43.sb-cd.com/1/4/14228352-720p.mp4?secure=xlMmANCGgxNsAkuXUXPFOg,1789447413&m=43&d=1&_tid=14228352']};
            var live_keywords = 'Tana Lea,Butt,Young,inked,Tattoo,Big Ass,Blowjob,Cowgirl,HD Porn,Redhead,cheater,teen 18,';
        </script>
        <div id="player_wrapper_outer" class="relative" data-testid="video-player-wrapper">
            <div class="play_cover" data-testid="video-play-cover">
                <img id="player_cover_img" alt="Brazzers - Tattooed redhead , Tana Lea deepthroats cock" src="https://tbi.sb-cd.com/t/14228352/cb/37/w:800/t6-enh/brazzers-tattooed-redhead.jpg">
            </div>
            <div id="video_container">
                <video id="main_video_player_html5_api" src="https://vdownload-43.sb-cd.com/1/4/14228352-720p.mp4">
                    <source src="https://vdownload-43.sb-cd.com/1/4/14228352-720p.mp4" type="video/mp4">
                </video>
            </div>
        </div>
        <div id="vote-container">
            <span data-testid="upvote-percentage">100%</span>
        </div>
        <div data-testid="video-description">
            <p>Brazzers - Tattooed redhead , Tana Lea deepthroats cock</p>
        </div>
        <div data-testid="owner-details">
            <div data-testid="profile">
                <a href="/ho/channel/brazzers/">
                    <img class="lazyload w-10 h-10 rounded object-cover" src="//spankbang.com/avatar/90/channel_1818.jpg" alt="BRAZZERS">
                </a>
                <div>
                    <a href="/ho/channel/brazzers/" class="text-link-primary">
                        <p class="text-link-secondary text-body-lg flex items-center">BRAZZERS</p>
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>"""


def test_extract_video_data():
    data = Video._extract_data(HTML_FIXTURE)
    assert data["title"] == "Brazzers - Tattooed redhead , Tana Lea deepthroats cock"
    assert data["description"] == "Brazzers - Tattooed redhead , Tana Lea deepthroats cock"
    assert data["thumbnail"] == "https://tbi.sb-cd.com/t/14228352/cb/37/w:800/t6-enh/brazzers-tattooed-redhead.jpg"
    assert isinstance(data["tags"], list)
    assert len(data["tags"]) == 28
    assert "Tana Lea" in data["tags"]
    assert "Butt" in data["tags"]
    assert data["author"] == "BRAZZERS"
    assert data["image"] == "BRAZZERS"
    assert data["rating"] == "100%"
    assert data["length"] == "481"
    assert data["m3u8_base_url"] is not None and "master.m3u8" in data["m3u8_base_url"]
    assert isinstance(data["direct_download_urls"], list) and len(data["direct_download_urls"]) == 3
    assert data["video_qualities"] == ["240", "480", "720"]


@pytest.mark.asyncio
async def test_live_metadata():
    client = Client()
    url = "https://spankbang.com/9qfxd/video/asian+girl+rides+fuck+machine+to+massive+squirt+no+hands+needed"
    video = await client.get_video(url)
    assert isinstance(video.title, str) and len(video.title) > 3
    assert isinstance(video.author, str) and len(video.author) > 1
    assert isinstance(video.description, str) and len(video.description) > 5
    assert isinstance(video.length, str) and len(video.length) > 0
    assert isinstance(video.tags, list) and len(video.tags) > 2
    assert isinstance(video.video_qualities, list) and len(video.video_qualities) >= 1
    assert isinstance(video.direct_download_urls, list) and len(video.direct_download_urls) >= 1
    assert isinstance(video.thumbnail, str) and len(video.thumbnail) > 3
    assert isinstance(video.rating, str) and len(video.rating) >= 1


@pytest.mark.asyncio
async def test_download():
    client = Client()
    url = "https://spankbang.com/9qfxd/video/asian+girl+rides+fuck+machine+to+massive+squirt+no+hands+needed"
    video = await client.get_video(url)
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_1 = DownloadConfigHLS(quality="worst", remux=True, return_report=True, path=tmp_dir)
        config_2 = DownloadConfigHLS(quality="worst", remux=False, return_report=True, path=tmp_dir)

        stuff = await video.download(config_1)
        assert stuff.status == "completed"
        stuff = await video.download(config_2)
        assert stuff.status == "completed"

