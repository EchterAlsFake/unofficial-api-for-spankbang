import os.path
import logging
import threading

from typing import Literal
from functools import cached_property
from base_api.modules.errors import ResourceGone, NetworkingError, InvalidProxy, BotProtectionDetected, UnknownError
from base_api.modules.config import RuntimeConfig
from base_api.base import BaseCore, setup_logger, Helper
from urllib.parse import urlunsplit, urlencode, quote, urlsplit

from base_api.modules.type_hints import DownloadReport
from curl_cffi import AsyncSession
from curl_cffi.requests import Response
from curl_cffi.requests.cookies import Cookies
from curl_cffi.requests.exceptions import CookieConflict

# Monkeypatch curl_cffi to handle multiple cookies with the same name across domains
# This is needed because eaf_base_api calls dict(session.cookies) which triggers CookieConflict
# when both .spankbang.com and hls-uranus.sb-cd.com have __cf_bm cookies.
original_getitem = Cookies.__getitem__


def patched_getitem(self, name):
    try:
        return original_getitem(self, name)
    except CookieConflict:
        # Fallback to get_dict which is more lenient and just picks one
        return self.get_dict().get(name)


Cookies.__getitem__ = patched_getitem

try:
    from modules.consts import *
    from modules.errors import *
    from modules.type_hints import *

except (ImportError, ModuleNotFoundError):
    from .modules.consts import *
    from .modules.errors import *
    from .modules.type_hints import *


try:
    import lxml
    parser = "lxml"

except (ImportError, ModuleNotFoundError):
    parser = "html.parser"


async def get_html_content(core: BaseCore, url: str) -> str | None | dict:
    # What should I do here?
    try:
        content = await core.fetch(url)
        if isinstance(content, str):
            return content

        if isinstance(content, Response):
            if content.status_code == 404:
                raise NotFound(f"Server returned 404 for: {url}")

    except NetworkingError as e:
        raise NetworkError(str(e)) from e

    except InvalidProxy as e:
        raise ProxyError(str(e)) from e

    except BotProtectionDetected as e:
        raise BotDetection(str(e)) from e

    except UnknownError as e:
        raise UnknownNetworkError(str(e)) from e


class PornstarHelper(Helper):
    """
    Shares the same attributes like Pornstar, Channel and Creator
    """
    def __init__(self, url: str, core: BaseCore, helper_log_level=logging.DEBUG, html_content: str | None = None):
        super(PornstarHelper, self).__init__(core, video_constructor=Video, log_level=helper_log_level)
        self.url = url
        self.core = core
        self.html_content = html_content
        self._soup: BeautifulSoup | None = None

    async def init(self):
        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=self.url)

        assert isinstance(self.html_content, str)
        self._soup = BeautifulSoup(self.html_content, parser)
        return self

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call init")

        return self._soup

    @cached_property
    def name(self) -> str:
        return self.soup.find("h1", class_="p-0 text-title-sm font-bold capitalize text-primary md:text-title-md xl:text-title-md").text.strip()

    @cached_property
    def video_count(self) -> str:
        return self.soup.find("em", class_="not-italic text-primary").text.strip()

    @cached_property
    def views_count(self) -> str:
        return self.soup.find_all("em", class_="not-italic text-primary")[1].text.strip()

    @cached_property
    def subscribers_count(self) -> str:
        return self.soup.find_all("em", class_="not-italic text-primary")[2].text.strip()

    @cached_property
    def image(self) -> str:
        return self.soup.find("img", class_="w-full rounded").get("src")

    async def videos(self, pages: int = 0, videos_concurrency: int | None = None, pages_concurrency: int | None = None):
        page_urls = [self.url]
        for page in range(2, pages + 2):
            page_urls.append(f"{self.url}/{page}/")
        
        videos_concurrency = videos_concurrency or self.core.configuration.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency
        assert videos_concurrency and pages_concurrency

        async for video in self.iterator(target_page_urls=page_urls, max_page_concurrency=pages_concurrency,
                                 max_video_concurrency=videos_concurrency, video_link_extractor=extractor):
            yield video


class Channel(PornstarHelper):
    pass


class Creator(PornstarHelper):
    pass


class Pornstar(PornstarHelper):
    pass


class Video:
    def __init__(self, url, core: BaseCore, html_content: str | None = None):
        self.core = core
        self.url = url  # Needed for Porn Fetch
        self.html_content = html_content
        self._soup: BeautifulSoup | None = None
        self.logger = setup_logger(name="SPANKBANG API - [Video]", log_file=None, level=logging.ERROR)

    async def init(self):
        if not self.html_content:
            self.html_content = await get_html_content(core=self.core, url=self.url)

        assert isinstance(self.html_content, str)
        if '<div class="warning_process">' in self.html_content:
            raise VideoIsProcessing

        self._soup = BeautifulSoup(self.html_content, parser)
        self.extract_script_2()
        return self

    @property
    def soup(self) -> BeautifulSoup:
        if not self._soup:
            raise ValueError("You probably forgot to call init")

        return self._soup

    async def get_html_content(self):
        x =  await self.core.fetch(self.url)
        return x

    def enable_logging(self, log_file: str | None = None, level: int | None = None, log_ip: str | None = None, log_port: int | None = None):
        if not level:
            level = logging.DEBUG

        self.logger = setup_logger(name="SPANKBANG API - [Video]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    def extract_script_2(self):
        """This extracts the script with the m3u8 URLs which contain the segments used for downloading"""
        self.logger.debug("Trying to extract the second script...")
        main_container = self.soup.find('main', class_='main-container')
        script_tag = main_container.find('script', {'type': 'text/javascript'})
        self.stream_data_js = re.search(r'var stream_data = ({.*?});', script_tag.text.replace("\t", " "), re.DOTALL).group(1)
        m3u8_pattern = re.compile(r"'m3u8': \['(https://[^']+master.m3u8[^']*)']")
        resolution_pattern = re.compile(r"'(240p|320p|480p|720p|1080p|4k)': \['(https://[^']+.mp4[^']*)']")

        # Extract m3u8 master URL
        m3u8_match = m3u8_pattern.search(self.stream_data_js)
        m3u8_url = m3u8_match.group(1) if m3u8_match else None

        # Extract resolution URLs
        resolution_matches = resolution_pattern.findall(self.stream_data_js)
        resolution_urls = [url for res, url in resolution_matches]
        self.logger.info("Found m3u8 and resolution information!")
        # Combine the URLs with m3u8 first
        self.urls_list = [m3u8_url] + resolution_urls if m3u8_url else resolution_urls
        # (Damn I love ChatGPT xD)

    @cached_property
    def title(self) -> str:
        """Returns the title of the video"""
        # Try new redesign selector
        h1 = self.soup.find("h1", {"data-testid": "video-title"})
        if h1:
            return h1.text.strip()
        
        # Try old redesign selector (Tailwind classes)
        h1 = self.soup.find("h1", class_="text-primary text-body-lg font-bold mb-1 lg:mb-4 line-clamp-2")
        if h1:
            return h1.text.strip()

        # Try user's reported selector
        h1 = self.soup.find("h1", class_="headline__title")
        if h1:
            return h1.text.strip()
        
        # Fallback to any h1
        h1 = self.soup.find("h1")
        if h1:
            return h1.text.strip()
            
        # Fallback to meta tags
        meta_title = self.soup.find("meta", property="og:title") or self.soup.find("meta", attrs={"name": "twitter:title"})
        if meta_title:
            return meta_title.get("content", "").replace(": Porn - SpankBang", "").strip()

        return "Unknown Title"

    @cached_property
    def description(self) -> str:
        """Returns the description of the video"""
        return self.soup.find("meta", attrs={"name": "description"}).get("content")

    @cached_property
    def thumbnail(self) -> str:
        """Returns the thumbnail of the video"""
        return self.soup.find("img", class_="absolute inset-0 block h-full w-full object-cover").get("src")

    @cached_property
    def tags(self) -> list:
        """Returns the keywords of the video"""
        return self.soup.find("meta", attrs={"name": "keywords"}).get("content").split(",")

    @cached_property
    def author(self) -> str:
        """Returns the author of the video"""
        # Try new redesign selector
        author_tag = self.soup.find("p", class_="text-link-secondary text-body-lg flex items-center") or \
                     self.soup.find("p", class_="text-link-secondary text-body-lg flex items-center".replace(" ", "  "))
        if author_tag:
            return author_tag.text.strip()
        
        # Try image alt
        img_tag = self.soup.find("img", class_="lazyload w-10 h-10 rounded object-cover")
        if img_tag and img_tag.get("alt"):
            return img_tag.get("alt").strip()

        # Fallback to regex
        try:
            return REGEX_VIDEO_AUTHOR.search(self.html_content).group(1)
        except (AttributeError, IndexError):
            pass
        
        return "Unknown Author"

    @cached_property
    def rating(self) -> str:
        """Returns the rating of the video"""
        # Try new redesign selector
        rating_tag = self.soup.find("span", {"data-testid": "upvote-percentage"})
        if rating_tag:
            return rating_tag.text.strip()

        # Fallback to regex
        try:
            return REGEX_VIDEO_RATING.search(self.html_content).group(1)
        except (AttributeError, IndexError):
            pass

        return "Unknown Rating"

    @cached_property
    def length(self) -> str:
        """Returns the length in possibly 00:00 format"""
        return REGEX_VIDEO_LENGTH.search(self.stream_data_js).group(1)

    @cached_property
    def m3u8_base_url(self) -> str:
        """Returns the master m3u8 URL of the video"""
        return self.urls_list[0]

    @cached_property
    def direct_download_urls(self) -> list:
        """returns the CDN URLs of the video (direct download links)"""
        _ = []
        for idx, url in enumerate(self.urls_list):
            if idx != 0:
                _.append(url)
        return _

    @cached_property
    def video_qualities(self) -> list:
        """Returns the available qualities of the video"""
        quals = self.direct_download_urls
        qualities = set()
        for url in quals:
            match = PATTERN_RESOLUTION.search(url)
            if match:
                qualities.add(match.group(1).strip("p"))
        return sorted(qualities, key=int)

    async def get_segments(self, quality) -> list:
        """Returns a list of segments by a given quality for HLS streaming"""
        return await self.core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)

    async def download(self, quality, path="./", callback: callback_hint = None, no_title=False, remux: bool = False,
                 callback_remux=None, start_segment: int = 0, stop_event: threading.Event | None = None,
                 segment_state_path: str | None = None, segment_dir: str | None = None,
                 return_report: bool = False, cleanup_on_stop: bool = True, keep_segment_dir: bool = False, use_hls: bool = True
                 ) -> bool | DownloadReport:
        """
        :param callback:
        :param quality:
        :param path:
        :param no_title:
        :param remux:
        :param callback_remux:
        :param start_segment:
        :param stop_event:
        :param segment_state_path:
        :param segment_dir:
        :param return_report:
        :param cleanup_on_stop:
        :param keep_segment_dir:
        :param use_hls:
        :return:
        """
        if not no_title:
            path = os.path.join(path, f"{self.title}.mp4")

        if use_hls:
            try:
                return await self.core.download(video=self, quality=quality, path=path, callback=callback, remux=remux,
                                  callback_remux=callback_remux, start_segment=start_segment, stop_event=stop_event,
                                  segment_state_path=segment_state_path, segment_dir=segment_dir,
                                  return_report=return_report,
                                  cleanup_on_stop=cleanup_on_stop, keep_segment_dir=keep_segment_dir)
            except ResourceGone:
                raise VideoUnavailable("Video stream unavailable, this is an issue from spankbang itself!")

        else:
            cdn_urls = self.direct_download_urls
            quals = self.video_qualities
            quality_url_map = {qual: url for qual, url in zip(quals, cdn_urls)}

            quality_map = {
                "best": max(quals, key=lambda x: int(x)),
                "half": sorted(quals, key=lambda x: int(x))[len(quals) // 2],
                "worst": min(quals, key=lambda x: int(x))
            }

            selected_quality = quality_map[quality]
            download_url = quality_url_map[selected_quality]
            self.logger.info(f"Downloading legacy with URL -->: {download_url}")
            await self.core.legacy_download(url=download_url, path=path, callback=callback, stop_event=stop_event)
            return True


class Client(Helper):
    def __init__(self, core: BaseCore = BaseCore(RuntimeConfig())):
        super().__init__(core, video_constructor=Video)
        self.core = core
        self.core.configuration.use_http2 = False
        self.core.initialize_session()
        assert isinstance(self.core.session, AsyncSession)
        self.core.session.headers.clear()
        self.core.session.headers.update(headers)
        self.core.session.cookies.update(cookies)

    async def get_video(self, url) -> Video:
        video = Video(url, core=self.core)
        return await video.init()

    async def get_channel(self, url: str) -> Channel:
        channel = Channel(url=url, core=self.core)
        return await channel.init()

    async def get_pornstar(self, url: str) -> Pornstar:
        pornstar = Pornstar(url=url, core=self.core)
        return await pornstar.init()

    async def get_creator(self, url: str) -> Creator:
        creator = Creator(url=url, core=self.core)
        return await creator.init()

    async def search(self, query,
                filter: Literal["trending", "new", "featured", "popular"] | None = None,
                quality: Literal["hd", "fhd", "uhd"] | None = None,
                duration: Literal["10", "20", "40"] | None = None,
                date: Literal["d", "w", "m", "y"] | None = None,
                pages: int = 2, videos_concurrency: int | None = None,
                pages_concurrency: int | None = None
                 ):
        """
        :param query:
        :param filter:
        :param quality: hd = 720p, fhd = 1080p, uhd = 4k ->: DEFAULT: All qualities
        :param duration: 10 = 10 min, 20 = 20 min, 40 = 40+ min ->: DEFAULT: All durations
        :param date: "d" = day, "w" = week, "m" = month, "y" = year -->: DEFAULT: All dates
        :param pages: How many pages to fetch
        :param pages_concurrency: How many pages to scrape at the same time
        :param videos_concurrency: How many videos to scrape at the same time
        """

        BASE_HOST = "www.spankbang.com"
        path = f"/s/{quote(query)}/"
        params = {}

        if quality:
            params["q"] = quality

        if date:
            params["p"] = date

        if duration:
            params["m"] = duration

        if filter and filter != "trending":
            params["o"] = filter

        query_str = urlencode(params, doseq=True)
        self.url = urlunsplit(("https", BASE_HOST, path, query_str, ""))
        page_urls = [self.url]

        for page in range(2, pages + 2):
            parts = urlsplit(self.url)
            path = parts.path.rstrip("/") + f"/{page}/"
            url = urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
            page_urls.append(url)

        videos_concurrency = videos_concurrency or self.core.configuration.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.configuration.pages_concurrency
        assert videos_concurrency and pages_concurrency

        async for video in self.iterator(target_page_urls=page_urls, video_link_extractor=extractor, max_video_concurrency=videos_concurrency,
                                 max_page_concurrency=pages_concurrency):
            yield video
