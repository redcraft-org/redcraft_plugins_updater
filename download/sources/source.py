import httpx
import re


class Source:
    client = httpx.AsyncClient(timeout=60)

    async def download_element(self, url, **kwargs):
        release_url = await self.get_release_url(url, **kwargs)
        return await self.download_release(release_url)

    async def get_release_url(self, url, **kwargs):
        raise NotImplementedError()

    async def download_release(self, release_url):
        resp = await self.client.get(release_url)
        return resp.content

    def get_filter_regex(self, file_filter):
        return re.compile(file_filter.replace("*", ".+"))
