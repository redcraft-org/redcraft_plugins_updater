import json
import argparse
from dotenv import load_dotenv

from download.manager import DownloadManager


if __name__ == '__main__':
    load_dotenv()

    parser = argparse.ArgumentParser(description='Update plugins')
    parser.add_argument(
        'plugin_json_file',
        type=argparse.FileType('r'),
        help='The JSON file with the list of the plugins to download'
    )

    args = parser.parse_args()

    # Parse resources
    resources = json.load(args.plugin_json_file)

    # Download resources
    DownloadManager().download_resources(resources)
