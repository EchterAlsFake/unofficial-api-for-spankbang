import os.path
import logging
import threading

from typing import Literal, Optional
from functools import cached_property
from base_api.modules.errors import ResourceGone
from base_api.modules.config import RuntimeConfig
from base_api.base import BaseCore, setup_logger, Helper
from urllib.parse import urlunsplit, urlencode, quote, urlsplit

try:
    from modules.consts import *
    from modules.errors import *

except (ImportError, ModuleNotFoundError):
    from .modules.consts import *
    from .modules.errors import *


try:
    import lxml
    parser = "lxml"

except (ImportError, ModuleNotFoundError):
    parser = "html.parser"


class PornstarHelper(Helper):
    """
    Shares the same attributes like Pornstar, Channel and Creator
    """
    def __init__(self, url: str, core: BaseCore, helper_log_level=logging.DEBUG):
        super(PornstarHelper, self).__init__(core, video=Video, log_level=helper_log_level)
        self.url = url
        self.core = core
        self.content = self.core.fetch(self.url)
        self.soup = BeautifulSoup(self.content, parser)

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

    def videos(self, pages: int = 0, videos_concurrency: int = None, pages_concurrency: int = None):
        page_urls = [self.url]
        for page in range(2, pages + 2):
            page_urls.append(f"{self.url}/{page}/")
        
        videos_concurrency = videos_concurrency or self.core.config.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.config.pages_concurrency
        pages_concurrency = pages_concurrency or self.core.config.pages_concurrency

        yield from self.iterator(page_urls=page_urls, pages_concurrency=pages_concurrency,
                                 videos_concurrency=videos_concurrency, extractor=extractor)


class Channel(PornstarHelper):
    pass


class Creator(PornstarHelper):
    pass


class Pornstar(PornstarHelper):
    pass


class Video:
    def __init__(self, url, core: Optional[BaseCore]):
        self.core = core
        self.url = url  # Needed for Porn Fetch
        self.html_content = self.core.fetch(url)
        if '<div class="warning_process">' in self.html_content:
            raise VideoIsProcessing

        self.logger = setup_logger(name="SPANKBANG API - [Video]", log_file=None, level=logging.ERROR)
        self.soup = BeautifulSoup(self.html_content, parser)
        self.extract_script_2()

    def enable_logging(self, log_file: str = None, level=None, log_ip: str = None, log_port: int = None):
        self.logger = setup_logger(name="SPANKBANG API - [Video]", log_file=log_file, level=level, http_ip=log_ip,
                                   http_port=log_port)

    def extract_script_2(self):
        """This extracts the script with the m3u8 URLs which contain the segments used for downloading"""
        self.logger.debug("Trying to extract the second script...")
        main_container = self.soup.find('main', class_='main-container')
        script_tag = main_container.find('script', {'type': 'text/javascript'})
        self.stream_data_js = re.search(r'var stream_data = ({.*?});', script_tag.text.replace("\t", " "), re.DOTALL).group(1)
        m3u8_pattern = re.compile(r"'m3u8': \['(https://[^']+master.m3u8[^']*)'\]")
        resolution_pattern = re.compile(r"'(240p|320p|480p|720p|1080p|4k)': \['(https://[^']+.mp4[^']*)'\]")

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
        return self.soup.find("h1", class_="main_content_title").text.strip()

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
        return REGEX_VIDEO_AUTHOR.search(self.html_content).group(1)

    @cached_property
    def rating(self) -> str:
        """Returns the rating of the video"""
        return REGEX_VIDEO_RATING.search(self.html_content).group(1)

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

    def get_segments(self, quality) -> list:
        """Returns a list of segments by a given quality for HLS streaming"""
        return self.core.get_segments(quality=quality, m3u8_url_master=self.m3u8_base_url)

    def download(self, quality, path="./", callback=None, no_title=False, remux: bool = False,
                 callback_remux=None, start_segment: int = 0, stop_event: Optional[threading.Event] = None,
                 segment_state_path: Optional[str] = None, segment_dir: Optional[str] = None,
                 return_report: bool = False, cleanup_on_stop: bool = True, keep_segment_dir: bool = False, use_hls: bool = True
                 ) -> bool:
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
        :return:
        """
        if not no_title:
            path = os.path.join(path, f"{self.title}.mp4")

        if use_hls:
            try:
                return self.core.download(video=self, quality=quality, path=path, callback=callback, remux=remux,
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
            self.core.legacy_download(url=download_url, path=path, callback=callback, stop_event=stop_event)
            return True


class Client(Helper):
    def __init__(self, core: Optional[BaseCore] = None):
        super().__init__(core, video=Video)
        self.core = core or BaseCore(config=RuntimeConfig())
        self.core.config.use_http2 = False
        self.core.initialize_session()
        self.core.session.headers.clear()
        self.core.session.headers.update(headers)
        self.core.session.cookies.update(cookies)

    def get_video(self, url) -> Video:
        return Video(url, core=self.core)

    def search(self, query,
                filter: Literal["trending", "new", "featured", "popular"] = None,
                quality: Literal["hd", "fhd", "uhd"] = "",
                duration: Literal["10", "20", "40"] = "",
                date: Literal["d", "w", "m", "y"] = "",
                pages: int = 2, videos_concurrency: int = None,
                pages_concurrency: int = None
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

        videos_concurrency = videos_concurrency or self.core.config.videos_concurrency
        pages_concurrency = pages_concurrency or self.core.config.pages_concurrency

        yield from self.iterator(page_urls=page_urls, extractor=extractor, videos_concurrency=videos_concurrency,
                                 pages_concurrency=pages_concurrency)

    def get_channel(self, url: str) -> Channel:
        return Channel(url=url, core=self.core)

    def get_pornstar(self, url: str) -> Pornstar:
        return Pornstar(url=url, core=self.core)

    def get_creator(self, url: str) -> Creator:
        return Creator(url=url, core=self.core)

