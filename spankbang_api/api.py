from __future__ import annotations

import re
import asyncio
import logging
import functools
import argparse

from spankbang_api.modules import errors as provider_errors
from base_api.modules.provider import fetch_content, download_errors, prepare_download_config
from base_api.modules.logger import configure_app_logging, get_logger

from base_api.modules.static_functions import str_to_bool

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
    make_iterator_config,
    is_resource_gone,
    default_on_error,
    scrape_stream,
)
from base_api.modules.errors import ResourceGone

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


logger = get_logger(__name__)


HELPER_RETRY = RetryPolicy(max_attempts=4, base_delay=0.5, max_delay=8.0)


_is_resource_gone = is_resource_gone
on_error = default_on_error


async def get_html_content(core: BaseCore, url: str, *, owner=None) -> str:
    return await fetch_content(core, url, logger=logger, owner=owner,
                               error_types=provider_errors)


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
        html_content = await get_html_content(core=self.core, url=self.url, owner=self)
        return await asyncio.to_thread(self._extract_data, html_content)

    @staticmethod
    def _extract_data(html_content: str) -> dict:
        parser = LexborHTMLParser(html_content)

        name_node = parser.css_first('h1[data-testid="profile-name"]') or parser.css_first("h1")
        name = name_node.text(strip=True) if name_node else None

        img_node = (
            parser.css_first('img[data-testid="profile-detail-image"]')
            or parser.css_first("div[data-testid='profile-detail'] img")
            or parser.css_first("img.w-full.rounded")
        )
        image = (img_node.attributes.get("src") or img_node.attributes.get("data-src")) if img_node else None

        video_count = None
        views_count = None
        subscribers_count = None

        stats_container = parser.css_first('div[data-testid="profile-stats"]')
        if stats_container:
            for span in stats_container.css("span"):
                text = span.text(strip=True)
                em = span.css_first("em")
                val = em.text(strip=True) if em else None
                if not val:
                    continue
                if "Video" in text:
                    video_count = val
                elif "View" in text:
                    views_count = val
                elif "Sub" in text:
                    subscribers_count = val

        if not (video_count and views_count and subscribers_count):
            ems = (
                stats_container.css("em.not-italic.text-primary")
                if stats_container
                else parser.css("em.not-italic.text-primary")
            )
            if not video_count and len(ems) > 0:
                video_count = ems[0].text(strip=True)
            if not views_count and len(ems) > 1:
                views_count = ems[1].text(strip=True)
            if not subscribers_count and len(ems) > 2:
                subscribers_count = ems[2].text(strip=True)

        return {
            "name": name,
            "video_count": video_count,
            "views_count": views_count,
            "subscribers_count": subscribers_count,
            "image": image,
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


def _quality_sort_key(q: str) -> int:
    if q.lower() == "4k":
        return 2160
    digits = "".join(c for c in q if c.isdigit())
    return int(digits) if digits else 0


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
        html_content = await get_html_content(core=self.core, url=self.url, owner=self)

        if '<div class="warning_process">' in html_content:
            raise VideoIsProcessing

        return await asyncio.to_thread(self._extract_data, html_content)

    @staticmethod
    def _extract_data(html_content: str) -> dict[str, object]:
        parser = LexborHTMLParser(html_content)

        # Stream data & URLs
        stream_match = re.search(r'var stream_data\s*=\s*(\{.*?\});', html_content, re.DOTALL)
        stream_data_js = stream_match.group(1) if stream_match else ""

        m3u8_pattern = re.compile(r"'m3u8': \['(https://[^']+master.m3u8[^']*)']")
        resolution_pattern = re.compile(r"'(240p|320p|480p|720p|1080p|4k)': \['(https://[^']+\.mp4[^']*)']")

        # Extract m3u8 master URL
        m3u8_match = m3u8_pattern.search(stream_data_js) if stream_data_js else None
        m3u8_base_url = m3u8_match.group(1) if m3u8_match else None

        # Extract resolution URLs
        resolution_matches = resolution_pattern.findall(stream_data_js) if stream_data_js else []
        direct_download_urls = [url for _res, url in resolution_matches]

        # Extract video qualities
        qualities: set[str] = set()
        for res, _url in resolution_matches:
            qualities.add(res.rstrip("p"))
        if not qualities:
            for url in direct_download_urls:
                match = PATTERN_RESOLUTION.search(url)
                if match:
                    qualities.add(match.group(1).rstrip("p"))
        video_qualities = sorted(qualities, key=_quality_sort_key) if qualities else []

        # Title
        title: str | None = None
        h1_node = (
            parser.css_first('h1[data-testid="video-title"]')
            or parser.css_first("h1.headline__title")
            or parser.css_first("h1")
        )
        if h1_node:
            title = h1_node.text(strip=True)
        if not title:
            meta_title = parser.css_first('meta[property="og:title"]') or parser.css_first('meta[name="twitter:title"]')
            if meta_title and meta_title.attributes.get("content"):
                title = meta_title.attributes.get("content", "").replace(": Porn - SpankBang", "").strip()

        # Description
        description: str | None = None
        desc_node = parser.css_first('div[data-testid="video-description"]')
        if desc_node:
            description = desc_node.text(strip=True)
        if not description:
            meta_desc = parser.css_first('meta[name="description"]') or parser.css_first('meta[property="og:description"]')
            if meta_desc and meta_desc.attributes.get("content"):
                description = meta_desc.attributes.get("content").strip()

        # Thumbnail
        thumbnail: str | None = None
        thumb_node = (
            parser.css_first("#player_cover_img")
            or parser.css_first('div[data-testid="video-play-cover"] img')
            or parser.css_first("img.absolute.inset-0.block.h-full.w-full.object-cover")
        )
        if thumb_node and thumb_node.attributes.get("src"):
            thumbnail = thumb_node.attributes.get("src")
        if not thumbnail:
            meta_thumb = parser.css_first('meta[property="og:image"]')
            if meta_thumb and meta_thumb.attributes.get("content"):
                thumbnail = meta_thumb.attributes.get("content")
        if not thumbnail and stream_data_js:
            cover_match = re.search(r"'(?:cover_image|thumbnail)'\s*:\s*'([^']+)'", stream_data_js)
            if cover_match:
                thumbnail = cover_match.group(1)

        # Tags
        tags: list[str] | None = None
        tags_container = parser.css_first('div[data-testid="video-tags"]')
        if tags_container:
            tags = [a.text(strip=True) for a in tags_container.css("a") if a.text(strip=True)]
        if not tags:
            meta_kw = parser.css_first('meta[name="keywords"]')
            if meta_kw and meta_kw.attributes.get("content"):
                tags = [t.strip() for t in meta_kw.attributes.get("content").split(",") if t.strip()]
        if not tags:
            live_kw_match = re.search(r"var live_keywords\s*=\s*'([^']*)';", html_content)
            if live_kw_match:
                tags = [t.strip() for t in live_kw_match.group(1).split(",") if t.strip()]

        # Author
        author: str | None = None
        profile_node = parser.css_first('div[data-testid="profile"]')
        if profile_node:
            author_elem = profile_node.css_first("p") or profile_node.css_first("a.text-link-primary")
            if author_elem:
                author = author_elem.text(strip=True)
        if not author:
            author_tag = parser.css_first("p.text-link-secondary")
            if author_tag:
                author = author_tag.text(strip=True)
        if not author:
            try:
                author = REGEX_VIDEO_AUTHOR.search(html_content).group(1).strip()
            except (AttributeError, IndexError):
                pass

        # Image (Author thumbnail alt text / profile image)
        image: str | None = None
        img_tag = (
            parser.css_first('div[data-testid="profile"] img')
            or parser.css_first("img.lazyload.w-10.h-10.rounded.object-cover")
        )
        if img_tag and img_tag.attributes.get("alt"):
            image = img_tag.attributes.get("alt").strip()
        if not image:
            try:
                image = REGEX_VIDEO_AUTHOR.search(html_content).group(1).strip()
            except (AttributeError, IndexError):
                pass

        # Rating
        rating: str | None = None
        rating_tag = parser.css_first('span[data-testid="upvote-percentage"]')
        if rating_tag:
            rating = rating_tag.text(strip=True)
        if not rating:
            try:
                rating = REGEX_VIDEO_RATING.search(html_content).group(1).strip()
            except (AttributeError, IndexError):
                pass

        # Length (in seconds)
        length: str | None = None
        if stream_data_js:
            len_match = REGEX_VIDEO_LENGTH.search(stream_data_js)
            if len_match:
                length = len_match.group(1)

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


    @download_errors(DownloadFailed)
    async def download(self, configuration_hls: DownloadConfigHLS | None = None,
                       configuration_raw: DownloadConfigRAW | None = None,
                       use_hls: bool = True) -> bool | DownloadReport:

        try:
            await self.load_fields("title", "m3u8_base_url", "direct_download_urls", "video_qualities")

            if use_hls:
                if configuration_hls is None:
                    raise ValueError("configuration_hls is required for an HLS download")
                config_hls = prepare_download_config(configuration_hls, self.title)
                config_hls.m3u8_base_url = self.m3u8_base_url
                return await self.core.download(config_hls)

            else:
                if configuration_raw is None:
                    raise ValueError("configuration_raw is required for a raw download")
                config_raw = prepare_download_config(configuration_raw, self.title)
                cdn_urls = self.direct_download_urls
                quals = self.video_qualities
                quality_url_map = {qual: url for qual, url in zip(quals, cdn_urls)}

                quality_map = {
                    "best": max(quals, key=_quality_sort_key),
                    "half": sorted(quals, key=_quality_sort_key)[len(quals) // 2],
                    "worst": min(quals, key=_quality_sort_key)
                }

                selected_quality = quality_map[config_raw.quality]
                download_url = quality_url_map[selected_quality]
                return await self.core.legacy_download(url=download_url, configuration=config_raw)
        except ResourceGone as error:
            raise VideoUnavailable(f"Video stream unavailable for {self.url}: {error}") from error


class Client:
    def __init__(self, core: BaseCore | None = None):
        if core is None:
            core = BaseCore(RuntimeConfig())
        self.core = core
        self.core.configuration.http_version = "v3"
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

    def search(self, query,
                 filter: Literal["trending", "new", "featured", "popular"] | None = None,
                 quality: Literal["hd", "fhd", "uhd"] | None = None,
                 duration: Literal["10", "20", "40"] | None = None,
                 date: Literal["d", "w", "m", "y"] | None = None,
                 pages: int = 2,
                 iterator_config: IteratorConfig | None = None,
                 ) -> AsyncGenerator[ScrapeResult[Video], None]:
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

        return scrape_stream(
            core=self.core,
            constructor=Video,
            target_page_urls=page_urls,
            item_extractor=video_extractor,
            iterator_config=iterator_config,
        )



def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SpankBang API Command Line Interface")
    parser.add_argument("--download", metavar="URL", type=str, help="URL to download from")
    parser.add_argument("--quality", metavar="best|half|worst", type=str, default="best", help="The video quality (best, half, worst)")
    parser.add_argument("--file", metavar="FILE", type=str, help="(Optional) Specify a file with URLs (separated with new lines)")
    parser.add_argument("--output", metavar="DIR", type=str, required=True, help="The output path (with filename or directory)")
    parser.add_argument("--no-title", metavar="True,False", type=str, nargs="?", const="True", default="False",
                        help="Whether to apply video title automatically to output path or not")
    return parser


async def run_main(args_list: list[str] | None = None):
    parser = create_parser()
    args = parser.parse_args(args_list)
    no_title = str_to_bool(args.no_title) if isinstance(args.no_title, str) else bool(args.no_title)
    config = DownloadConfigHLS(quality=args.quality, path=args.output, no_title=no_title)

    urls: list[str] = []
    if args.download:
        urls.append(args.download)
    if args.file:
        with open(args.file, "r") as f:
            urls.extend([line.strip() for line in f if line.strip()])

    if not urls:
        parser.print_help()
        return

    client = Client()
    for url in urls:
        print(f"Fetching video information for: {url}")
        try:
            video = await client.get_video(url, load_html=True)
            title = getattr(video, "title", None) or url
            print(f"Starting download for: {title}")
            await video.download(configuration_hls=config)
            print(f"Download complete: {title}")
        except Exception as e:
            logger.exception("CLI failed while processing %s", url)
            print(f"Error downloading {url}: {e}")


def main():
    configure_app_logging(level=logging.INFO)
    try:
        asyncio.run(run_main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")


if __name__ == "__main__":
    main()
