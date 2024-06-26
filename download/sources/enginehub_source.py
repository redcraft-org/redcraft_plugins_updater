import json

import requests

from bs4 import BeautifulSoup

from download.sources.source import Source


class EnginehubSource(Source):
    async def get_release_url(self, url, file_filter=None, **kwargs):
        filter_regex = self.get_filter_regex(file_filter)

        stripped_url = url.strip("/")

        # Get the last successful build
        enginehub_json_url = "{}/last-successful".format(stripped_url)

        enginehub_response = await self.client.get(
            enginehub_json_url, follow_redirects=True
        )

        enginehub_response.raise_for_status()

        enginehub_parser = BeautifulSoup(
            enginehub_response.text, features="html.parser"
        )
        script_next_data = enginehub_parser.find("script", id="__NEXT_DATA__")
        enginehub_response = json.loads(script_next_data.next_element)

        for artifact in (
            enginehub_response.get("props", {})
            .get("pageProps", {})
            .get("build", {})
            .get("artifacts")
            or []
        ):
            # Find and return the file from the build
            if filter_regex.match(artifact["name"]):
                build_type = enginehub_response["props"]["pageProps"]["project"][
                    "buildType"
                ]
                build_id = enginehub_response["props"]["pageProps"]["build"]["build_id"]
                artifact_url = "https://ci.enginehub.org/repository/download/{}/{}:id/{}?guest=1".format(
                    build_type, build_id, artifact["name"]
                )

                return artifact_url

        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                file_filter, enginehub_json_url
            )
        )
