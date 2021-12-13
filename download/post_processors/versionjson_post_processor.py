import io
import json
from zipfile import ZipFile


class VersionjsonPostProcessor:
    def process(self, downloaded_binary, source, name, url, **kwargs):
        with ZipFile(io.BytesIO(downloaded_binary), "r") as server_jar:
            with server_jar.open("version.json") as version_json_file:
                version_json_contents = json.load(version_json_file)
                # UGLY: Could not be bothered to do better
                version = version_json_contents.get("release_target")

                if not version:
                    raise ValueError(
                        "{} does not contain a valid version.json file".format(
                            name)
                    )

                name = "{}-{}.jar".format(name, version)

        return downloaded_binary, source, name, url
