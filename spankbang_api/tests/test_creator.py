import pytest
from ..api import Client, Creator
from ..modules.consts import extractor
from base_api.modules.config import IteratorConfig

HTML_CREATOR_FIXTURE = """<main class="main-container" data-testid="main">
    <div class=" responsive-page mx-auto px-4 sm:px-6 xl:px-10" x-data="photosList('creators_profile_page')" data-testid="creator-page" none="">
        <div class="mb-4 flex flex-col gap-4 xl:mb-6">
            <div class="flex-col-reverse flex w-full justify-between gap-6 xl:flex-row xl:gap-12 2xl:gap-20">
                <div class="flex w-full flex-col gap-4 md:flex-row" data-testid="profile-detail">
                    <div class="flex gap-4 xl:gap-6">
                        <div class="flex h-32 shrink-0 basis-24 items-center xl:h-[8.625rem]">
                            <img class="flex aspect-3/4 h-full rounded object-cover" src="//spankbang.com/avatar/creators/976883.jpg?v=1788217243" alt="Yvonna" title="Yvonna" data-testid="profile-detail-image">
                        </div>
                        <div x-data="{ showTooltip: false }" class=" flex flex-grow flex-col justify-center gap-4 md:gap-2">
                            <div class="relative flex flex-row items-center gap-1 xl:gap-2">
                                <h1 class="p-0 text-title-sm font-bold capitalize text-primary md:text-title-md xl:text-title-md" data-testid="profile-name">
                                    Yvonna
                                </h1>
                                <span class="relative top-1 self-center text-body-lg xl:text-title-md">
                                    <svg class="i_svg i_icon-verified-colored"><use xlink:href="#icon-verified-colored"></use></svg>
                                </span>
                            </div>
                            <div class="hidden md:block">
                                <div class="flex flex-row flex-wrap gap-2 md:gap-4" data-testid="profile-stats">
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Videos: <em class="not-italic text-primary">7</em>
                                        </span>
                                    </div>
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Views: <em class="not-italic text-primary">23K</em>
                                        </span>
                                    </div>
                                    <div>
                                        <span class=" text-body-sm text-tertiary md:text-body-md">
                                            Subscribers: <em class="not-italic text-primary">140</em>
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
                <div data-testid="video-item" data-id="17035549" class=" js-video-item   z-0 flex flex-col">
                    <a href="/a54pp/video/would+you+look+twice+tease+lover">
                        <picture>
                            <img src="https://tbi.sb-cd.com/t/17035549/4d/c3/w:300/t6-enh/would-you-look-twice-tease-lo.jpg" loading="lazy" alt="Would you look twice? Tease Lover">
                        </picture>
                        <div class="text-body-sm text-primary absolute bottom-2 left-2 rounded bg-neutral-900/75 px-1" data-testid="video-item-resolution">
                            HD
                        </div>
                        <div class="text-body-sm text-primary absolute right-2 bottom-2 rounded bg-neutral-900/75 px-1" data-testid="video-item-length">
                            6m
                        </div>
                    </a>
                    <div x-data="videoInfo" data-testid="video-info-with-badge" class="responsive-page mt-1.5">
                        <div class="flex justify-between">
                            <span class="flex min-w-0 items-center">
                                <span data-testid="badge" data-badge="creator" class="mr-0.5 inline-flex text-icon-2xs text-icon-entity md:mr-1">
                                    <svg class="i_svg i_icon-verified-colored"><use xlink:href="#icon-verified-colored"></use></svg>
                                </span>
                                <a data-testid="title" class="!inline truncate" href="/kxrn/creator/yvonna/">
                                    <span class="text-action-tertiary text-body-sm  md:text-body-md">Yvonna</span>
                                </a>
                            </span>
                            <span class="ml-0.5 flex items-center justify-end whitespace-nowrap text-body-sm text-tertiary">
                                <span data-testid="views" class="mr-1 flex items-center">
                                    <span class="md:text-body-md">2.5K</span>
                                </span>
                                <span data-testid="rates" class="mr-1 flex items-center">
                                    <span class="md:text-body-md">93%</span>
                                </span>
                            </span>
                        </div>
                        <div class="mt-0.5 flex h-10 justify-between gap-0.5">
                            <p class="line-clamp-2 w-11/12">
                                <a href="/a54pp/video/would+you+look+twice+tease+lover" title="Would you look twice? Tease Lover">
                                    <span class="text-secondary text-body-md block">Would you look twice? Tease Lover</span>
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


def test_extract_creator_data():
    data = Creator._extract_data(HTML_CREATOR_FIXTURE)
    assert data["name"] == "Yvonna"
    assert data["video_count"] == "7"
    assert data["views_count"] == "23K"
    assert data["subscribers_count"] == "140"
    assert data["image"] is not None and "976883.jpg" in data["image"]


def test_extractor_creator_videos():
    videos = extractor(HTML_CREATOR_FIXTURE)
    assert len(videos) == 1
    v = videos[0]
    assert v["title"] == "Would you look twice? Tease Lover"
    assert v["resolution"] == "HD"
    assert v["length"] == "6m"
    assert v["views"] == "2.5K"
    assert v["rating"] == "93%"
    assert v["tag"] == "Yvonna"
    assert "17035549" in v["thumbnail"]
    assert "/a54pp/video/would+you+look+twice+tease+lover" in v["url"]


@pytest.mark.asyncio
async def test_attributes():
    client = Client()
    creator = await client.get_creator("https://spankbang.com/kxrn/creator/yvonna/")
    assert isinstance(creator.name, str)
    assert isinstance(creator.views_count, str)
    assert isinstance(creator.image, str)
    assert isinstance(creator.video_count, str)

    idx = 0
    iterator_config = IteratorConfig(
        max_item_concurrency=1,
        max_page_concurrency=1,
        load_specific_sources=("html",),
    )
    async for video in creator.videos(iterator_config=iterator_config):
        idx += 1
        assert isinstance(video.unwrap().title, str)
        if idx == 3:
            break
