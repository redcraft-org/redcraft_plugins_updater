import os
import requests


from download.sources.source import Source


class FabricmcSource(Source):
    INSTALLERS_URL = "https://meta.fabricmc.net/v2/versions/installer"
    async def get_release_url(self, url, **kwargs):
        # Get fabric version
        response = await self.client.get(url)
        fabric_versions = response.json()

        if fabric_versions is not None and len(fabric_versions) >= 1:
            fabric_version = fabric_versions[0]
            fabric_version = fabric_version["loader"]["version"]
        else:
            raise Exception("Url `{url}` unvalid")

        # Get installer version
        response = await self.client.get(self.INSTALLERS_URL)
        installer_versions = response.json()

        if fabric_versions is not None and len(fabric_versions) >= 1:
            installer_version = installer_versions[0]
            installer_version = installer_version["version"]
        else:
            raise Exception("INSTALLERS_URL `{self.INSTALLERS_URL}` unvalid")
        
        # Create url lastest fabric
        return f"{url}/{fabric_version}/{installer_version}/server/jar"
