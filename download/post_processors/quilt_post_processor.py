import io
from zipfile import ZipFile

import json


class QuiltPostProcessor:
    def process(self, downloaded_binary, source, name, url, **kwargs):
        plugin_info = self.extract_plugin_info(downloaded_binary, name)

        name = "{}-{}.jar".format(name, plugin_info["version"])

        return downloaded_binary, source, name, url

    def extract_plugin_info(self, downloaded_binary, name):
        file_handler = io.BytesIO(downloaded_binary)
        possible_plugin_metadata_file = "quilt.mod.json"
        last_exception = None
        try:
            with ZipFile(file_handler, "r") as plugin_contents:
                with plugin_contents.open(
                    possible_plugin_metadata_file
                ) as plugin_meta_file:
                    plugin_info = json.load(plugin_meta_file)

                    plugin_quilt_loader = plugin_info.get("quilt_loader")
                    plugin_metadata = plugin_quilt_loader.get("metadata")

                    plugin_name = plugin_metadata.get("name")
                    plugin_version = plugin_quilt_loader.get("version")

                    if not plugin_name or not plugin_version:
                        raise ValueError(
                            "{} is not a valid plugin metadata file".format(
                                possible_plugin_metadata_file
                            )
                        )
                    return {"name": plugin_name, "version": plugin_version}
        except Exception as e:
            raise Exception(f"QuiltPostProcessor {name}")
