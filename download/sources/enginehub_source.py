import json

import requests

from bs4 import BeautifulSoup

from download.sources.direct_source import DirectSource


class EnginehubSource(DirectSource):

    session = None

    def __init__(self):
        self.session = requests.session()

    def download_element(self, url, filter=None, **_):
        filter_regex = self.get_filter_regex(filter)

        stripped_url = url.strip("/")

        # Get the last successful build
        enginehub_json_url = "{}/last-successful".format(stripped_url)

        enginehub_response = self.session.get(enginehub_json_url)

        enginehub_parser = BeautifulSoup(enginehub_response.text, features="html.parser")

        enginehub_response = json.loads(enginehub_parser.find("script", id="__NEXT_DATA__").text)

        print(enginehub_parser.find("script", id="__NEXT_DATA__").text)

        for artifact in enginehub_response.get("props", {}).get("pageProps", {}).get("build", {}).get("artifacts") or []:
            # Find and return the file from the build
            if filter_regex.match(artifact["name"]):
                build_type = enginehub_response["props"]["pageProps"]["project"]["buildType"]
                build_id = enginehub_response["props"]["pageProps"]["build"]["build_id"]
                artifact_url = "https://ci.enginehub.org/repository/download/{}/{}:id/{}?guest=1".format(
                    build_type, build_id, artifact["name"]
                )

                print(artifact_url)

                return self.session.get(artifact_url).content

        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                filter, enginehub_json_url
            )
        )
