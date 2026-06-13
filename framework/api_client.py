import requests

class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10 ):
        self.base_url = base_url.rstrip("/")  # Remove trailing slashes so f"{base_url}{path}" does not create double slashes.
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get(self, path: str, **kwargs):
        # **kwargs collects extra named request options, such as params, cookies, auth, verify,
        # or allow_redirects, and forwards them to requests.Session.get without listing each one here.
        return self.session.get(
            f"{self.base_url}{path}",
            timeout=self.timeout_seconds,
            **kwargs,
        )
    def post(self, path: str, json=None, headers=None, **kwargs):
        # **kwargs keeps this wrapper flexible by passing through any additional requests options
        # that are not explicit parameters, such as params, cookies, auth, verify, or allow_redirects.
        return self.session.post(
            f"{self.base_url}{path}",
            json=json,
            headers=headers,
            timeout=self.timeout_seconds,
            **kwargs,
        )
