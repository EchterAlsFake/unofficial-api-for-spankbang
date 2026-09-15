import pytest
from ..api import Client, Pornstar
from ..modules.consts import extractor
from base_api.modules.config import IteratorConfig

HTML_PORNSTAR_FIXTURE = """<main class="main-container" data-testid="main">
    <div class=" responsive-page mx-auto px-4 sm:px-6 xl:px-10" data-testid="pornstar-page" none="">
        <div class="mb-4 flex flex-col gap-4 xl:mb-6">
            <div class=" flex w-full justify-between gap-6 xl:flex-row xl:gap-12 2xl:gap-20">
                <div class="flex w-full flex-col gap-4 md:flex-row" data-testid="profile-detail">
                    <div class="flex gap-4 xl:gap-6">
                        <div class="flex h-32 shrink-0 basis-24 items-center xl:h-[8.625rem]">
                            <img class="flex aspect-3/4 h-full rounded object-cover" src="//spankbang.com/pornstarimg/f/110-250.jpg" alt="Angela White" title="Angela White" data-testid="profile-detail-image">
                        </div>
                        <div x-data="{ showTooltip: false }" class=" flex flex-grow flex-col justify-center gap-4 md:gap-2">
                            <div class="relative flex flex-row items-center gap-1 xl:gap-2">
                                <h1 class="p-0 text-title-sm font-bold capitalize text-primary md:text-title-md xl:text-title-md" data-testid="profile-name">
                                    Angela White
                                </h1>
                            </div>
                            <div class="hidden md:block">
                                <div class="flex flex-row flex-wrap gap-2 md:gap-4" data-testid="profile-stats">
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Videos: <em class="not-italic text-primary">1.2K</em>
                                        </span>
                                    </div>
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Views: <em class="not-italic text-primary">39M</em>
                                        </span>
                                    </div>
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Subscribers: <em class="not-italic text-primary">59K</em>
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="mb-6">
            <div x-data="videoList" class="js-media-list grid h-fit grid-flow-dense gap-x-2 gap-y-4 grid-cols-4 four-col !grid-cols-4" data-testid="video-list">
                <div data-testid="video-item" data-id="17037215" class=" js-video-item   z-0 flex flex-col">
                    <a href="/a55zz/video/brazzers+angela+white+rewards+her+hardworking+employees+with+a+wild+office+threeway">
                        <picture>
                            <img src="https://tbi.sb-cd.com/t/17037215/31/2a/w:300/t6-enh/brazzers-angela-white-reward.jpg" loading="lazy" alt="BRAZZERS - Angela White Rewards Her Hardworking Employees With A Wild Office Threeway" class=" relative z-0 aspect-video w-full rounded object-contain">
                        </picture>
                        <div class="text-body-sm text-primary absolute bottom-2 left-2 rounded bg-neutral-900/75 px-1" data-testid="video-item-resolution">
                            HD
                        </div>
                        <div class="text-body-sm text-primary absolute right-2 bottom-2 rounded bg-neutral-900/75 px-1" data-testid="video-item-length">
                            10m
                        </div>
                    </a>
                    <div x-data="videoInfo" data-testid="video-info-with-badge" class="responsive-page mt-1.5">
                        <div class="flex justify-between">
                            <span class="flex min-w-0 items-center">
                                <span data-testid="badge" data-badge="channel" class="mr-0.5 inline-flex text-icon-2xs text-icon-entity md:mr-1">
                                    <svg class="i_svg i_icon-video-camera-outlined"><use xlink:href="#icon-video-camera-outlined"></use></svg>
                                </span>
                                <a data-testid="title" class="!inline truncate" href="/ho/channel/brazzers/">
                                    <span class="text-action-tertiary text-body-sm  md:text-body-md">BRAZZERS</span>
                                </a>
                            </span>
                            <span class="ml-0.5 flex items-center justify-end whitespace-nowrap text-body-sm text-tertiary">
                                <span data-testid="views" class="mr-1 flex items-center">
                                    <span class="md:text-body-md">18K</span>
                                </span>
                                <span data-testid="rates" class="mr-1 flex items-center">
                                    <span class="md:text-body-md">100%</span>
                                </span>
                            </span>
                        </div>
                        <div class="mt-0.5 flex h-10 justify-between gap-0.5">
                            <p class="line-clamp-2 w-11/12">
                                <a href="/a55zz/video/brazzers+angela+white+rewards+her+hardworking+employees+with+a+wild+office+threeway" title="BRAZZERS - Angela White Rewards Her Hardworking Employees With A Wild Office Threeway">
                                    <span class="text-secondary text-body-md  block">BRAZZERS - Angela White Rewards Her Hardworking Employees With A Wild Office Threeway</span>
                                </a>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</main>
"""


def test_extract_pornstar_data():
    data = Pornstar._extract_data(HTML_PORNSTAR_FIXTURE)
    assert data["name"] == "Angela White"
    assert data["video_count"] == "1.2K"
    assert data["views_count"] == "39M"
    assert data["subscribers_count"] == "59K"
    assert data["image"] is not None and "110-250.jpg" in data["image"]


def test_extractor_pornstar_videos():
    videos = extractor(HTML_PORNSTAR_FIXTURE)
    assert len(videos) == 1
    v = videos[0]
    assert v["title"] == "BRAZZERS - Angela White Rewards Her Hardworking Employees With A Wild Office Threeway"
    assert v["resolution"] == "HD"
    assert v["length"] == "10m"
    assert v["views"] == "18K"
    assert v["rating"] == "100%"
    assert v["tag"] == "BRAZZERS"
    assert "17037215" in v["thumbnail"]
    assert "/a55zz/video/brazzers+angela+white+rewards+her+hardworking+employees+with+a+wild+office+threeway" in v["url"]


@pytest.mark.asyncio
async def test_attributes():
    client = Client()
    pornstar = await client.get_pornstar("https://spankbang.com/32/pornstar/angela+white/")
    assert isinstance(pornstar.name, str)
    assert isinstance(pornstar.views_count, str)
    assert isinstance(pornstar.image, str)
    assert isinstance(pornstar.video_count, str)

    idx = 0
    iterator_config = IteratorConfig(
        max_item_concurrency=1,
        max_page_concurrency=1,
        load_specific_sources=("html",),
    )
    async for video in pornstar.videos(iterator_config=iterator_config):
        idx += 1
        assert isinstance(video.unwrap().title, str)
        if idx == 3:
            break
