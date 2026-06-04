<h1 align="center">Spankbang API</h1> 

<div align="center">
    <a href="https://pepy.tech/project/spankbang_api"><img src="https://static.pepy.tech/badge/spankbang_api" alt="Downloads"></a>
    <a href="https://github.com/EchterAlsFake/spankbang_api/workflows/"><img src="https://github.com/EchterAlsFake/spankbang_api/workflows/CodeQL/badge.svg" alt="CodeQL Analysis"/></a>
    <a href="https://github.com/EchterAlsFake/spankbang_api/workflows/"><img src="https://echteralsfake.me/ci/spankbang_api/badge.svg" alt="API Tests"/></a>
</div>

# Description
Spankbang API is an API for Spankbang. It allows you to fetch information from videos using regexes and requests.

> [!CAUTION]
> Spankbang is very strict about rate limiting. This API will **RESPECT** all 429 errors and wait properly. Don't
> try to bypass this and don't ask me to bypass it. I won't.

# Disclaimer

> [!IMPORTANT] 
> Spankbang API is in violation to Spankbang's ToS!
> If you are the website owner of spankbang.com, contact me at my E-Mail, and I'll take this repository immediately offline.
> EchterAlsFake@proton.me

# Features
- Fetch videos + metadata
- Download videos
- Fetch Channels
- Fetch Pornstars
- Search for videos
- Asynchronous
- Built-in caching
- Easy interface
- Great type hinting

#### Networking Features
- HTTP 2.0 / HTTP 3.0
- Browser impersonation
- Custom JA3
- All proxy types
- Proxy authentication
- Speed Limit
- DNS over HTTPS
- And even more...
- All of this is configurable and can be adjusted as you like!

# Quickstart

### Have a look at the [Documentation](https://github.com/EchterAlsFake/API_Docs/blob/master/Porn_APIs/Spankbang.md) for more details

- Install the library with `pip install spankbang_api`
- Or from git using `pip install git+https://github.com/EchterAlsFake/spankbang_api`


```python
from spankbang_api import Client
import asyncio
# Initialize a Client object

async def do_something():
    client = Client()
    
    # Fetch a video
    video_object = await client.get_video("<insert_url_here>")
    
    # Get information from videos
    video_object.title
    video_object.rating
    video_object.description
    # See docs for more...
    
    # Download the video
    await video_object.download(quality="best", path="your_output_path")
asyncio.run(do_something())

```

# Changelog
See [Changelog](https://github.com/EchterAlsFake/spankbang_api/blob/master/README/Changelog.md) for more details.

# Contribution
Do you see any issues or having some feature requests? Simply open an Issue or talk
in the discussions.

Pull requests are welcome :) 

# License
Licensed under the LGPLv3 License

Copyright (C) 2023–2026 Johannes Habel

