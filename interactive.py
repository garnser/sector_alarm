import requests
import os
import logging
import json
import sys

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("SectorAlarmAPI")

API_URL = "https://mypagesapi.sectoralarm.net"
AUTH_TOKEN = None

class SectorAlarmAPI:
    def __init__(self, email, password, panel_id, panel_code):
        self.email = email
        self.password = password
        self.panel_id = panel_id
        self.panel_code = panel_code
        self.session = requests.Session()
        self.data = {}   # To store all endpoint results
        self.cache = {}  # To store the structure of categories, sections, and modules

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
                data = response.json()
                # Extract the structure
                structure = self.extract_structure(data)
                self.cache[name] = structure
            else:
                logger.error(f"Failed to retrieve data from {name}. Status code: {response.status_code}")

    def save_cache(self):
        with open('cache.json', 'w', encoding='utf-8') as cache_file:
            json.dump(self.cache, cache_file, indent=4, ensure_ascii=False)

    def load_cache(self):
        if os.path.exists('cache.json'):
            with open('cache.json', 'r', encoding='utf-8') as cache_file:
                self.cache = json.load(cache_file)
            logger.info("Cache loaded from cache.json")
        else:
            logger.info("Cache file not found. Building cache...")
            self.build_cache()
            self.save_cache()

    def rebuild_cache(self):
        logger.info("Rebuilding cache...")
        self.build_cache()
        self.save_cache()

    def cache_statistics(self):
        """Display statistics of the cache."""
        num_categories = len(self.cache)
        num_sections = 0
        num_items = 0

        def traverse(node):
            nonlocal num_sections, num_items
            if isinstance(node, dict):
                num_sections += len(node)
                for value in node.values():
                    traverse(value)
            elif isinstance(node, list):
                num_items += len(node)
                for item in node:
                    traverse(item)

        for category in self.cache.values():
            traverse(category)

        print("\nCache Statistics:")
        print(f"Total Categories: {num_categories}")
        print(f"Total Sections: {num_sections}")
        print(f"Total Items: {num_items}")
        input("Press Enter to continue...")

    def interactive_mode(self):
        while True:
            print("\nMain Menu:")
            print("1. Select a category")
            print("2. Rebuild cache")
            print("3. Show cache statistics")
            print("4. Lock/Unlock Doors")
            print("5. Arm/Disarm Alarm")
            print("F. Fetch all data")
            print("0. Exit")
            choice = input("Select an option: ")
            if choice == "1":
                self.select_category()
            elif choice == "2":
                self.rebuild_cache()
            elif choice == "3":
                self.cache_statistics()
            elif choice == "4":
                self.lock_unlock_doors()
            elif choice == "5":
                self.arm_disarm_alarm()
            elif choice.upper() == "F":
                self.fetch_all_data()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def select_category(self):
        print("\nCategories:")
        categories = list(self.cache.keys())
        for idx, cat in enumerate(categories):
            print(f"{idx + 1}. {cat}")
        print("0. Back")
        try:
            choice = int(input("Select a category (by number): "))
            if choice == 0:
                pass
            elif 1 <= choice <= len(categories):
                category = categories[choice -1]
                self.navigate_structure(self.cache[category], [{'key': category, 'display': category}], key_path=[])
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def navigate_structure(self, structure, path, key_path):
        if isinstance(structure, dict):
            # Directly navigate into 'Places', 'Components', 'Sections' if they exist
            for key in ['Places', 'Components', 'Sections']:
                if key in structure:
                    display_name = key
                    new_path = path + [{'key': key, 'display': display_name}]
                    new_key_path = key_path + [key]
                    self.navigate_structure(structure[key], new_path, new_key_path)
                    return
            # If all values are None or not dict/list, fetch and display data
            if all(not isinstance(value, (dict, list)) for value in structure.values()):
                data = self.fetch_data_at_path(path)
                print(f"\n{self.get_display_path(path)}")
                print(json.dumps(data, indent=4, ensure_ascii=False))
                input("Press Enter to continue...")
                return
            else:
                # Else, show sections
                keys = list(structure.keys())
                while True:
                    print(f"\n{self.get_display_path(path)}")
                    print("Sections:")
                    for idx, key in enumerate(keys):
                        print(f"{idx + 1}. {key}")
                    print("0. Back")
                    print("F. Fetch data for this level")
                    choice = input("Select a section (by number) or F to fetch data: ")
                    if choice == "0":
                        break
                    elif choice.upper() == "F":
                        data = self.fetch_data_at_path(path)
                        print(json.dumps(data, indent=4, ensure_ascii=False))
                        input("Press Enter to continue...")
                        return  # Return after fetching data
                    elif choice.isdigit():
                        idx_choice = int(choice)
                        if 1 <= idx_choice <= len(keys):
                            key = keys[idx_choice -1]
                            display_name = key
                            new_path = path + [{'key': key, 'display': display_name}]
                            new_key_path = key_path + [key]
                            sub_structure = structure[key]
                            self.navigate_structure(sub_structure, new_path, new_key_path)
                            return
                        else:
                            print("Invalid choice.")
                    else:
                        print("Invalid input.")
        elif isinstance(structure, list):
            if not structure:
                print(f"\n{self.get_display_path(path)}")
                print("This list is empty.")
                input("Press Enter to go back.")
                return
            # If there's only one item, automatically navigate into it
            if len(structure) == 1:
                item = structure[0]
                identifier = self.get_identifier(item)
                new_path = path + [{'key': '0', 'display': identifier}]
                self.navigate_structure(item, new_path, key_path)
                return
            else:
                while True:
                    print(f"\n{self.get_display_path(path)}")
                    print("Items:")
                    for idx, item in enumerate(structure):
                        identifier = self.get_identifier(item)
                        print(f"{idx + 1}. {identifier}")
                    print("0. Back")
                    print("F. Fetch data for this level")
                    choice = input("Select an item (by number) or F to fetch data: ")
                    if choice == "0":
                        break
                    elif choice.upper() == "F":
                        data = self.fetch_data_at_path(path)
                        print(json.dumps(data, indent=4, ensure_ascii=False))
                        input("Press Enter to continue...")
                        return  # Return after fetching data
                    elif choice.isdigit():
                        idx_choice = int(choice)
                        if 1 <= idx_choice <= len(structure):
                            item = structure[idx_choice -1]
                            identifier = self.get_identifier(item)
                            new_path = path + [{'key': str(idx_choice - 1), 'display': identifier}]
                            self.navigate_structure(item, new_path, key_path)
                            return
                        else:
                            print("Invalid choice.")
                    else:
                        print("Invalid input.")
        else:
            # Leaf node, fetch data automatically
            data = self.fetch_data_at_path(path)
            print(f"\n{self.get_display_path(path)}")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            input("Press Enter to continue...")

    def get_identifier(self, item):
        """Get a meaningful identifier for list items."""
        if isinstance(item, dict):
            for key in ['Name', 'Label', 'Id', 'Key']:
                if key in item and item[key]:
                    return f"{item.get(key)}"
            return "Item"
        else:
            return str(item)

    def get_display_path(self, path):
        """Construct the display path from the path list."""
        return ' > '.join([p['display'] for p in path])

    def fetch_data_at_path(self, path):
        category = path[0]['key']
        # Retrieve data from the API for the selected category
        data = self.retrieve_category_data(category)
        if data is None:
            return None
        # Now navigate through the data according to the path
        sub_data = data
        for p in path[1:]:
            key = p['key']
            if isinstance(sub_data, dict):
                sub_data = sub_data.get(key)
            elif isinstance(sub_data, list):
                try:
                    index = int(key)
                    sub_data = sub_data[index]
                except (ValueError, IndexError):
                    sub_data = None
                    break
            else:
                sub_data = None
                break
        return sub_data

    def fetch_all_data(self):
        """Fetch all data from all categories."""
        all_data = {}
        for category in self.cache.keys():
            data = self.retrieve_category_data(category)
            if data is not None:
                all_data[category] = data
        print(json.dumps(all_data, indent=4, ensure_ascii=False))
        input("Press Enter to continue...")

    def retrieve_category_data(self, category):
        # Map category to the endpoint
        endpoints = self.get_all_endpoints()

        method_url = endpoints.get(category)
        if method_url is None:
            logger.error(f"Unknown category {category}")
            return None
        method, url = method_url

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
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
            # Arm/Disarm endpoints
            "Arm": ("POST", f"{API_URL}/api/Panel/Arm"),
            "Disarm": ("POST", f"{API_URL}/api/Panel/Disarm"),
        }
        return endpoints

    def lock_unlock_doors(self):
        """Allow user to lock or unlock doors."""
        # Retrieve lock status to get the list of locks
        locks_data = self.retrieve_category_data("Lock Status")
        if locks_data is None or not locks_data:
            print("No locks found.")
            input("Press Enter to return to the main menu.")
            return

        locks = locks_data  # Assuming locks_data is a list of locks
        # Display the list of locks
        print("\nAvailable Locks:")
        for idx, lock in enumerate(locks):
            lock_name = lock.get("Label", f"Lock {idx + 1}")
            status = lock.get("Status")
            print(f"{idx + 1}. {lock_name} (Status: {status})")

        print("0. Back")
        try:
            choice = int(input("Select a lock to control (by number): "))
            if choice == 0:
                return
            elif 1 <= choice <= len(locks):
                selected_lock = locks[choice - 1]
                lock_serial = selected_lock.get("Serial")
                lock_label = selected_lock.get("Label", "Unknown")
                # Ask for action
                action = input(f"Do you want to (L)ock or (U)nlock '{lock_label}'? ").upper()
                if action == "L":
                    self.lock_door(lock_serial)
                elif action == "U":
                    self.unlock_door(lock_serial)
                else:
                    print("Invalid action.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def lock_door(self, lock_serial):
        """Lock the specified door."""
        endpoint = self.get_all_endpoints()["Lock"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
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
            print("Door locked successfully.")
        else:
            print(f"Failed to lock door. Status code: {response.status_code}")
            print(response.text)
        input("Press Enter to continue...")

    def unlock_door(self, lock_serial):
        """Unlock the specified door."""
        endpoint = self.get_all_endpoints()["Unlock"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
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
            print("Door unlocked successfully.")
        else:
            print(f"Failed to unlock door. Status code: {response.status_code}")
            print(response.text)
        input("Press Enter to continue...")

    def arm_disarm_alarm(self):
        """Allow user to arm or disarm the alarm."""
        # Ask the user whether to arm or disarm
        action = input("Do you want to (A)rm or (D)isarm the alarm? ").upper()
        if action == "A":
            self.arm_alarm()
        elif action == "D":
            self.disarm_alarm()
        else:
            print("Invalid action.")
            input("Press Enter to return to the main menu.")

    def arm_alarm(self):
        """Arm the alarm system."""
        endpoint = self.get_all_endpoints()["Arm"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
            "API-Version": "5"
        }
        payload = {
            "PanelId": self.panel_id
        }

        response = self.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print("Alarm armed successfully.")
        else:
            print(f"Failed to arm alarm. Status code: {response.status_code}")
            print(response.text)
        input("Press Enter to continue...")

    def disarm_alarm(self):
        """Disarm the alarm system."""
        endpoint = self.get_all_endpoints()["Disarm"]
        method, url = endpoint

        headers = {
            "Content-Type": "application/json",
            "Authorization": AUTH_TOKEN,
            "API-Version": "5"
        }
        payload = {
            "PanelCode": self.panel_code,
            "PanelId": self.panel_id
        }

        response = self.session.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print("Alarm disarmed successfully.")
        else:
            print(f"Failed to disarm alarm. Status code: {response.status_code}")
            print(response.text)
        input("Press Enter to continue...")

def main():
    # Load configuration
    try:
        with open('config.json', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
        email = config.get("email")
        password = config.get("password")
        panel_id = config.get("panel_id")
        panel_code = config.get("panel_code")
    except FileNotFoundError:
        print("Configuration file 'config.json' not found.")
        return

    api = SectorAlarmAPI(email, password, panel_id, panel_code)
    api.login()
    api.load_cache()
    # Start interactive session
    api.interactive_mode()

if __name__ == "__main__":
    main()
