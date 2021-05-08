import requests


class CloudProxyManager:
    def __init__(self, cloudproxy_url=None, user_agent=None):
        self.session = requests.session()
        self.cloudproxy_url = cloudproxy_url or "http://localhost:8191/v1"
        self.user_agent = user_agent

        # We clear all sessions to make sure to not have conflicts
        self.clear_cloudproxy_sessions()

        session_create_request = {"cmd": "sessions.create"}
        session_create_response = requests.post(
            self.cloudproxy_url, json=session_create_request
        )

        self.cloudproxy_session = session_create_response.json().get("session")

    def clear_cloudproxy_sessions(self):
        # Get session list
        session_list_request = {"cmd": "sessions.list"}
        session_list_response = requests.post(
            self.cloudproxy_url, json=session_list_request
        )

        # Clear each session
        for session_id in session_list_response.json().get("sessions"):
            session_destroy_request = {"cmd": "sessions.destroy", "session": session_id}
            requests.post(self.cloudproxy_url, json=session_destroy_request)

    def request(self, url, method="GET", cookies=None):
        cloudproxy_request = {
            "cmd": "request.{}".format(method.lower()),
            "url": url,
            "session": self.cloudproxy_session,
        }

        if self.user_agent:
            cloudproxy_request["userAgent"] = self.user_agent

        if cookies:
            cloudproxy_request["cookies"] = cookies

        cloudproxy_response = self.session.post(
            self.cloudproxy_url, json=cloudproxy_request
        )

        status_code = cloudproxy_response.status_code

        if status_code >= 500:
            raise ValueError(
                "CloudProxy request failed, got status code {}".format(status_code)
            )

        return cloudproxy_response
