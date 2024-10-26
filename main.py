import requests
import os
import logging
import json

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("SectorAlarmAPI")

API_URL = "https://mypagesapi.sectoralarm.net"
AUTH_TOKEN = None

class SectorAlarmAPI:
    def __init__(self, email, password, panel_id):
        self.email = email
        self.password = password
        self.panel_id = panel_id
        self.session = requests.Session()
        self.data = {}  # To store all endpoint results

    def login(self):
        """Authenticate and retrieve the authorization token."""
        global AUTH_TOKEN
        headers = {
            "Content-Type": "application/json",
            "API-Version": "5"
        }
        data = {
            "UserId": self.email,
            "Password": self.password
        }

        response = self.session.post(f"{API_URL}/api/Login/Login", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            AUTH_TOKEN = response.json().get("AuthorizationToken")
            logger.info("Login successful.")
        else:
            logger.error(f"Login failed with status code {response.status_code}.")
            logger.error(response.text)

    def try_panel_endpoints(self):
        """Attempt various /api/panel endpoints to find valid data."""
        potential_panel_endpoints = [
            "GetTemperatures", "GetPanelStatus", "GetSmartplugStatus", "GetLockStatus", "GetLogs"
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
            "API-Version": "5"
        }

        for endpoint in potential_panel_endpoints:
            url = f"{API_URL}/api/panel/{endpoint}?panelId={self.panel_id}"
            response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                self.data[endpoint] = response.json()
            else:
                logger.error(f"Failed to retrieve data from {endpoint}. Status code: {response.status_code}")

    def try_housecheck_endpoints(self):
        """Attempt various /api/housecheck and /api/v2/housecheck endpoints to find valid data."""
        endpoints = {
            "Humidity": ("GET", f"{API_URL}/api/housecheck/panels/{self.panel_id}/humidity"),
            "Doors and Windows": ("POST", f"{API_URL}/api/v2/housecheck/doorsandwindows"),
            "Leakage Detectors": ("POST", f"{API_URL}/api/v2/housecheck/leakagedetectors"),
            "Smoke Detectors": ("POST", f"{API_URL}/api/v2/housecheck/smokedetectors")
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
            "API-Version": "5"
        }
        payload = {"panelId": self.panel_id}  # For POST requests

        for name, (method, url) in endpoints.items():
            if method == "POST":
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
            else:
                response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                self.data[name] = response.json()
            else:
                logger.error(f"Failed to retrieve data from {name}. Status code: {response.status_code}")

    def get_consolidated_data(self):
        """Return all gathered data as JSON."""
        return json.dumps(self.data, indent=4)

def main():
    email = os.getenv("SA_EMAIL")
    password = os.getenv("SA_PASSWORD")
    panel_id = os.getenv("SA_PANELID")

    api = SectorAlarmAPI(email, password, panel_id)
    api.login()
    api.try_panel_endpoints()
    api.try_housecheck_endpoints()

    # Output consolidated data in JSON format
    print(api.get_consolidated_data())

if __name__ == "__main__":
    main()
