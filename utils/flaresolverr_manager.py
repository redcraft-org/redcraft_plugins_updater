import traceback
import logging
import requests


class FlareSolverrManager:
    # (connect timeout, read timeout) — keep connect short so unreachable hosts
    # fail fast, but allow long reads since solving a challenge can take a while.
    REQUEST_TIMEOUT = (10, 180)
    SOLVE_TIMEOUT_MS = 120000

    def __init__(self, flaresolverr_url=None):
        self.logger = logging.getLogger("FlareSolverrManager")
        self.session = requests.session()
        self.flaresolverr_url = flaresolverr_url or "http://localhost:8191/v1"

        # We clear all sessions to make sure to not have conflicts
        self.clear_flaresolverr_sessions()

        session_create_request = {"cmd": "sessions.create"}
        session_create_response = requests.post(
            self.flaresolverr_url,
            json=session_create_request,
            timeout=self.REQUEST_TIMEOUT,
        )

        self.flaresolverr_session = session_create_response.json().get("session")

    def clear_flaresolverr_sessions(self):
        # Get session list
        session_list_request = {"cmd": "sessions.list"}
        session_list_response = requests.post(
            self.flaresolverr_url,
            json=session_list_request,
            timeout=self.REQUEST_TIMEOUT,
        )

        sessions = session_list_response.json().get("sessions")

        # Clear each session
        if sessions:
            for session_id in sessions:
                session_destroy_request = {
                    "cmd": "sessions.destroy",
                    "session": session_id,
                }
                requests.post(
                    self.flaresolverr_url,
                    json=session_destroy_request,
                    timeout=self.REQUEST_TIMEOUT,
                )

    def request(self, url, method="GET", cookies=None, post_data=None, tries=3):
        flaresolverr_request = {
            "cmd": "request.{}".format(method.lower()),
            "url": url,
            "session": self.flaresolverr_session,
            "maxTimeout": self.SOLVE_TIMEOUT_MS,
        }

        if cookies:
            flaresolverr_request["cookies"] = cookies

        if post_data is not None:
            flaresolverr_request["postData"] = post_data

        flaresolverr_response = None
        last_error = None

        for try_count in range(tries):
            try:
                flaresolverr_response = self.session.post(
                    self.flaresolverr_url,
                    json=flaresolverr_request,
                    timeout=self.REQUEST_TIMEOUT,
                )

                status_code = flaresolverr_response.status_code

                if status_code >= 500:
                    raise ValueError(
                        "FlareSolverr request failed, got status code {}: {}".format(
                            status_code, flaresolverr_response.content
                        )
                    )

                break
            except Exception as error:
                self.logger.warning(
                    "FlareSolverr error {}/{}: {}: {}".format(
                        try_count + 1, tries, type(error).__name__, error
                    )
                )
                last_error = error
                traceback.print_exc()

        if not flaresolverr_response and last_error:
            raise last_error

        return flaresolverr_response
