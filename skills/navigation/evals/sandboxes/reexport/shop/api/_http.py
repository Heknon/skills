import urllib.request

DEFAULT_TIMEOUT = 10


class HttpClient:
    def __init__(self, base_url, timeout=DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout

    def get(self, path):
        with urllib.request.urlopen(self.base_url + path, timeout=self.timeout) as response:
            return response.read()
