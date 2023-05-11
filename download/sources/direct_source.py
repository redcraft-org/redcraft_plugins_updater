import re

import requests
from download.sources.source import Source

class DirectSource(Source):
    async def get_release_url(self, url, _filter):
        return url
