from download.sources.source import Source


class ModrinthSource(Source):
    API_BASE = "https://api.modrinth.com/v2"

    async def get_release_url(self, url, file_filter=None, **kwargs):
        slug = self._extract_slug(url)
        versions_url = "{}/project/{}/version".format(self.API_BASE, slug)

        response = await self.client.get(versions_url)
        response.raise_for_status()
        versions = response.json()

        if not versions:
            raise ValueError("No versions found for Modrinth project {}".format(slug))

        filter_regex = self.get_filter_regex(file_filter) if file_filter else None

        # Modrinth returns versions newest-first.
        for version in versions:
            files = version.get("files", [])
            primary_files = [f for f in files if f.get("primary")] or files

            for candidate in primary_files:
                if filter_regex is None or filter_regex.match(candidate["filename"]):
                    return candidate["url"]

        raise ValueError(
            "No matching file for Modrinth project {} (file_filter={})".format(
                slug, file_filter
            )
        )

    @staticmethod
    def _extract_slug(url):
        # URLs look like https://modrinth.com/{mod,plugin,...}/{slug}[/...]
        # The slug is the segment after the project type.
        path = url.split("modrinth.com/", 1)[-1].strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError("Could not parse Modrinth slug from URL {}".format(url))
        return parts[1]
