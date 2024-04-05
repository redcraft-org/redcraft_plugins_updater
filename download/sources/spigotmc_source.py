import logging
import cloudscraper
import requests
import os

import pyotp
from bs4 import BeautifulSoup

from utils.flaresolverr_manager import FlareSolverrManager

from download.sources.direct_source import DirectSource


class SpigotmcSource(DirectSource):

    base_url = "https://www.spigotmc.org"

    session = None
    logout_url = None
    session_escalate_count = 0

    def __init__(
        self,
        login=None,
        password=None,
        totp_secret=None,
        flaresolverr_url="http://localhost:8191/v1",
    ):
        self.logger = logging.getLogger("SpigotMCSource")
        self.login = os.environ.get("SPIGOTMC_LOGIN", login)
        self.password = os.environ.get("SPIGOTMC_PASSWORD", password)
        self.totp_secret = os.environ.get("SPIGOTMC_TOTP_SECRET", totp_secret)
        self.flaresolverr_url = os.environ.get("FLARESOLVERR_URL", flaresolverr_url)

        # Initialize our Cloudscraper instance and go on the homepage to get first cookies
        self.session = cloudscraper.create_scraper()
        self.escalate_token(self.base_url)

        self.session.get("{}/login".format(self.base_url))

        if self.login and self.password:
            data = {
                "login": self.login,
                "password": self.password,
                "register": "0",
                "remember": "1",
                "cookie_check": "1",
                "code": pyotp.TOTP(self.totp_secret).now(),
            }

            # Post our credentials on the login form and try to extract the logout link
            login_response = self.session.post(
                "{}/login/login".format(self.base_url), data=data
            )

            login_response.raise_for_status()

            login_parser = BeautifulSoup(login_response.text, features="html.parser")

            if login_parser.find("input", {"id": "ctrl_totp_code"}):
                data = {
                    "code": pyotp.TOTP(self.totp_secret).now(),
                    "trust": "1",
                    "provider": "totp",
                    "_xfConfirm": "1",
                    "_xfToken": "",
                    "remember": "1",
                    "redirect": "https://www.spigotmc.org/",
                    "save": "Confirm",
                    "_xfRequestUri": "/login/two-step?redirect=https%3A%2F%2Fwww.spigotmc.org%2F&remember=1",
                    "_xfNoRedirect": "1",
                    "_xfResponseType": "json",
                }

                mfa_response = self.session.post(
                    "{}/login/two-step".format(self.base_url), data=data
                )

                mfa_response.raise_for_status()

            home_page_response = self.session.get(self.base_url)

            home_page_parser = BeautifulSoup(
                home_page_response.text, features="html.parser"
            )

            logout_link = home_page_parser.find("a", {"class": "LogOut"})
            if not logout_link:
                raise ValueError("Couldn't get a logout link, login probably failed.")
        else:
            self.logger.warning(
                "Could not find SpigotMC credentials, will try to download anonymously"
            )

    def escalate_token(self, url):
        # This method is very important!
        # It is used to bypass a limitation of cloudscraper that returns the following exception:

        # cloudscraper.exceptions.CloudflareChallengeError
        # Detected a Cloudflare version 2 Captcha challenge, This feature is not available in the opensource (free) version.

        # To bypass this, we copy the cookies and user agent from the cloudscraper session, put it in FlareSolverr and
        # try to download a plugin (with an external download or FlareSolverr will fail) and inject the now escaleted
        # tokens back into our cloudscraper session

        self.logger.info("Escalating SpigotMC token")

        flaresolverr_client = FlareSolverrManager(
            flaresolverr_url=self.flaresolverr_url
        )

        # Prepare our cookie object from cloudscraper to FlareSolverr
        cookies = []
        for cookie in self.session.cookies:
            cookies.append(
                {
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                }
            )

        # Do our first request to the protected URL
        flaresolverr_client.request(url, cookies=cookies)

        # Do our first second to the homepage of SpigotMC.org to get our escalated credentials
        escalate_base_cookies_response = flaresolverr_client.request(self.base_url)

        escalate_base_cookies_response.raise_for_status()

        solution = escalate_base_cookies_response.json().get("solution", {})

        escalated_cookies = solution.get("cookies", [])

        flaresolverr_client.clear_flaresolverr_sessions()

        self.session.headers["User-Agent"] = solution.get("userAgent")

        # Replace cloudscraper cookies with escalated ones from FlareSolverr
        self.session.cookies.clear()
        for cookie in escalated_cookies:
            cookie_obj = requests.cookies.create_cookie(
                cookie["name"],
                cookie["value"],
                domain=cookie["domain"],
                path=cookie["path"],
                secure=cookie["secure"],
            )
            self.session.cookies.set_cookie(cookie_obj)

    async def get_release_url(self, url, **kwargs):
        # Browse the plugin page
        plugin_page_response = self.session.get(url)
        plugin_page_parser = BeautifulSoup(
            plugin_page_response.text, features="html.parser"
        )

        download_button = plugin_page_parser.find("label", {"class": "downloadButton"})
        size_or_external = download_button.find("small", {"class": "minorText"}).text

        # Ignore if it's an external site, we can't make edge cases for every website out there
        if size_or_external == "Via external site":
            raise ValueError(
                "Plugin at {} is an external link and is not supported", url
            )

        # Get download link
        relative_download_link = download_button.find("a").get("href")
        plugin_download_link = "{}/{}".format(self.base_url, relative_download_link)

        return plugin_download_link

    async def download_release(self, release_url):
        resp = self.session.get(release_url)
        return resp.content
