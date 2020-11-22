import requests

class DirectSource:

    def download_element(self, url):
        return requests.get(url).content
