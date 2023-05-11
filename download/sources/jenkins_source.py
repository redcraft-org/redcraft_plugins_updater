import requests

from download.sources.source import Source


class JenkinsSource(Source):


    async def get_release_url(self, url, file_filter=None):
        filter_regex = self.get_filter_regex(file_filter)

        stripped_url = url.strip("/")

        # Get the last successful build
        jenkins_json_url = "{}/lastSuccessfulBuild/api/json".format(stripped_url)

        jenkins_response = await self.client.get(jenkins_json_url)
        jenkins_response = jenkins_response.json()

        for artifact in jenkins_response.get("artifacts") or []:
            # Find and return the file from the build
            if filter_regex.match(artifact["fileName"]):
                artifact_url = "{}/lastSuccessfulBuild/artifact/{}".format(
                    stripped_url, artifact["relativePath"]
                )

                return artifact_url

        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                file_filter, jenkins_json_url
            )
        )
