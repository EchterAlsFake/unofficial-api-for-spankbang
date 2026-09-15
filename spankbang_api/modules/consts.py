import re

from urllib.parse import urljoin
from selectolax.lexbor import LexborHTMLParser

headers = {
    "Origin": "https://www.spankbang.com",
    "Referer": "https://www.spankbang.com/",
}

cookies = {
    "age_pass": "1",
    "pg_interstitial_v5": "1",
    "pg_pop_v5": "1",
    "player_quality": "1080",
    "preroll_skip": "1",
    "backend_version": "main",
    "videos_layout": "four-col"
}

PATTERN_RESOLUTION = re.compile(r'(\d+p)\.mp4')
REGEX_VIDEO_RATING = re.compile(r'<span class="rate">(.*?)</span>')
REGEX_VIDEO_AUTHOR = re.compile(r'<span class="name">(.*?)</span>')
REGEX_VIDEO_LENGTH = re.compile(r"'length'\s*:\s*(\d+)")

def extractor(content: str, base_url: str = "https://www.spankbang.com") -> list[dict[str, object]]:
    video_data = []
    parser = LexborHTMLParser(content)

    video_soups = parser.css('div[x-data="videoList"]')
    if len(video_soups) > 1:
        divs = video_soups[-1].css("div.js-video-item") or video_soups[-1].css('div[data-testid="video-item"]')
    elif len(video_soups) == 1:
        divs = video_soups[0].css("div.js-video-item") or video_soups[0].css('div[data-testid="video-item"]')
    else:
        divs = parser.css("div.js-video-item") or parser.css('div[data-testid="video-item"]')

    for div in divs:
        a_tag = div.css_first('a[href*="/video/"]') or div.css_first("a")
        href = a_tag.attributes.get("href") if a_tag else None
        if not isinstance(href, str) or not href:
            continue
        title_tag = div.css_first('a[title]')
        resolution = div.css_first('div[data-testid="video-item-resolution"]')
        length = div.css_first('div[data-testid="video-item-length"]')
        views = div.css_first('span[data-testid="views"]')
        rates = div.css_first('span[data-testid="rates"]')
        tag_link = div.css_first('a[data-testid="title"]')

        img_node = div.css_first("img")
        thumbnail = None
        if img_node:
            thumbnail = img_node.attributes.get("src") or img_node.attributes.get("data-src")

        title = None
        if title_tag and title_tag.attributes.get("title"):
            title = title_tag.attributes.get("title")
        elif title_tag:
            title = title_tag.text(strip=True)
        elif img_node and img_node.attributes.get("alt"):
            title = img_node.attributes.get("alt")

        video_info = {
            "url": urljoin(base_url, href),
            "title": title,
            "thumbnail": thumbnail,
            "resolution": resolution.text(strip=True) if resolution else None,
            "length": length.text(strip=True) if length else None,
            "views": views.text(strip=True) if views else None,
            "rating": rates.text(strip=True) if rates else None,
            "tag": tag_link.text(strip=True) if tag_link else None,
        }

        video_data.append(video_info)

    return video_data
