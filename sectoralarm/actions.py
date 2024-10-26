# sectoralarm/actions.py

import logging
from .endpoints import get_action_endpoints, API_URL

logger = logging.getLogger("SectorAlarmAPI")


class ActionsManager:
    def __init__(self, api):
        self.api = api  # Reference to the SectorAlarmAPI instance

    def lock_door(self, lock_serial):
        """Lock the specified door."""
        endpoints = get_action_endpoints()
        endpoint = endpoints["Lock"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api.auth_token,
            "API-Version": "5"
        }
        payload = {
            "LockSerial": lock_serial,
            "PanelCode": "",
            "PanelId": self.api.panel_id,
            "Platform": "web"
        }

        response = self.api.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("Door locked successfully.")
            return True
        else:
            logger.error(f"Failed to lock door. Status code: {response.status_code}")
            logger.error(response.text)
            return False

    def unlock_door(self, lock_serial):
        """Unlock the specified door."""
        endpoints = get_action_endpoints()
        endpoint = endpoints["Unlock"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api.auth_token,
            "API-Version": "5"
        }
        payload = {
            "LockSerial": lock_serial,
            "PanelCode": self.api.panel_code,
            "PanelId": self.api.panel_id,
            "Platform": "web"
        }

        response = self.api.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("Door unlocked successfully.")
            return True
        else:
            logger.error(f"Failed to unlock door. Status code: {response.status_code}")
            logger.error(response.text)
            return False

    def arm_system(self):
        """Arm the security system."""
        endpoints = get_action_endpoints()
        endpoint = endpoints["Arm"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api.auth_token,
            "API-Version": "5"
        }
        payload = {"PanelId": self.api.panel_id}

        response = self.api.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("System armed successfully.")
            return True
        else:
            logger.error(f"Failed to arm system. Status code: {response.status_code}")
            logger.error(response.text)
            return False

    def disarm_system(self):
        """Disarm the security system."""
        endpoints = get_action_endpoints()
        endpoint = endpoints["Disarm"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api.auth_token,
            "API-Version": "5"
        }
        payload = {
            "PanelCode": self.api.panel_code,
            "PanelId": self.api.panel_id
        }

        response = self.api.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("System disarmed successfully.")
            return True
        else:
            logger.error(f"Failed to disarm system. Status code: {response.status_code}")
            logger.error(response.text)
            return False

    def get_system_status(self):
        """Get the current status of the security system."""
        url = f"{API_URL}/api/Panel/GetPanelStatus?panelId={self.api.panel_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api.auth_token,
            "API-Version": "5"
        }

        response = self.api.session.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to retrieve system status. Status code: {response.status_code}")
            return None
