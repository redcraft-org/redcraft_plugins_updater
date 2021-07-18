import requests

from download.sources.direct_source import DirectSource


class PapermcSource(DirectSource):

    session = None

    def __init__(self):
        self.session = requests.session()

    def download_element(self, url, filter=None, **_):
        filter_regex = self.get_filter_regex(filter)

        stripped_url = url.strip("/")

        papermc_response = self.session.get(stripped_url).json()

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

            return self.session.get(artifact_url).content

        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                filter, stripped_url
            )
        )
