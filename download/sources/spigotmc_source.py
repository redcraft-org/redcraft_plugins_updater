import asyncio
import logging
import threading
import time
import cloudscraper
import requests
import os

import pyotp
from bs4 import BeautifulSoup

from utils.flaresolverr_manager import FlareSolverrManager

from download.sources.direct_source import DirectSource


class SpigotmcSource(DirectSource):

    base_url = "https://www.spigotmc.org"
    # Minimum gap between SpigotMC requests to stay under Cloudflare's
    # rate limit (Error 1015). Tuned empirically.
    REQUEST_INTERVAL_SECONDS = 5.0

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

        # cloudscraper sessions are not thread-safe, and FlareSolverr drives a
        # single Chromium instance — serialize all SpigotMC work to avoid
        # corrupting cookies / overloading the solver.
        self._session_lock = threading.Lock()
        self._last_request_at = 0.0

        # Initialize our Cloudscraper instance and go on the homepage to get first cookies
        self.session = cloudscraper.create_scraper()

        # Escalation can fail (e.g. FlareSolverr/Cloudflare bot detection). It
        # must not raise, otherwise the source is never cached and every plugin
        # re-runs the whole flow, hammering the solver and triggering harder
        # blocks.
        self.escalated = False
        try:
            self.escalate_token(self.base_url)
            self.escalated = True
        except Exception as exc:
            self.logger.warning(
                "SpigotMC token escalation failed (%s: %s); continuing without escalation",
                type(exc).__name__,
                exc,
            )

        self.logged_in = False
        if not (self.login and self.password):
            self.logger.warning(
                "Could not find SpigotMC credentials, will try to download anonymously"
            )
        elif not self.escalated:
            self.logger.warning(
                "Skipping SpigotMC login because escalation failed; will try to download anonymously"
            )
        else:
            # Best-effort login. Failure must not raise — if it does, every
            # subsequent SpigotMC download will re-trigger the full escalation
            # flow, which hammers FlareSolverr and trips Cloudflare bot
            # detection across the whole IP.
            try:
                self._attempt_login()
                self.logged_in = True
            except Exception as exc:
                self.logger.warning(
                    "SpigotMC login failed (%s: %s); continuing anonymously",
                    type(exc).__name__,
                    exc,
                )

    def _attempt_login(self):
        # The login POST has to go through FlareSolverr too. cloudscraper's TLS
        # fingerprint differs from Chromium's, so even with valid escalated
        # cookies, Cloudflare flags the POST as a bot request and returns 403.
        from urllib.parse import urlencode

        flaresolverr_client = FlareSolverrManager(
            flaresolverr_url=self.flaresolverr_url
        )

        try:
            login_data = {
                "login": self.login,
                "password": self.password,
                "register": "0",
                "remember": "1",
                "cookie_check": "1",
                "code": pyotp.TOTP(self.totp_secret).now(),
            }
            login_response = flaresolverr_client.request(
                "{}/login/login".format(self.base_url),
                method="POST",
                post_data=urlencode(login_data),
            )
            login_response.raise_for_status()
            login_solution = login_response.json().get("solution", {}) or {}

            response_html = login_solution.get("response", "")
            login_parser = BeautifulSoup(response_html, features="html.parser")

            if login_parser.find("input", {"id": "ctrl_totp_code"}):
                mfa_data = {
                    "code": pyotp.TOTP(self.totp_secret).now(),
                    "trust": "1",
                    "provider": "totp",
                    "_xfConfirm": "1",
                    "_xfToken": "",
                    "remember": "1",
                    "redirect": "{}/".format(self.base_url),
                    "save": "Confirm",
                    "_xfRequestUri": "/login/two-step?redirect=https%3A%2F%2Fwww.spigotmc.org%2F&remember=1",
                    "_xfNoRedirect": "1",
                    "_xfResponseType": "json",
                }
                mfa_response = flaresolverr_client.request(
                    "{}/login/two-step".format(self.base_url),
                    method="POST",
                    post_data=urlencode(mfa_data),
                )
                mfa_response.raise_for_status()
                login_solution = mfa_response.json().get("solution", {}) or {}

            # Confirm we're logged in by checking the homepage for a logout link.
            home_response = flaresolverr_client.request(self.base_url)
            home_response.raise_for_status()
            home_solution = home_response.json().get("solution", {}) or {}

            home_parser = BeautifulSoup(
                home_solution.get("response", ""), features="html.parser"
            )
            if not home_parser.find("a", {"class": "LogOut"}):
                raise ValueError(
                    "Couldn't get a logout link, login probably failed."
                )

            # Transfer cookies + UA from FlareSolverr (the authenticated
            # browser session) back into cloudscraper so plugin downloads use
            # the matching identity.
            self.session.headers["User-Agent"] = home_solution.get("userAgent")
            self.session.cookies.clear()
            for cookie in home_solution.get("cookies", []):
                cookie_obj = requests.cookies.create_cookie(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie["domain"],
                    path=cookie.get("path", "/"),
                    secure=cookie.get("secure", False),
                )
                self.session.cookies.set_cookie(cookie_obj)
        finally:
            try:
                flaresolverr_client.clear_flaresolverr_sessions()
            except Exception:
                pass

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
        # cloudscraper is synchronous (requests-based) and would block the asyncio
        # event loop, so we run it on a thread.
        return await asyncio.to_thread(self._get_release_url_sync, url)

    def _throttle(self):
        # Caller must hold self._session_lock.
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.REQUEST_INTERVAL_SECONDS:
            time.sleep(self.REQUEST_INTERVAL_SECONDS - elapsed)
        self._last_request_at = time.monotonic()

    def _get_release_url_sync(self, url):
        with self._session_lock:
            self._throttle()
            self.logger.info("Fetching SpigotMC plugin page {}".format(url))
            plugin_page_response = self.session.get(url)
            plugin_page_parser = BeautifulSoup(
                plugin_page_response.text, features="html.parser"
            )

            download_button = plugin_page_parser.find(
                "label", {"class": "downloadButton"}
            )
            if download_button is None:
                raise ValueError(
                    "Could not find download button on SpigotMC plugin page {} (HTTP {})".format(
                        url, plugin_page_response.status_code
                    )
                )
            size_or_external = download_button.find("small", {"class": "minorText"}).text

            # Ignore if it's an external site, we can't make edge cases for every website out there
            if size_or_external == "Via external site":
                raise ValueError(
                    "Plugin at {} is an external link and is not supported".format(url)
                )

            # Get download link
            relative_download_link = download_button.find("a").get("href")
            plugin_download_link = "{}/{}".format(self.base_url, relative_download_link)

            return plugin_download_link

    async def download_release(self, release_url):
        return await asyncio.to_thread(self._download_release_sync, release_url)

    def _download_release_sync(self, release_url):
        with self._session_lock:
            self._throttle()
            self.logger.info("Downloading SpigotMC binary from {}".format(release_url))
            resp = self.session.get(release_url)
            return resp.content
