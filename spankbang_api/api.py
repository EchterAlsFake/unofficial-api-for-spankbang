from __future__ import annotations

import re
import copy
import asyncio
import logging
import os.path
import functools

from typing import ClassVar, Literal, AsyncGenerator
from dataclasses import dataclass
from base_api.modules.config import IteratorConfig, RuntimeConfig
from urllib.parse import urlunsplit, urlencode, quote, urlsplit
from base_api import (
    BaseCore,
    BaseMedia,
    DownloadConfigHLS,
    DownloadConfigRAW,
    ErrorAction,
    ErrorMode,
    Helper,
    MediaLoadError,
    MediaLoadErrors,
    RetryPolicy,
    ScrapeErrorContext,
    ScrapeResult,
    media_field,
)
from base_api.modules.errors import (
    BotProtectionDetected,
    HTTPStatusError,
    InvalidProxy,
    NetworkRequestError,
    ResourceGone,
    UnknownError,
)

from curl_cffi import AsyncSession
from selectolax.lexbor import LexborHTMLParser
from curl_cffi.requests.cookies import Cookies
from base_api.modules.type_hints import DownloadReport
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

from spankbang_api.modules.errors import (NetworkError, NotFound, UnknownNetworkError, BotDetection, VideoUnavailable,
                                          VideoIsProcessing, ProxyError, DownloadFailed)
from spankbang_api.modules.consts import (headers, REGEX_VIDEO_AUTHOR, REGEX_VIDEO_LENGTH, REGEX_VIDEO_RATING,
                                          PATTERN_RESOLUTION, extractor, cookies)


logger = logging.getLogger("Spankbang API")
logger.addHandler(logging.NullHandler())


HELPER_RETRY = RetryPolicy(max_attempts=4, base_delay=0.5, max_delay=8.0)


def make_iterator_config() -> IteratorConfig:
    return IteratorConfig(
        load_specific_sources=("html",),
        item_retry=None,
        page_retry=None,
        page_error_mode=ErrorMode.SKIP,
        item_error_handler=None,
        page_error_handler=None,
    )


def _is_resource_gone(error: BaseException) -> bool:
    if isinstance(error, ResourceGone):
        return True
    if isinstance(error, MediaLoadError):
        return _is_resource_gone(error.original_error)
    if isinstance(error, MediaLoadErrors):
        return any(_is_resource_gone(nested) for nested in error.errors)
    return False


async def on_error(context: ScrapeErrorContext) -> ErrorAction:
    logger.warning(
        "URL: %s, ERROR: %s, Attempt: %s/%s",
        context.url,
        context.error,
        context.attempt,
        context.max_attempts,
    )

    if _is_resource_gone(context.error):
        return ErrorAction.SKIP

    return ErrorAction.RETRY


async def get_html_content(core: BaseCore, url: str) -> str:
    try:
        return await core.fetch_text(url)

    except HTTPStatusError as e:
        if e.status_code == 404:
            raise NotFound(f"Server returned 404 for: {url}") from e
        raise

    except NetworkRequestError as e:
        raise NetworkError(str(e)) from e

    except InvalidProxy as e:
        raise ProxyError(str(e)) from e

    except BotProtectionDetected as e:
        raise BotDetection(str(e)) from e

    except UnknownError as e:
        raise UnknownNetworkError(str(e)) from e


@dataclass(kw_only=True, slots=True)
class PornstarHelper(BaseMedia):
    url: str
    core: BaseCore
    name: str | None = media_field("html")
    video_count: str | None = media_field("html")
    views_count: str | None = media_field("html")
    subscribers_count: str | None = media_field("html")
    image: str | None = media_field("html")

    loader_methods: ClassVar[dict[str, str]] = {"html": "_load_html"}

    async def _load_html(self) -> dict[str, object]:
        html_content = await get_html_content(core=self.core, url=self.url)
        return await asyncio.to_thread(self._extract_data, html_content)

    @staticmethod
    def _extract_data(html_content: str) -> dict:
        parser = LexborHTMLParser(html_content)

        name_node = parser.css_first("h1")
        name = name_node.text(strip=True) if name_node else None
        
        ems = parser.css("em.not-italic.text-primary")
        video_count = ems[0].text(strip=True) if len(ems) > 0 else None
        views_count = ems[1].text(strip=True) if len(ems) > 1 else None
        subscribers_count = ems[2].text(strip=True) if len(ems) > 2 else None
        
        img_node = parser.css_first("img.w-full.rounded")
        image = img_node.attributes.get("src") if img_node else None

        return {
            "name": name,
            "video_count": video_count,
            "views_count": views_count,
            "subscribers_count": subscribers_count,
            "image": image
        }

    async def videos(
        self,
        pages: int = 0,
        iterator_config: IteratorConfig | None = None,
    ) -> AsyncGenerator[ScrapeResult[Video], None]:
        url = self.url
        page_urls = [url]
        for page in range(2, pages + 2):
            page_urls.append(f"{url}/{page}/")
        
        base_url = f"https://{urlsplit(url).netloc}"
        video_extractor = functools.partial(extractor, base_url=base_url)
        helper = Helper(core=self.core, constructor=Video)

        if iterator_config is None:
            iterator_config = make_iterator_config()

        stream = helper.iterator(
            target_page_urls=page_urls,
            item_extractor=video_extractor,
            iterator_config=iterator_config,
        )
        async with stream:
            async for result in stream:
                yield result


class Channel(PornstarHelper):
    pass


class Creator(PornstarHelper):
    pass


class Pornstar(PornstarHelper):
    pass


@dataclass(kw_only=True, slots=True)
class Video(BaseMedia):
    url: str
    core: BaseCore
    title: str | None = media_field("html")
    description: str | None = media_field("html")
    thumbnail: str | None = media_field("html")
    tags: list | None = media_field("html")
    author: str | None = media_field("html")
    image: str | None = media_field("html")
    rating: str | None = media_field("html")
    length: str | None = media_field("html")
    m3u8_base_url: str | None = media_field("html")
    direct_download_urls: list | None = media_field("html")
    video_qualities: list | None = media_field("html")

    # Optional
    tag: str | None = None
    views: str | None = None
    resolution: str | None = None
    video_source_url: str | None = None

    loader_methods: ClassVar[dict[str, str]] = {"html": "_load_html"}

    async def _load_html(self) -> dict[str, object]:
        html_content = await get_html_content(core=self.core, url=self.url)

        if '<div class="warning_process">' in html_content:
            raise VideoIsProcessing

        return await asyncio.to_thread(self._extract_data, html_content)

    @staticmethod
    def _extract_data(html_content: str):
        parser = LexborHTMLParser(html_content)

        main_container = parser.css_first('main.main-container')
        script_tag = main_container.css_first('script', {'type': 'text/javascript'})
        stream_data_js = re.search(r'var stream_data = ({.*?});', script_tag.text().replace("\t", " "), re.DOTALL).group(1)
        m3u8_pattern = re.compile(r"'m3u8': \['(https://[^']+master.m3u8[^']*)']")
        resolution_pattern = re.compile(r"'(240p|320p|480p|720p|1080p|4k)': \['(https://[^']+.mp4[^']*)']")

        # Extract m3u8 master URL
        m3u8_match = m3u8_pattern.search(stream_data_js)
        m3u8_url = m3u8_match.group(1) if m3u8_match else None

        # Extract resolution URLs
        resolution_matches = resolution_pattern.findall(stream_data_js)
        resolution_urls = [url for res, url in resolution_matches]
        # Combine the URLs with m3u8 first
        urls_list = [m3u8_url] + resolution_urls if m3u8_url else resolution_urls
        # (Damn I love ChatGPT xD)

        # Try new redesign selector
        h1 = parser.css_first("h1", {"data-testid": "video-title"})
        if h1:
            title = h1.text(strip=True)

        # Try user's reported selector
        h1 = parser.css_first("h1.headline__title")
        if h1:
            title = h1.text(strip=True)
        
        # Fallback to any h1
        h1 = parser.css_first("h1")
        if h1:
            title = h1.text(strip=True)
            
        # Fallback to meta tags
        meta_title = parser.css_first('meta[property="og:title"]') or parser.css_first('meta[name="twitter:title"]')
        if meta_title:
            title = meta_title.attributes.get("content", "").replace(": Porn - SpankBang", "").strip()

        description = parser.css_first('meta[name="description"]').attributes.get("content")
        thumbnail = parser.css_first("img.absolute.inset-0.block.h-full.w-full.object-cover").attributes.get("src")
        tags = parser.css_first('meta[name="keywords"]').attributes.get("content").split(",")

        author_tag = parser.css_first("p.text-link-secondary.text-body-lg.flex.items-center") or \
                     parser.css_first("p.text-link-secondary.text-body-lg.flex.items-center".replace(" ", "  "))

        if author_tag:
            author = author_tag.text(strip=True)
        
        # Try image alt
        img_tag = parser.css_first("img.lazyload.w-10.h-10.rounded.object-cover")
        if img_tag and img_tag.attributes.get("alt"):
            image = img_tag.attributes.get("alt").strip()

        # Fallback to regex
        try:
            image = REGEX_VIDEO_AUTHOR.search(html_content).group(1)
        except (AttributeError, IndexError):
            pass

        rating_tag = parser.css_first('span[data-testid="upvote-percentage"]')
        if rating_tag:
            rating = rating_tag.text(strip=True)

        # Fallback to regex
        try:
            rating = REGEX_VIDEO_RATING.search(html_content).group(1)
        except (AttributeError, IndexError):
            pass

        length = REGEX_VIDEO_LENGTH.search(stream_data_js).group(1)
        m3u8_base_url = urls_list[0]

        direct_download_urls = []
        for idx, url in enumerate(urls_list):
            if idx != 0:
                direct_download_urls.append(url)

        quals = direct_download_urls
        qualities = set()
        for url in quals:
            match = PATTERN_RESOLUTION.search(url)
            if match:
                qualities.add(match.group(1).strip("p"))
        video_qualities = sorted(qualities, key=int)

        return {
            "title": title,
            "description": description,
            "thumbnail": thumbnail,
            "tags": tags,
            "author": author,
            "image": image,
            "rating": rating,
            "length": length,
            "m3u8_base_url": m3u8_base_url,
            "direct_download_urls": direct_download_urls,
            "video_qualities": video_qualities,
        }


    async def download(self, configuration_hls: DownloadConfigHLS | None = None,
                       configuration_raw: DownloadConfigRAW | None = None,
                       use_hls: bool = True) -> bool | DownloadReport:

        await self.load_fields("title", "m3u8_base_url", "direct_download_urls", "video_qualities")

        config_hls = copy.deepcopy(configuration_hls)
        config_raw = copy.deepcopy(configuration_raw)
        config_hls.m3u8_base_url = self.m3u8_base_url

        if config_hls and not config_hls.no_title:
            config_hls.path = os.path.join(config_hls.path, f"{self.title}.mp4")
        if config_raw and not config_raw.no_title:
            config_raw.path = os.path.join(config_raw.path, f"{self.title}.mp4")

        if use_hls:
            try:
                return await self.core.download(config_hls)

            except ResourceGone:
                raise VideoUnavailable("Video stream unavailable, this is an issue from spankbang itself!")

            except Exception as e:
                raise DownloadFailed(str(e))


        else:
            cdn_urls = self.direct_download_urls
            quals = self.video_qualities
            quality_url_map = {qual: url for qual, url in zip(quals, cdn_urls)}

            quality_map = {
                "best": max(quals, key=lambda x: int(x)),
                "half": sorted(quals, key=lambda x: int(x))[len(quals) // 2],
                "worst": min(quals, key=lambda x: int(x))
            }

            selected_quality = quality_map[config_raw.quality]
            download_url = quality_url_map[selected_quality]
            await self.core.legacy_download(url=download_url, configuration=config_raw)
            return True


class Client:
    def __init__(self, core: BaseCore = BaseCore(RuntimeConfig())):
        self.core = core
        self.core.initialize_session()
        assert isinstance(self.core.session, AsyncSession)
        self.core.session.headers.clear()
        self.core.session.headers.update(headers)
        self.core.session.cookies.update(cookies)

    async def get_video(self, url: str, load_html: bool = True) -> Video:
        video = Video(url=url, core=self.core)
        if load_html:
            await video.load_sources("html")
        return video

    async def get_channel(self, url: str, load_html: bool = True) -> Channel:
        channel = Channel(url=url, core=self.core)
        if load_html:
            await channel.load_sources("html")
        return channel

    async def get_pornstar(self, url: str, load_html: bool = True) -> Pornstar:
        pornstar = Pornstar(url=url, core=self.core)
        if load_html:
            await pornstar.load_sources("html")
        return pornstar

    async def get_creator(self, url: str, load_html: bool = True) -> Creator:
        creator = Creator(url=url, core=self.core)
        if load_html:
            await creator.load_sources("html")
        return creator

    async def search(self, query,
                 filter: Literal["trending", "new", "featured", "popular"] | None = None,
                 quality: Literal["hd", "fhd", "uhd"] | None = None,
                 duration: Literal["10", "20", "40"] | None = None,
                 date: Literal["d", "w", "m", "y"] | None = None,
                 pages: int = 2,
                 iterator_config: IteratorConfig | None = None,
                 ):
        """
        :param query:
        :param filter:
        :param quality: hd = 720p, fhd = 1080p, uhd = 4k ->: DEFAULT: All qualities
        :param duration: 10 = 10 min, 20 = 20 min, 40 = 40+ min ->: DEFAULT: All durations
        :param date: "d" = day, "w" = week, "m" = month, "y" = year -->: DEFAULT: All dates
        :param pages: How many pages to fetch
        :param iterator_config: Iterator concurrency, loading, ordering, and error behavior.
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
        url = urlunsplit(("https", BASE_HOST, path, query_str, ""))
        page_urls = [url]

        for page in range(2, pages + 2):
            parts = urlsplit(url)
            path = parts.path.rstrip("/") + f"/{page}/"
            url = urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
            page_urls.append(url)

        base_url = f"https://{urlsplit(url).netloc}"
        video_extractor = functools.partial(extractor, base_url=base_url)
        helper = Helper(core=self.core, constructor=Video)

        if iterator_config is None:
            iterator_config = make_iterator_config()

        stream = helper.iterator(
            target_page_urls=page_urls,
            item_extractor=video_extractor,
            iterator_config=iterator_config,
        )
        async with stream:
            async for result in stream:
                yield result
