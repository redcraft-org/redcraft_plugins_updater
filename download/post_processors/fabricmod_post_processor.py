import io
from zipfile import ZipFile

import json


class FabricmodPostProcessor:
    def process(self, downloaded_binary, source, name, url, **kwargs):
        plugin_info = self.extract_plugin_info(downloaded_binary)

        name = "{}-{}.jar".format(name, plugin_info["version"])

        return downloaded_binary, source, name, url

    def extract_plugin_info(self, downloaded_binary):
        file_handler = io.BytesIO(downloaded_binary)
        possible_plugin_metadata_files = ["fabric.mod.json"]
        last_exception = None
        for possible_plugin_metadata_file in possible_plugin_metadata_files:
            try:
                with ZipFile(file_handler, "r") as plugin_contents:
                    with plugin_contents.open(
                        possible_plugin_metadata_file
                    ) as plugin_meta_file:
                        plugin_metadata = json.load(plugin_meta_file)
                        plugin_name = plugin_metadata.get("name")
                        plugin_version = plugin_metadata.get("version")

                        if not plugin_name or not plugin_version:
                            raise ValueError(
                                "{} is not a valid plugin metadata file".format(
                                    possible_plugin_metadata_file
                                )
                            )
                        return {"name": plugin_name, "version": plugin_version}
            except Exception as e:
                last_exception = e

        raise last_exception
