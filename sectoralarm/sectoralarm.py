import requests
import logging
import json
import sys
import os

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("SectorAlarmAPI")

API_URL = "https://mypagesapi.sectoralarm.net"

class SectorAlarmAPI:
    def __init__(self, email, password, panel_id, panel_code):
        self.email = email
        self.password = password
        self.panel_id = panel_id
        self.panel_code = panel_code
        self.session = requests.Session()
        self.auth_token = None  # Moved AUTH_TOKEN to an instance variable
        self.cache = {}  # To store the structure of categories, sections, and modules

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

        response = self.session.post(f"{API_URL}/api/Login/Login", headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            self.auth_token = response.json().get("AuthorizationToken")
            logger.info("Login successful.")
        else:
            logger.error(f"Login failed with status code {response.status_code}.")
            logger.error(response.text)
            sys.exit("Login failed. Please check your credentials.")

    def extract_structure(self, data, key_path=[]):
        """Recursively extract the structure of the data, replacing values with None, but keeping identifiers."""
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key_path = key_path + [key]
                if 'Components' in key_path:
                    # Inside 'Components', keep identifiers
                    if key in ['Name', 'Label', 'Id', 'Key']:
                        new_dict[key] = value
                    else:
                        new_dict[key] = None
                elif key in ['Name', 'Label', 'Id', 'Key']:
                    new_dict[key] = value  # Keep the value
                elif key in ['Components', 'Places', 'Sections']:
                    new_dict[key] = self.extract_structure(value, new_key_path)
                else:
                    new_dict[key] = None  # Replace other values with None
            return new_dict
        elif isinstance(data, list):
            return [self.extract_structure(item, key_path) for item in data]
        else:
            return None

    def build_cache(self):
        """Build the cache of categories, sections, and modules."""
        endpoints = self.get_all_endpoints()

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "API-Version": "5"
        }
        payload = {"panelId": self.panel_id}  # For POST requests

        for name, (method, url) in endpoints.items():
            if method == "POST":
                response = self.session.post(url, headers=headers, json=payload, timeout=30)
            else:
                response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                # Extract the structure
                structure = self.extract_structure(data)
                self.cache[name] = structure
            else:
                logger.error(f"Failed to retrieve data from {name}. Status code: {response.status_code}")

    def save_cache(self, filename='cache.json'):
        with open(filename, 'w', encoding='utf-8') as cache_file:
            json.dump(self.cache, cache_file, indent=4, ensure_ascii=False)

    def load_cache(self, filename='cache.json'):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as cache_file:
                self.cache = json.load(cache_file)
            logger.info(f"Cache loaded from {filename}")
        else:
            logger.info("Cache file not found. Building cache...")
            self.build_cache()
            self.save_cache(filename)

    def rebuild_cache(self, filename='cache.json'):
        logger.info("Rebuilding cache...")
        self.build_cache()
        self.save_cache(filename)

    def retrieve_category_data(self, category):
        """Retrieve data for a specific category from the API."""
        endpoints = self.get_all_endpoints()

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

    def get_all_endpoints(self):
        """Return a dictionary of all endpoints."""
        endpoints = {
            # Housecheck endpoints
            "Humidity": ("GET", f"{API_URL}/api/housecheck/panels/{self.panel_id}/humidity"),
            "Doors and Windows": ("POST", f"{API_URL}/api/v2/housecheck/doorsandwindows"),
            "Leakage Detectors": ("POST", f"{API_URL}/api/v2/housecheck/leakagedetectors"),
            "Smoke Detectors": ("POST", f"{API_URL}/api/v2/housecheck/smokedetectors"),
            "Cameras": ("GET", f"{API_URL}/api/v2/housecheck/cameras/{self.panel_id}"),
            "Persons": ("GET", f"{API_URL}/api/persons/panels/{self.panel_id}"),
            "Temperatures": ("POST", f"{API_URL}/api/v2/housecheck/temperatures"),
            # Panel endpoints
            "Panel Status": ("GET", f"{API_URL}/api/panel/GetPanelStatus?panelId={self.panel_id}"),
            "Smartplug Status": ("GET", f"{API_URL}/api/panel/GetSmartplugStatus?panelId={self.panel_id}"),
            "Lock Status": ("GET", f"{API_URL}/api/panel/GetLockStatus?panelId={self.panel_id}"),
            "Logs": ("GET", f"{API_URL}/api/panel/GetLogs?panelId={self.panel_id}"),
            # Lock/Unlock endpoints
            "Unlock": ("POST", f"{API_URL}/api/Panel/Unlock"),
            "Lock": ("POST", f"{API_URL}/api/Panel/Lock"),
        }
        return endpoints

    def lock_door(self, lock_serial):
        """Lock the specified door."""
        endpoint = self.get_all_endpoints()["Lock"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "API-Version": "5"
        }
        payload = {
            "LockSerial": lock_serial,
            "PanelCode": "",
            "PanelId": self.panel_id,
            "Platform": "web"
        }

        response = self.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("Door locked successfully.")
            return True
        else:
            logger.error(f"Failed to lock door. Status code: {response.status_code}")
            logger.error(response.text)
            return False

    def unlock_door(self, lock_serial):
        """Unlock the specified door."""
        endpoint = self.get_all_endpoints()["Unlock"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "API-Version": "5"
        }
        payload = {
            "LockSerial": lock_serial,
            "PanelCode": self.panel_code,
            "PanelId": self.panel_id,
            "Platform": "web"
        }

        response = self.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("Door unlocked successfully.")
            return True
        else:
            logger.error(f"Failed to unlock door. Status code: {response.status_code}")
            logger.error(response.text)
            return False
