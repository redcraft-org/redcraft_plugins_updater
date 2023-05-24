import os
import requests


from download.sources.source import Source


class FabricmcSource(Source):
    async def get_release_url(self, url, file_filter=None, **kwargs):
        # Get fabric version
        response = await self.client.get(url)
        fabric_versions = response.json()

        if fabric_versions is not None and len(fabric_versions) >= 1:
            fabric_version = fabric_versions[0]
            fabric_version = fabric_version["loader"]["version"]
        else:
            raise Exception("...")

        # Get installer version
        installers_url = "https://meta.fabricmc.net/v2/versions/installer"
        response = await self.client.get(installers_url)
        installer_versions = response.json()

        if fabric_versions is not None and len(fabric_versions) >= 1:
            installer_version = installer_versions[0]
            installer_version = installer_version["version"]
        else:
            raise Exception("...")
        
        # Create url lastest fabric
        return f"{url}/{fabric_version}/{installer_version}/server/jar"
