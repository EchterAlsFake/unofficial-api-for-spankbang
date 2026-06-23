import re

from typing import List
from bs4 import BeautifulSoup

try:
    import lxml
    parser = "lxml"

except (ImportError, ModuleNotFoundError):
    parser = "html.parser"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
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
REGEX_VIDEO_PROCESSING = re.compile(r'<div class="warning_process">')

def extractor(content: str, base_url: str = "https://www.spankbang.com") -> List[str]:
    video_urls = []
    soup = BeautifulSoup(content, parser)
    video_soup = soup.find_all("div", attrs={"x-data": "videoList"})[1]

    divs = video_soup.find_all("div", class_="js-video-item z-0 flex flex-col")

    if not divs:
        divs = soup.find_all("div", class_=" js-video-item  z-0 flex flex-col")

    from urllib.parse import urljoin
    for div in divs:
        url = div.find("a").get("href")
        video_urls.append(urljoin(base_url, url))

    return video_urls