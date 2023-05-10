import io
from zipfile import ZipFile

import yaml


class PluginPostProcessor:
    def process(self, downloaded_binary, source, name, url, **kwargs):
        plugin_info = self.extract_plugin_info(downloaded_binary)

        name = "{}-{}.jar".format(name, plugin_info["version"])

        return downloaded_binary, source, name, url

    def extract_plugin_info(self, downloaded_binary):
        file_handler = io.BytesIO(downloaded_binary)
        # In order to be compatible with Bukkit and BungeeCord plugins, we need to check two files
        possible_plugin_metadata_files = ["bungee.yml", "plugin.yml"]
        last_exception = None
        for possible_plugin_metadata_file in possible_plugin_metadata_files:
            try:
                with ZipFile(file_handler, "r") as plugin_contents:
                    with plugin_contents.open(
                        possible_plugin_metadata_file
                    ) as plugin_meta_file:
                        # Load yml file and check metadata
                        plugin_metadata = yaml.safe_load(plugin_meta_file)
                        plugin_name = plugin_metadata.get("name")
                        plugin_version = plugin_metadata.get("version")
                        if not plugin_name or not plugin_version:
                            raise ValueError(
                                "{} is not a valid plugin metadata file".format(
                                    possible_plugin_metadata_file
                            download/post_processors/plugin_post_processor.py
                                )
                            )
                        return {"name": plugin_name, "version": plugin_version}
            except Exception as e:
                last_exception = e

        # If we're here, it means we didn't return and everything failed, so we return the last exception we saw
        raise last_exception
