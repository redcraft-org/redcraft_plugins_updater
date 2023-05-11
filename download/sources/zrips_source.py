import json

import requests

from bs4 import BeautifulSoup

from download.sources.source import Source


class ZripsSource(Source):
    async def get_release_url(self, url, **kwargs):
        zrips_response = await self.client.get(url)

        zrips_parser = BeautifulSoup(zrips_response.text, features="html.parser")

        url = url + zrips_parser.find("a").get("href")
        return url
