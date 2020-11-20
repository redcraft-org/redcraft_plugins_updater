import os

from tqdm import tqdm
from dotenv import load_dotenv

from spigotmc_client import SpigotMcClient


if __name__ == '__main__':
    load_dotenv()

    # Get settings from env or the .env file
    login = os.environ.get('SPIGOTMC_LOGIN')
    password = os.environ.get('SPIGOTMC_PASSWORD')
    output_folder = os.environ.get('OUTPUT_FOLDER', 'plugins')
    cloudproxy_url = os.environ.get('CLOUDPROXY_URL', 'http://localhost:8191/v1')

    client = SpigotMcClient()

    client.log_in(login, password, cloudproxy_url=cloudproxy_url)

    watched_plugins = client.get_watched_plugins()

    # Download every plugin we watch
    for plugin_data in tqdm(watched_plugins.values(), desc='Downloading plugins'):
        new_plugin_data = client.download_plugin(plugin_data, output_folder)
