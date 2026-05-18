import os
import requests
from requests.auth import HTTPBasicAuth


class OracleAPClient:
    def __init__(self):
        self.base_url = os.environ["ORACLE_BASE_URL"].rstrip("/")
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(
            os.environ["ORACLE_USERNAME"],
            os.environ["ORACLE_PASSWORD"],
        )
        self.session.headers.update({"Accept": "application/json"})

    def get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
