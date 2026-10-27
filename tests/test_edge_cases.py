import unittest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from base_api import DownloadConfigHLS, DownloadConfigRAW
from base_api.modules.config import RuntimeConfig
from base_api.modules.errors import VideoUnavailable, DownloadFailed
from spankbang_api.modules.errors import VideoIsProcessing

from spankbang_api.api import Client, Video, Channel, Creator, Pornstar, create_parser, run_main, _quality_sort_key
from spankbang_api.modules.consts import extractor


class EdgeCasesTests(unittest.IsolatedAsyncioTestCase):

    def test_quality_sort_key(self):
        self.assertEqual(_quality_sort_key("240p"), 240)
        self.assertEqual(_quality_sort_key("480"), 480)
        self.assertEqual(_quality_sort_key("720p"), 720)
        self.assertEqual(_quality_sort_key("1080p"), 1080)
        self.assertEqual(_quality_sort_key("4k"), 2160)
        self.assertEqual(_quality_sort_key("4K"), 2160)
        self.assertEqual(_quality_sort_key("unknown"), 0)

    def test_video_url_normalization_bare_id(self):
        v1 = Video(url="https://spankbang.com/9qfxd", core=MagicMock())
        self.assertEqual(v1.url, "https://spankbang.com/9qfxd/video/")

        v2 = Video(url="https://spankbang.com/9qfxd/", core=MagicMock())
        self.assertEqual(v2.url, "https://spankbang.com/9qfxd/video/")

    def test_video_url_normalization_embed_and_play(self):
        v_embed = Video(url="https://spankbang.com/9qfxd/embed/", core=MagicMock())
        self.assertEqual(v_embed.url, "https://spankbang.com/9qfxd/video/")

        v_embed_noslash = Video(url="https://spankbang.com/9qfxd/embed", core=MagicMock())
        self.assertEqual(v_embed_noslash.url, "https://spankbang.com/9qfxd/video/")

        v_play = Video(url="https://spankbang.com/9qfxd/play/", core=MagicMock())
        self.assertEqual(v_play.url, "https://spankbang.com/9qfxd/video/")

        v_play_noslash = Video(url="https://spankbang.com/9qfxd/play", core=MagicMock())
        self.assertEqual(v_play_noslash.url, "https://spankbang.com/9qfxd/video/")

    def test_pornstar_helper_depth_detection(self):
        ch1 = Channel(url="https://spankbang.com/channel/brazzers/", core=MagicMock())
        self.assertEqual(ch1.url, "https://spankbang.com/channel/brazzers")

        ch2 = Channel(url="https://de.spankbang.com/ho/channel/brazzers/", core=MagicMock())
        self.assertEqual(ch2.url, "https://de.spankbang.com/ho/channel/brazzers")

        cr1 = Creator(url="https://spankbang.com/creator/yvonna/", core=MagicMock())
        self.assertEqual(cr1.url, "https://spankbang.com/creator/yvonna")

        cr2 = Creator(url="https://spankbang.com/kxrn/creator/yvonna/", core=MagicMock())
        self.assertEqual(cr2.url, "https://spankbang.com/kxrn/creator/yvonna")

        ps1 = Pornstar(url="https://spankbang.com/pornstar/angela+white/", core=MagicMock())
        self.assertEqual(ps1.url, "https://spankbang.com/pornstar/angela+white")

        ps2 = Pornstar(url="https://spankbang.com/32/pornstar/angela+white/", core=MagicMock())
        self.assertEqual(ps2.url, "https://spankbang.com/32/pornstar/angela+white")

        ps3 = Pornstar(url="https://de.spankbang.com/en/32/pornstar/angela+white/", core=MagicMock())
        self.assertEqual(ps3.url, "https://de.spankbang.com/en/32/pornstar/angela+white")

    def test_multilingual_profile_stats_german(self):
        html_de = """
        <div data-testid="profile-name"><h1>Brazzers</h1></div>
        <div data-testid="profile-stats">
            <div><span>Videos: <em class="not-italic text-primary">4.7K</em></span></div>
            <div><span>Aufrufe: <em class="not-italic text-primary">49M</em></span></div>
            <div><span>Abonnenten: <em class="not-italic text-primary">49K</em></span></div>
        </div>
        """
        data = Channel._extract_data(html_de)
        self.assertEqual(data["name"], "Brazzers")
        self.assertEqual(data["video_count"], "4.7K")
        self.assertEqual(data["views_count"], "49M")
        self.assertEqual(data["subscribers_count"], "49K")

    def test_multilingual_profile_stats_french_and_spanish(self):
        html_fr = """
        <div data-testid="profile-name"><h1>Angela White Porn Videos</h1></div>
        <div data-testid="profile-stats">
            <div><span>Vues: <em>10M</em></span></div>
            <div><span>Vidéos: <em>500</em></span></div>
            <div><span>Abonnés: <em>20K</em></span></div>
        </div>
        """
        data = Pornstar._extract_data(html_fr)
        self.assertEqual(data["name"], "Angela White")
        self.assertEqual(data["video_count"], "500")
        self.assertEqual(data["views_count"], "10M")
        self.assertEqual(data["subscribers_count"], "20K")

    def test_pornstar_name_cleaning(self):
        html = """<h1 data-testid="profile-name">Angela White Porn Videos</h1>"""
        data = Pornstar._extract_data(html)
        self.assertEqual(data["name"], "Angela White")

    def test_scheme_relative_image_and_thumbnail(self):
        html = """
        <h1 data-testid="profile-name">Test</h1>
        <img data-testid="profile-detail-image" src="//spankbang.com/avatar/test.jpg">
        """
        data = Creator._extract_data(html)
        self.assertEqual(data["image"], "https://spankbang.com/avatar/test.jpg")

    def test_video_extract_double_quotes_and_4k(self):
        html = """
        <h1 data-testid="video-title">Epic 4K Scene</h1>
        <script>
            var stream_data = {
                "m3u8": ["https://cdn.sb-cd.com/master.m3u8"],
                "1080p": ["https://cdn.sb-cd.com/1080p.mp4"],
                "4k": ["https://cdn.sb-cd.com/4k.mp4"],
                "720p": ["https://cdn.sb-cd.com/720p.mp4"]
            };
        </script>
        <meta property="og:video:duration" content="720">
        <div data-testid="video-description">Full 4k experience</div>
        """
        data = Video._extract_data(html)
        self.assertEqual(data["title"], "Epic 4K Scene")
        self.assertEqual(data["length"], "720")
        self.assertEqual(data["m3u8_base_url"], "https://cdn.sb-cd.com/master.m3u8")
        self.assertEqual(data["video_qualities"], ["720", "1080", "4k"])
        self.assertEqual(data["direct_download_urls"], [
            "https://cdn.sb-cd.com/720p.mp4",
            "https://cdn.sb-cd.com/1080p.mp4",
            "https://cdn.sb-cd.com/4k.mp4"
        ])

    def test_video_processing_detection(self):
        html = '<html><body><div class="warning_process">Processing</div></body></html>'
        v = Video(url="https://spankbang.com/123/video/test", core=MagicMock())
        with patch("spankbang_api.api.get_html_content", AsyncMock(return_value=html)):
            with self.assertRaises(VideoIsProcessing):
                asyncio.run(v._load_html())

    def test_extractor_multi_containers(self):
        html = """
        <div x-data="videoList">
            <div data-testid="video-item"><a href="/1/video/v1" title="V1"></a></div>
            <div data-testid="video-item"><a href="/2/video/v2" title="V2"></a></div>
        </div>
        <div x-data="videoList">
            <div data-testid="video-item"><a href="/3/video/v3" title="V3"></a></div>
            <div data-testid="video-item"><a href="/4/video/v4" title="V4"></a></div>
            <div data-testid="video-item"><a href="/5/video/v5" title="V5"></a></div>
            <div data-testid="video-item"><a href="/6/video/v6" title="V6"></a></div>
        </div>
        <div x-data="videoList">
            <div data-testid="video-item"><a href="/7/video/v7" title="V7"></a></div>
        </div>
        """
        videos = extractor(html, base_url="https://spankbang.com")
        self.assertEqual(len(videos), 4)
        self.assertEqual(videos[0]["url"], "https://spankbang.com/3/video/v3")

    async def test_search_pagination_and_query_encoding(self):
        client = Client()
        stream = client.search(
            query="asian & amateur / bbw",
            filter="new",
            quality="hd",
            duration="20",
            date="m",
            pages=3
        )
        self.assertIsNotNone(stream)

    async def test_raw_download_quality_fallbacks(self):
        mock_core = MagicMock()
        mock_core.legacy_download = AsyncMock(return_value=True)

        video = Video(url="https://spankbang.com/123/video/test", core=mock_core)
        video.title = "Test Video"
        video.video_qualities = ["240", "480", "720", "1080", "4k"]
        video.direct_download_urls = [
            "https://cdn/240.mp4",
            "https://cdn/480.mp4",
            "https://cdn/720.mp4",
            "https://cdn/1080.mp4",
            "https://cdn/2160.mp4"
        ]

        with patch.object(Video, "load_fields", AsyncMock()):
            # 1. Best
            cfg_best = DownloadConfigRAW(quality="best")
            await video.download(configuration_raw=cfg_best)
            self.assertEqual(mock_core.legacy_download.call_args.kwargs["url"], "https://cdn/2160.mp4")

            # 2. Worst
            cfg_worst = DownloadConfigRAW(quality="worst")
            await video.download(configuration_raw=cfg_worst)
            self.assertEqual(mock_core.legacy_download.call_args.kwargs["url"], "https://cdn/240.mp4")

            # 3. Label "hd"
            cfg_hd = DownloadConfigRAW(quality="hd")
            await video.download(configuration_raw=cfg_hd)
            self.assertEqual(mock_core.legacy_download.call_args.kwargs["url"], "https://cdn/720.mp4")

            # 4. Label "4k"
            cfg_4k = DownloadConfigRAW(quality="4k")
            await video.download(configuration_raw=cfg_4k)
            self.assertEqual(mock_core.legacy_download.call_args.kwargs["url"], "https://cdn/2160.mp4")

            # 5. Numeric string "1080p"
            cfg_1080p = DownloadConfigRAW(quality="1080p")
            await video.download(configuration_raw=cfg_1080p)
            self.assertEqual(mock_core.legacy_download.call_args.kwargs["url"], "https://cdn/1080.mp4")

            # 6. Fallback for non-existent quality "360p" -> nearest is 480
            cfg_360 = DownloadConfigRAW(quality="360p")
            await video.download(configuration_raw=cfg_360)
            self.assertEqual(mock_core.legacy_download.call_args.kwargs["url"], "https://cdn/480.mp4")

    async def test_download_error_conditions(self):
        mock_core = MagicMock()
        video = Video(url="https://spankbang.com/123/video/test", core=mock_core)
        video.title = "Test"
        video.m3u8_base_url = None
        video.direct_download_urls = []
        video.video_qualities = []

        with patch.object(Video, "load_fields", AsyncMock()):
            # Missing both configs wraps in DownloadFailed with ValueError
            with self.assertRaises(DownloadFailed) as ctx:
                await video.download()
            self.assertIsInstance(ctx.exception.__cause__, ValueError)

            # Missing HLS stream raises VideoUnavailable
            with self.assertRaises(VideoUnavailable):
                await video.download(configuration_hls=DownloadConfigHLS(quality="best"))

            # Missing raw stream raises VideoUnavailable
            with self.assertRaises(VideoUnavailable):
                await video.download(configuration_raw=DownloadConfigRAW(quality="best"))

    def test_cli_parser_raw_flag(self):
        parser = create_parser()
        args = parser.parse_args(["--download", "https://spankbang.com/123/video/test", "--output", "/tmp", "--raw"])
        self.assertTrue(args.raw)


if __name__ == "__main__":
    unittest.main()
