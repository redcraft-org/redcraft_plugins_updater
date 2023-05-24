import io
import re
from zipfile import ZipFile
from jproperties import Properties


class FabricmcPostProcessor:
    INFO_FILE_NAME = "install.properties"

    def process(
        self, downloaded_binary, source, name, url, archive_filter=None, **kwargs
    ):
        file_handler = io.BytesIO(downloaded_binary)
        properties = Properties()

        with ZipFile(file_handler, "r") as file_contents:
            with file_contents.open(self.INFO_FILE_NAME) as fabric_info:
                properties.load(fabric_info, "utf-8")

        game_version = properties.get("game-version").data
        name = f"{name}-{game_version}.jar"

        return downloaded_binary, source, name, url
