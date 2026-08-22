from download.sources.source import Source


class PapermcSource(Source):
    API_BASE = "https://fill.papermc.io/v3"

    async def get_release_url(self, url, file_filter=None, **kwargs):
        filter_regex = self.get_filter_regex(file_filter)

        project, version = self._parse_url(url)

        project_url = "{}/projects/{}".format(self.API_BASE, project)
        project_response = await self.client.get(project_url)
        project_response.raise_for_status()
        version_groups = project_response.json()["versions"]

        # The requested version can be a version group (like 1.20 for Paper or
        # 3.0.0 for Velocity), which lists its versions newest first, so try
        # them in order until a build has a matching artifact
        versions = version_groups.get(version, [version])

        for candidate_version in versions:
            build_url = "{}/projects/{}/versions/{}/builds/latest".format(
                self.API_BASE, project, candidate_version
            )
            build_response = await self.client.get(build_url)
            if build_response.status_code != 200:
                continue
            build = build_response.json()

            for download in build.get("downloads", {}).values():
                if filter_regex.match(download["name"]):
                    return download["url"]

        raise ValueError(
            'Could not find a matching artifact "{}" for {} {}'.format(
                file_filter, project, version
            )
        )

    @staticmethod
    def _parse_url(url):
        # URLs look like https://papermc.io/api/v2/projects/waterfall/version_group/1.20/builds
        # or https://fill.papermc.io/v3/projects/paper/versions/1.21
        parts = url.strip("/").split("/")
        try:
            project_index = parts.index("projects")
            project = parts[project_index + 1]
            version = parts[project_index + 3]
        except (ValueError, IndexError):
            raise ValueError(
                "Could not parse PaperMC project and version from URL {}".format(url)
            )
        return project, version
