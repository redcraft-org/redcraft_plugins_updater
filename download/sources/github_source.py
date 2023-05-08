import requests


from download.sources.source import Source


class GithubSource(Source):
    async def get_release_url(self, url, _filter=None):
        filter_regex = self.get_filter_regex(_filter)

        user_repo_id = url.split("github.com/")[1].strip("/")

        # Get releases on the GitHub API
        github_json_url = "https://api.github.com/repos/{}/releases".format(
            user_repo_id
        )

        # response = await self.client.get(github_json_url)
        response = requests.get(github_json_url)
        github_releases = response.json()

        for release in github_releases:
            for asset in release.get("assets") or []:
                if filter_regex.match(asset["name"]):
                    asset_url = asset["browser_download_url"]
                    # Download and return the release
                    return asset_url


        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                filter, github_json_url
            )
        )
