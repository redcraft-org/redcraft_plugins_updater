import os
import requests


from download.sources.source import Source


class GithubSource(Source):
    async def get_release_url(self, url, file_filter=None, **kwargs):
        filter_regex = self.get_filter_regex(file_filter)

        user_repo_id = url.split("github.com/")[1].strip("/")

        # Get releases on the GitHub API
        github_json_url = "https://api.github.com/repos/{}/releases".format(
            user_repo_id
        )

        github_token = os.environ.get("GITHUB_TOKEN", None)
        headers = {}
        if github_token is not None:
            headers["Authorization"] = f"token {github_token}"

        response = await self.client.get(github_json_url, headers=headers)
        response.raise_for_status()
        github_releases = response.json()

        for release in github_releases:
            for asset in release.get("assets") or []:
                if filter_regex.match(asset["name"]):
                    asset_url = asset["browser_download_url"]
                    return asset_url

        raise ValueError(
            'Could not find a matching a matching artifact "{}" at {}'.format(
                file_filter, github_json_url
            )
        )
