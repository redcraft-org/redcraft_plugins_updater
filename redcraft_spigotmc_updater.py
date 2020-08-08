import os
from zipfile import ZipFile
import json
from urllib.parse import urlencode
import base64
import io

import yaml
import requests
from tqdm import tqdm
from dotenv import load_dotenv
from bs4 import BeautifulSoup


class SpigotMcUpdater:

    base_url = 'https://www.spigotmc.org'

    request_method = os.environ.get('REQUEST_METHOD', 'cloudproxy').lower()

    cloudproxy_url = os.environ.get('CLOUDPROXY_URL', 'http://localhost:8191/v1')
    cloudproxy_session_id = None

    session = None

    def init_session(self):
        if self.request_method == 'cloudscraper':
            import cloudscraper
            self.session = cloudscraper.create_scraper()
            return

        self.session = requests.session()

        if self.request_method == 'cloudproxy':
            session_list_request = {
                'cmd': 'sessions.list'
            }
            session_list_response = self.session.post(self.cloudproxy_url, json=session_list_request)

            for session_id in session_list_response.json().get('sessions'):
                session_destroy_request = {
                    'cmd': 'sessions.destroy',
                    'session': session_id
                }
                session_destroy_response = self.session.post(self.cloudproxy_url, json=session_destroy_request)

            session_create_request = {
                'cmd': 'sessions.create'
            }
            session_create_response = self.session.post(self.cloudproxy_url, json=session_create_request)

            self.cloudproxy_session_id = session_create_response.json().get('session')

    def make_request(self, url, data=None, method='GET', expect_download=False):
        if self.request_method == 'cloudproxy':
            cloudproxy_request = {
                'cmd': 'request.get',
                'url': url,
                'method': method,
                'session': self.cloudproxy_session_id
            }

            if expect_download:
                cloudproxy_request['download'] = True
                cloudproxy_request['maxTimeout'] = 120000

            if data:
                cloudproxy_request['postData'] = urlencode(data)
                cloudproxy_request['headers'] = {'Content-Type': 'application/x-www-form-urlencoded'}

            cloudproxy_response = self.session.post(self.cloudproxy_url, json=cloudproxy_request)
            solution = cloudproxy_response.json().get('solution', {})

            crafted_response = requests.models.Response()
            crafted_response.status_code = solution.get('status')
            crafted_response._content = solution.get('response', '').encode('utf-8')

            return crafted_response

        return self.session.request(method, url, data=data)

    def download_file(self, url):
        return self.make_request(url, expect_download=True)

    def extract_plugin_info(self, file):
        with ZipFile(file, 'r') as plugin_contents:
            with plugin_contents.open('plugin.yml') as plugin_meta_file:
                plugin_metadata = yaml.safe_load(plugin_meta_file)
                plugin_name = plugin_metadata.get('name')
                plugin_version = plugin_metadata.get('version')
                if not plugin_name or not plugin_version:
                    raise ValueError('plugin.yml is not a valid plugin metadata file')

                return {
                    'name': plugin_name,
                    'version': plugin_version
                }

    def spigotmc_login(self):
        self.make_request('{}/login'.format(self.base_url))

        data = {
            'login': os.environ.get('LOGIN'),
            'password': os.environ.get('PASSWORD'),
            'register': '0',
            'remember': '0'
        }

        login_response = self.make_request('{}/login/login'.format(self.base_url), method='POST', data=data)
        login_parser = BeautifulSoup(login_response.text, features='html.parser')

        logout_link = login_parser.find('a', {'class': 'LogOut'})

        if logout_link is None:
            raise ValueError('Couldn\'t get a logout link, login probably failed.')

        return logout_link.get('href')

    def get_existing_plugins(self):
        plugins = {}

        output_folder = os.environ.get('OUTPUT_FOLDER')
        for file_name in tqdm(os.listdir(output_folder), desc='Exploring current versions'):
            file = os.path.join(output_folder, file_name)
            if file.endswith('.jar'):
                try:
                    plugin_metadata = self.extract_plugin_info(file)
                    plugin_name = plugin_metadata['name']
                    plugins[plugin_name] = plugin_metadata
                except Exception as e:
                    print('An exception occurred while reading {} ({})'.format(file, e))

        return plugins

    def get_watched_plugins(self):
        plugins = {}

        first_watched_resources_response = self.make_request('{}/resources/watched'.format(self.base_url))
        first_watched_resources_parser = BeautifulSoup(first_watched_resources_response.text, features='html.parser')

        page_selector_element = first_watched_resources_parser.find('div', {'class': 'PageNav'})
        last_page = int(page_selector_element.get('data-last') or 0) + 1

        for page_number in tqdm(range(1, last_page), desc='Exploring watched plugins pages'):
            current_watched_resources_response = self.make_request('{}/resources/watched?page={}'.format(self.base_url, page_number))
            current_watched_resources_parser = BeautifulSoup(current_watched_resources_response.text, features='html.parser')

            resources = current_watched_resources_parser.findAll('li', {'class': 'resourceListItem'})
            for resource in resources:
                plugin_url_element = resource.find('h3').find('a')
                plugin_url = '{}/{}'.format(self.base_url, plugin_url_element.get('href'))
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

    def download_plugin(self, plugin):
        plugin_page_response = self.make_request(plugin['url'])
        plugin_page_parser = BeautifulSoup(plugin_page_response.text, features='html.parser')

        download_button = plugin_page_parser.find('label', {'class': 'downloadButton'})
        size_or_external = download_button.find('small', {'class': 'minorText'}).text

        if size_or_external == 'Via external site':
            plugin['name'] = plugin['display_name']
            return plugin

        relative_download_link = download_button.find('a').get('href')
        plugin_download_link = '{}/{}'.format(self.base_url, relative_download_link)

        plugin_binary_response = self.download_file(plugin_download_link)

        plugin_data = base64.b64decode(plugin_binary_response.content)

        zip_handle = io.BytesIO(plugin_data)

        file_name = None

        try:
            plugin_metadata = self.extract_plugin_info(zip_handle)
            file_name = '{name}.jar'.format(**plugin_metadata)
            plugin.update(plugin_metadata)
        except Exception:
            # Means it's not a plugin but a zip file
            plugin['name'] = plugin['display_name']
            file_name = '{name}.zip'.format(**plugin)

        file_path = os.path.join(os.environ.get('OUTPUT_FOLDER', 'plugins'), file_name)

        with open(file_path, 'wb') as file:
            file.write(plugin_data)

        plugin['name'] = plugin['display_name']

        return plugin

    def download_plugins(self, plugins):
        updated_plugins = {}
        for plugin_data in tqdm(plugins.values(), desc='Downloading plugins'):
            new_plugin_data = self.download_plugin(plugin_data)
            updated_plugins[new_plugin_data['name']] = new_plugin_data

        return updated_plugins

    def run_pipeline(self):
        self.init_session()

        logout_link = self.spigotmc_login()

        current_plugins = self.get_existing_plugins()

        watched_plugins = self.get_watched_plugins()

        updated_plugins = self.download_plugins(watched_plugins)

        return updated_plugins


if __name__ == '__main__':
    load_dotenv()
    updater = SpigotMcUpdater()
    updated_plugins = updater.run_pipeline()
