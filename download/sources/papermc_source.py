import requests

from download.sources.source import Source


class PapermcSource(Source):
    async def get_release_url(self, url, file_filter=None, **kwargs):
        filter_regex = self.get_filter_regex(file_filter)

        stripped_url = url.strip("/")

        papermc_response = await self.client.get(stripped_url)
        papermc_response = papermc_response.json()

        last_build = papermc_response["builds"][-1]

        download = last_build["downloads"]["application"]
        # Find and return the file from the build
        name = download["name"]
        if filter_regex.match(name):
            artifact_url = "{}/{}/downloads/{}".format(
                stripped_url.replace("version_group", "versions"),
                last_build["build"],
                name,
            )

            return artifact_url

        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                file_filter, stripped_url
            )
        )
