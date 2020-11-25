import requests

from download.sources.direct_source import DirectSource


class GithubSource(DirectSource):

    session = None

    def __init__(self):
        self.session = requests.session()

    def download_element(self, url, filter=None, **kwargs):
        filter_regex = self.get_filter_regex(filter)

        user_repo_id = url.split('github.com/')[1].strip('/')

        # Get releases on the GitHub API
        github_json_url = 'https://api.github.com/repos/{}/releases'.format(user_repo_id)

        github_releases = self.session.get(github_json_url).json()

        for release in github_releases:
            for asset in release.get('assets') or []:
                if filter_regex.match(asset['name']):
                    asset_url = asset['browser_download_url']
                    # Download and return the release
                    return self.session.get(asset_url).content

        raise ValueError('Could not find a matching a matching artifact "{}" at {}'.format(
            filter, github_json_url))
