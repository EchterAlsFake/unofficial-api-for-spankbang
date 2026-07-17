import re

from urllib.parse import urljoin
from selectolax.lexbor import LexborHTMLParser

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
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

def extractor(content: str, base_url: str = "https://www.spankbang.com") -> list[str]:
    video_data = []
    parser = LexborHTMLParser(content)

    video_soup = parser.css('div[x-data="videoList"]')[1]
    divs = video_soup.css("div.js-video-item.z-0.flex.flex-col")

    for div in divs:
        a_tag = div.css_first("a")
        title_tag = div.css_first('a[title]')
        resolution = div.css_first('div[data-testid="video-item-resolution"]')
        length = div.css_first('div[data-testid="video-item-length"]')
        views = div.css_first('span[data-testid="views"]')
        rates = div.css_first('span[data-testid="rates"]')
        tag_link = div.css_first('a[data-testid="title"]')

        video_info = {
            "url": urljoin(base_url, a_tag.attributes.get("href")),
            "title": title_tag.attributes.get("title") if title_tag else None,
            "thumbnail": div.css_first("img").attributes.get("src"),
            "resolution": resolution.text(strip=True) if resolution else None,
            "length": length.text(strip=True) if length else None,
            "views": views.text(strip=True) if views else None,
            "rating": rates.text(strip=True) if rates else None,
            "tag": tag_link.text(strip=True) if tag_link else None
        }

        video_data.append(video_info)

    return video_data