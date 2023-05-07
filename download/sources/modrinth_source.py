import json

import requests

from bs4 import BeautifulSoup

from download.sources.source import Source


class ModrinthSource(Source):
    async def get_release_url(self, url, _filter=None):
        modrinth_response = await self.client.get(url)

        modrinth_parser = BeautifulSoup(modrinth_response.text, features="html.parser")

        featured_link = (
            modrinth_parser.find("div", {"class": "featured-version"})
            .find("a")
            .get("href")
        )

        return featured_link
