# sectoralarm/client.py

import requests
import logging
from .endpoints import get_data_endpoints, API_URL
from .exceptions import AuthenticationError
from .cache import CacheManager
from .actions import ActionsManager

logger = logging.getLogger("SectorAlarmAPI")
logger.setLevel(logging.INFO)  # Adjust logging level as needed


class SectorAlarmAPI:
    def __init__(self, email, password, panel_id, panel_code):
        self.email = email
        self.password = password
        self.panel_id = panel_id
        self.panel_code = panel_code
        self.session = requests.Session()
        self.auth_token = None
        self.cache_manager = CacheManager(self)
        self.actions_manager = ActionsManager(self)

    def login(self):
        """Authenticate and retrieve the authorization token."""
        headers = {
            "Content-Type": "application/json",
            "API-Version": "5"
        }
        data = {
            "UserId": self.email,
            "Password": self.password
        }

        response = self.session.post(
            f"{API_URL}/api/Login/Login", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            self.auth_token = response.json().get("AuthorizationToken")
            logger.info("Login successful.")
        else:
            logger.error(f"Login failed with status code {response.status_code}.")
            logger.error(response.text)
            raise AuthenticationError("Login failed. Please check your credentials.")

    def retrieve_category_data(self, category):
        """Retrieve data for a specific category from the API."""
        endpoints = get_data_endpoints(self.panel_id)

        method_url = endpoints.get(category)
        if method_url is None:
            logger.error(f"Unknown category {category}")
            return None
        method, url = method_url

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "API-Version": "5"
        }
        payload = {"panelId": self.panel_id}

        if method == "POST":
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
        else:
            response = self.session.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to retrieve data from {category}. Status code: {response.status_code}")
            return None
