import httpx
import re


class Source:
    client = httpx.AsyncClient(timeout=60)

    async def download_element(self, url, filter=None):
        release_url = await self.get_release_url(url, filter)
        return await self.download_release(release_url)

    async def get_release_url(self, url, _filter):
        raise NotImplementedError()

    async def download_release(self, release_url):
        print(release_url)
        resp = await self.client.get(release_url)
        return resp.content

    def get_filter_regex(self, _filter):
        return re.compile(_filter.replace("*", ".+"))
