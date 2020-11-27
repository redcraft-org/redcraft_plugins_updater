import logging
import cloudscraper
import requests
import os

from bs4 import BeautifulSoup
from tqdm import tqdm

from utils.cloudproxy_manager import CloudProxyManager

from download.sources.direct_source import DirectSource


class SpigotmcSource(DirectSource):

    base_url = 'https://www.spigotmc.org'

    # Needs to be a popular plugin with an external download
    plugin_to_escalate_token = 'https://www.spigotmc.org/resources/fast-async-worldedit-voxelsniper.13932/download?version=320370'

    session = None
    logout_url = None
    session_escalate_count = 0

    def __init__(self, login=None, password=None, cloudproxy_url=None):
        self.login = os.environ.get('SPIGOTMC_LOGIN', login)
        self.password = os.environ.get('SPIGOTMC_PASSWORD', password)
        self.cloudproxy_url = os.environ.get('CLOUDPROXY_URL', cloudproxy_url or 'http://localhost:8191/v1')

        # Initialize our Cloudscraper instance and go on the homepage to get first cookies
        self.session = cloudscraper.create_scraper()
        self.escalate_token(self.base_url)
        self.session.get('{}/login'.format(self.base_url))

        if self.login and self.password:
            data = {
                'login': self.login,
                'password': self.password,
                'register': '0',
                'remember': '0'
            }

            # Post our credentials on the login form and try to extract the logout link
            login_response = self.session.post('{}/login/login'.format(self.base_url), data=data)
            login_parser = BeautifulSoup(login_response.text, features='html.parser')

            if not login_parser.find('a', {'class': 'LogOut'}):
                raise ValueError('Couldn\'t get a logout link, login probably failed.')
        else:
            logging.warning('Could not find SpigotMC credentials, will try to download anonymously')

        self.escalate_token(self.plugin_to_escalate_token)


    def escalate_token(self, url):
        # This method is very important!
        # It is used to bypass a limitation of cloudscraper that returns the following exception:

        # cloudscraper.exceptions.CloudflareChallengeError
        # Detected a Cloudflare version 2 Captcha challenge, This feature is not available in the opensource (free) version.

        # To bypass this, we copy the cookies and user agent from the cloudscraper session, put it in CloudProxy and
        # try to download a plugin (with an external download or CloudProxy will fail) and inject the now escaleted
        # tokens back into our cloudscraper session

        self.session_escalate_count += 1

        for _ in tqdm(range(0, 1), desc='Escalating SpigotMC.org token try {}'.format(self.session_escalate_count)):
            cloudproxy_client = CloudProxyManager(cloudproxy_url=self.cloudproxy_url, user_agent=self.session.headers['User-Agent'])

            # Prepare our cookie object from cloudscraper to CloudProxy
            cookies = []
            for cookie in self.session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain
                })

            # Do our first request to the protected URL
            cloudproxy_client.request(url, cookies=cookies)

            # Do our first second to the homepage of SpigotMC.org to get our escalated credentials
            escalate_base_cookies_response = cloudproxy_client.request(self.base_url)

            escalated_cookies = escalate_base_cookies_response.json().get('solution', {}).get('cookies', [])

            cloudproxy_client.clear_cloudproxy_sessions()

            # Replace cloudscraper cookies with escalated ones from CloudProxy
            self.session.cookies.clear()
            for cookie in escalated_cookies:
                cookie_obj = requests.cookies.create_cookie(cookie['name'], cookie['value'], domain=cookie['domain'])
                self.session.cookies.set_cookie(cookie_obj)

    def download_element(self, url, **kwargs):
        # Browse the plugin page
        plugin_page_response = self.session.get(url)
        plugin_page_parser = BeautifulSoup(plugin_page_response.text, features='html.parser')

        download_button = plugin_page_parser.find('label', {'class': 'downloadButton'})
        size_or_external = download_button.find('small', {'class': 'minorText'}).text

        # Ignore if it's an external site, we can't make edge cases for every website out there
        if size_or_external == 'Via external site':
            raise ValueError('Plugin at {} is an external link and is not supported', url)

        # Get download link
        relative_download_link = download_button.find('a').get('href')
        plugin_download_link = '{}/{}'.format(self.base_url, relative_download_link)

        # Download plugin
        plugin_binary_response = self.session.get(plugin_download_link)
        return plugin_binary_response.content
