import pytest
from ..api import Client, Channel
from ..modules.consts import extractor
from base_api.modules.config import IteratorConfig

HTML_CHANNEL_FIXTURE = """<main class="main-container" data-testid="main">
    <div class=" responsive-page mx-auto px-4 sm:px-6 xl:px-10" data-testid="channel-page" none="">
        <div class="mb-4 flex flex-col gap-4 xl:mb-6">
            <div class="flex-col-reverse flex w-full justify-between gap-6 xl:flex-row xl:gap-12 2xl:gap-20">
                <div class="flex w-full flex-col gap-4 md:flex-row" data-testid="profile-detail">
                    <div class="flex gap-4 xl:gap-6">
                        <div class="flex h-32 shrink-0 basis-24 items-center xl:h-[8.625rem]">
                            <a href="/o5/channel/filthy+kings/">
                                <img class="w-full rounded" src="//spankbang.com/avatar/250/channel_3298.jpg" alt="Filthy Kings" title="Filthy Kings" data-testid="profile-detail-image">
                            </a>
                        </div>
                        <div x-data="{ showTooltip: false }" class=" flex flex-grow flex-col justify-center gap-4 md:gap-2">
                            <div class="relative flex flex-row items-center gap-1 xl:gap-2">
                                <h1 class="p-0 text-title-sm font-bold capitalize text-primary md:text-title-md xl:text-title-md" data-testid="profile-name">
                                    Filthy Kings
                                </h1>
                            </div>
                            <div class="hidden md:block">
                                <div class="flex flex-row flex-wrap gap-2 md:gap-4" data-testid="profile-stats">
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Videos: <em class="not-italic text-primary">320</em>
                                        </span>
                                    </div>
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Views: <em class="not-italic text-primary">4.1M</em>
                                        </span>
                                    </div>
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Subscribers: <em class="not-italic text-primary">7.7K</em>
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="js-media-list grid h-fit grid-flow-dense gap-x-2 gap-y-4 grid-cols-4 !grid-cols-4 four-col" x-data="videoList">
            <div data-testid="video-item" data-id="17038576" class=" js-video-item   z-0 flex flex-col">
                <a href="/a571s/video/mylf+seeker+big+ass+asian+milf+destroyed">
                    <picture>
                        <img src="https://tbi.sb-cd.com/t/17038576/77/8e/w:500/t6-enh/mylf-seeker-big-ass-asian-mi.jpg" loading="lazy" alt="MYLF SEEKER - Big Ass Asian MILF Destroyed" class=" relative z-0 aspect-video w-full rounded object-contain">
                    </picture>
                    <div class="text-body-sm text-primary absolute bottom-2 left-2 rounded bg-neutral-900/75 px-1" data-testid="video-item-resolution">
                        4K
                    </div>
                    <div class="text-body-sm text-primary absolute right-2 bottom-2 rounded bg-neutral-900/75 px-1" data-testid="video-item-length">
                        15m
                    </div>
                </a>
                <div x-data="videoInfo" data-testid="video-info-with-badge" class="responsive-page mt-1.5">
                    <div class="flex justify-between">
                        <span class="flex min-w-0 items-center">
                            <span data-testid="badge" data-badge="channel" class="mr-0.5 inline-flex text-icon-2xs text-icon-entity md:mr-1">
                                <svg class="i_svg i_icon-video-camera-outlined"><use xlink:href="#icon-video-camera-outlined"></use></svg>
                            </span>
                            <a data-testid="title" class="!inline truncate" href="/o5/channel/filthy+kings/">
                                <span class="text-action-tertiary text-body-sm  md:text-body-md">Filthy Kings</span>
                            </a>
                        </span>
                        <span class="ml-0.5 flex items-center justify-end whitespace-nowrap text-body-sm text-tertiary">
                            <span data-testid="views" class="mr-1 flex items-center">
                                <span class="mr-0.5 inline-flex"><svg class="i_svg i_icon-visible-outlined"><use xlink:href="#icon-visible-outlined"></use></svg></span>
                                <span class="md:text-body-md">73</span>
                            </span>
                            <span data-testid="rates" class="mr-1 flex items-center">
                                <span class="mr-0.5 inline-flex"><svg class="i_svg i_icon-thumbs-up"><use xlink:href="#icon-thumbs-up"></use></svg></span>
                                <span class="md:text-body-md">100%</span>
                            </span>
                        </span>
                    </div>
                    <div class="mt-0.5 flex h-10 justify-between gap-0.5">
                        <p class="line-clamp-2 w-11/12">
                            <a href="/a571s/video/mylf+seeker+big+ass+asian+milf+destroyed" title="MYLF SEEKER - Big Ass Asian MILF Destroyed">
                                <span class="text-secondary text-body-md  block">MYLF SEEKER - Big Ass Asian MILF Destroyed</span>
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</main>
"""


def test_extract_channel_data():
    data = Channel._extract_data(HTML_CHANNEL_FIXTURE)
    assert data["name"] == "Filthy Kings"
    assert data["video_count"] == "320"
    assert data["views_count"] == "4.1M"
    assert data["subscribers_count"] == "7.7K"
    assert data["image"] is not None and "channel_3298.jpg" in data["image"]


def test_extractor_channel_videos():
    videos = extractor(HTML_CHANNEL_FIXTURE)
    assert len(videos) == 1
    v = videos[0]
    assert v["title"] == "MYLF SEEKER - Big Ass Asian MILF Destroyed"
    assert v["resolution"] == "4K"
    assert v["length"] == "15m"
    assert v["views"] == "73"
    assert v["rating"] == "100%"
    assert v["tag"] == "Filthy Kings"
    assert "17038576" in v["thumbnail"]
    assert "/a571s/video/mylf+seeker+big+ass+asian+milf+destroyed" in v["url"]


@pytest.mark.asyncio
async def test_attributes():
    client = Client()
    channel = await client.get_channel("https://de.spankbang.com/ho/channel/brazzers/")
    assert isinstance(channel.name, str)
    assert isinstance(channel.views_count, str)
    assert isinstance(channel.image, str)
    assert isinstance(channel.video_count, str)

    idx = 0
    iterator_config = IteratorConfig(
        max_item_concurrency=1,
        max_page_concurrency=1,
        load_specific_sources=("html",),
    )
    async for video in channel.videos(iterator_config=iterator_config):
        idx += 1

        assert isinstance(video.unwrap().title, str)
        if idx == 3:
            break
