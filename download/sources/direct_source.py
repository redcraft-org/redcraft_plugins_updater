import re

import requests

class DirectSource:

    def download_element(self, url):
        return requests.get(url).content

    def get_filter_regex(self, filter):
        return re.compile(filter.replace('*', '.+'))
