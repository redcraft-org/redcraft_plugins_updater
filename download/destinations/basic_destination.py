import os


class BasicDestination:

    output_folder = None

    def __init__(self):
        self.output_folder = os.environ.get("OUTPUT_FOLDER", "plugins")

    def save(self, downloaded_binary, source, name, url, **kwargs):
        file_path = os.path.join(self.output_folder, name)

        # Write file to disk
        with open(file_path, "wb") as file:
            file.write(downloaded_binary)
