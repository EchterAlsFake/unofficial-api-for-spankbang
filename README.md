<h1 align="center">Spankbang API</h1> 

<div align="center">
    <a href="https://pepy.tech/project/spankbang_api"><img src="https://static.pepy.tech/badge/spankbang_api" alt="Downloads"></a>
    <a href="https://github.com/EchterAlsFake/spankbang_api/workflows/"><img src="https://github.com/EchterAlsFake/spankbang_api/workflows/CodeQL/badge.svg" alt="CodeQL Analysis"/></a>
    <a href="https://github.com/EchterAlsFake/spankbang_api/workflows/"><img src="https://github.com/EchterAlsFake/spankbang_api/actions/workflows/tests.yml/badge.svg" alt="API Tests"/></a>
</div>

# Description

Spankbang API is an API for Spankbang. It allows you to fetch information from videos using regexes and requests.

# Disclaimer

> [!IMPORTANT] 
> Spankbang API is in violation to Spankbang's ToS!
> If you are the website owner of spankbang.com, contact me at my E-Mail, and I'll take this repository immediately offline.
> EchterAlsFake@proton.me

> [!NOTE]
> This API was made for my other project Porn Fetch, which is the reason why I keep it so minimal. If you have any features you need, please
> just open an Issue and I will add that feature to this API. I will also add other features, later but my priority is primarily downloading videos!

# Quickstart

### Have a look at the [Documentation](https://github.com/EchterAlsFake/API_Docs/blob/master/Porn_APIs/Spankbang.md) for more details

- Install the library with `pip install spankbang_api`
- Or from git using `pip install git+https://github.com/EchterAlsFake/spankbang_api`


```python
from spankbang_api import Client, Quality
# Initialize a Client object
client = Client()

# Fetch a video
video_object = client.get_video("<insert_url_here>")

# Get information from videos
video_object.title
video_object.rating
video_object.description
# See docs for more...

# Download the video
video_object.download(quality=Quality.BEST, path="your_output_path")

```


# Changelog
See [Changelog](https://github.com/EchterAlsFake/spankbang_api/blob/master/README/Changelog.md) for more details.

# Contribution
Do you see any issues or having some feature requests? Simply open an Issue or talk
in the discussions.

Pull requests are welcome :) 

# License
Licensed under the LGPLv3 License

Copyright (C) 2023–2024 Johannes Habel

