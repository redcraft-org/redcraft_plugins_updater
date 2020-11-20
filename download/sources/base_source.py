import requests

class BaseSource:

    def download_element(self, url):
        return requests.get(url).content
