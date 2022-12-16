import json

import requests

from bs4 import BeautifulSoup

from download.sources.direct_source import DirectSource


class ModrinthSource(DirectSource):

    session = None

    def __init__(self):
        self.session = requests.session()

    def download_element(self, url, **_):
        modrinth_response = self.session.get(url)

        modrinth_parser = BeautifulSoup(modrinth_response.text, features="html.parser")

        featured_link = modrinth_parser.find("div", {"class": "featured-version"}).find("a").get("href")

        return self.session.get(featured_link).content
