import json
from dotenv import load_dotenv

from download.manager import DownloadManager


if __name__ == '__main__':
    load_dotenv()

    with open('resources_to_download.json') as resources_file:
        resources = json.load(resources_file)

        download_manager = DownloadManager()

        download_manager.download_resources(resources)
