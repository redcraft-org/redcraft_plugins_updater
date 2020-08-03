import os
from zipfile import ZipFile
import json

import yaml
import cloudscraper
from tqdm import tqdm
from dotenv import load_dotenv
from bs4 import BeautifulSoup

BASE_URL = 'https://www.spigotmc.org'


def spigotmc_login(session):
    session.get('{}/login'.format(BASE_URL))

    data = {
        'login': os.environ.get('LOGIN'),
        'password': os.environ.get('PASSWORD'),
        'register': '0',
        'remember': '0'
    }

    login_response = session.post('{}/login/login'.format(BASE_URL), data=data)
    login_parser = BeautifulSoup(login_response.text, features='html.parser')

    logout_link = login_parser.find('a', {'class': 'LogOut'})

    if logout_link is None:
        raise ValueError('Couldn\'t get a logout link, login probably failed.')

    return logout_link.get('href')


def get_existing_plugins():
    plugins = {}

    output_folder = os.environ.get('OUTPUT_FOLDER')
    for file_name in tqdm(os.listdir(output_folder), desc='Exploring current versions'):
        file = '{}/{}'.format(output_folder, file_name)
        if file.endswith('.jar'):
            try:
                with ZipFile(file, 'r') as plugin_contents:
                    with plugin_contents.open('plugin.yml') as plugin_meta_file:
                        plugin_metadata = yaml.safe_load(plugin_meta_file)
                        plugin_name = plugin_metadata.get('name')
                        plugin_version = plugin_metadata.get('version')
                        if not plugin_name or not plugin_version:
                            raise ValueError('plugin.yml is not a valid plugin metadata file')

                        plugins[plugin_name] = {
                            'name': plugin_name,
                            'version': plugin_version
                        }
            except Exception as e:
                print('An exception occurred while reading {} ({})'.format(file, e))

    return plugins


def get_watched_plugins(session):
    plugins = {}

    first_watched_resources_response = session.get('{}/resources/watched'.format(BASE_URL))
    first_watched_resources_parser = BeautifulSoup(first_watched_resources_response.text, features='html.parser')

    page_selector_element = first_watched_resources_parser.find('div', {'class': 'PageNav'})
    last_page = int(page_selector_element.get('data-last') or 0) + 1

    for page_number in tqdm(range(1, last_page), desc='Exploring watched plugins pages'):
        current_watched_resources_response = session.get('{}/resources/watched?page={}'.format(BASE_URL, page_number))
        current_watched_resources_parser = BeautifulSoup(current_watched_resources_response.text, features='html.parser')

        resources = current_watched_resources_parser.findAll('li', {'class': 'resourceListItem'})
        for resource in resources:
            plugin_url_element = resource.find('h3').find('a')
            plugin_url = '{}/{}'.format(BASE_URL, plugin_url_element.get('href'))
            plugin_name = plugin_url_element.text
            plugin_version = resource.find('span', {'class': 'version'}).text
            plugin_id = resource.find('input', {'name': 'resource_ids[]'}).get('value')

            plugins[plugin_id] = {
                'id': plugin_id,
                'url': plugin_url,
                'display_name': plugin_name,
                'version': plugin_version
            }

    return plugins


def download_plugin(plugin, session):
    plugin_page_response = session.get(plugin['url'])
    plugin_page_parser = BeautifulSoup(plugin_page_response.text, features='html.parser')

    relative_download_link = plugin_page_parser.find('label', {'class': 'downloadButton'}).find('a').get('href')
    plugin_download_link = '{}/{}'.format(BASE_URL, relative_download_link)

    # The following statement currently fails because of this:
    # https://github.com/VeNoMouS/cloudscraper/issues/258

    plugin_binary_response = session.get(plugin_download_link)

    # TODO REMOVE DEBUG

    print(plugin_binary_response)

    exit(0)

    plugin['name'] = plugin['display_name']

    return plugin


def download_plugins(plugins, session):
    updated_plugins = {}
    for plugin_data in tqdm(plugins.values(), desc='Downloading plugins'):
        new_plugin_data = download_plugin(plugin_data, session)
        updated_plugins[new_plugin_data['name']] = new_plugin_data

    return updated_plugins


if __name__ == '__main__':
    load_dotenv()
    session = cloudscraper.create_scraper(debug=True)

    logout_link = spigotmc_login(session)

    current_plugins = get_existing_plugins()

    watched_plugins = get_watched_plugins(session)

    updated_plugins = download_plugins(watched_plugins, session)
    print(json.dumps(updated_plugins, indent=4))  # TODO remove DEBUG
