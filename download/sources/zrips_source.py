import json

import requests

from bs4 import BeautifulSoup

from download.sources.direct_source import DirectSource


class ZripsSource(DirectSource):

    session = None

    def __init__(self):
        self.session = requests.session()

    def download_element(self, url, **_):
        zrips_response = self.session.get(url)

        zrips_parser = BeautifulSoup(
            zrips_response.text, features="html.parser")

        return self.session.get(url + zrips_parser.find("a").get("href")).content
