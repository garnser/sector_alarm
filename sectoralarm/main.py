# main.py

import sys
import getopt
import json
import os
from sectoralarm.client import SectorAlarmAPI, AuthenticationError

# Load CATEGORY_NAVIGATION from category_navigation.json
CONFIG_FILE = 'config/category_navigation.json'  # Adjust the path if necessary

try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as config_file:
        CATEGORY_NAVIGATION = json.load(config_file)
except FileNotFoundError:
    print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error parsing '{CONFIG_FILE}': {e}")
    sys.exit(1)


def main():
    """
    The main entry point of the SectorAlarm client script.
    Parses command-line arguments, initializes the API client,
    and starts either direct data fetching or interactive mode.
    """
    # Parse command-line options
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "he:p:i:c:md:", ["help", "email=", "password=", "panel_id=", "panel_code=", "mask", "data="]
        )
    except getopt.GetoptError as err:
        # Print help information and exit
        print(f"Error: {err}")
        usage()
        sys.exit(2)

    # Initialize default values
    config_overrides = {}
    mask_sensitive = False
    direct_data_oids = []

    # Process command-line options
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-e", "--email"):
            config_overrides['email'] = a
        elif o in ("-p", "--password"):
            config_overrides['password'] = a
        elif o in ("-i", "--panel_id"):
            config_overrides['panel_id'] = a
        elif o in ("-c", "--panel_code"):
            config_overrides['panel_code'] = a
        elif o in ("-m", "--mask"):
            mask_sensitive = True
        elif o in ("-d", "--data"):
            # Assume that 'a' is a comma-separated list of OIDs
            direct_data_oids = a.split(',')
        else:
            assert False, "Unhandled option"

    # Load configuration from file
    try:
        with open('config/config.json', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        config = {}

    # Override config with command-line options
    email = config_overrides.get('email', config.get('email'))
    password = config_overrides.get('password', config.get('password'))
    panel_id = config_overrides.get('panel_id', config.get('panel_id'))
    panel_code = config_overrides.get('panel_code', config.get('panel_code'))

    # Check that required parameters are provided
    if not email or not password or not panel_id:
        print("Error: Missing required configuration parameters (email, password, panel_id).")
        usage()
        sys.exit(2)

    # Initialize the API client
    api = SectorAlarmAPI(email, password, panel_id, panel_code)
    try:
        api.login()
    except AuthenticationError as e:
        print(f"Authentication Error: {e}")
        sys.exit(1)

    # Load cache
    api.cache_manager.load_cache()

    # Set mask_sensitive flag
    api.mask_sensitive = mask_sensitive or config.get('mask_sensitive', False)

    # If direct_data_oids are provided, fetch data for those OIDs
    if direct_data_oids:
        fetch_direct_data(api, direct_data_oids)
    else:
        # Start interactive session
        interactive_mode(api)


def usage():
    """
    Displays the usage instructions for the script.
    """
    print("""
Usage:
  sectoralarm [options]

Options:
  -h, --help                Show this help message and exit
  -e EMAIL, --email=EMAIL   Email address used for authentication
  -p PWD, --password=PWD    Password used for authentication
  -i ID, --panel_id=ID      Panel ID of your Sector Alarm system
  -c CODE, --panel_code=CODE Panel code (if required)
  -m, --mask                Mask sensitive data in output (SerialNo, Id, etc.)
  -d OIDs, --data=OIDs      Comma-separated list of OIDs to fetch data for directly

Examples:
  sectoralarm -e user@example.com -p password -i 123456
  sectoralarm -m -d 1.2,3.4.5

Description:
  This script allows you to interact with your Sector Alarm system.
  You can use command-line options to provide configuration parameters,
  enable data masking, and fetch data directly using OIDs.

  If no options are provided, the script will attempt to read configuration
  from 'config.json' and start in interactive mode.
""")


def mask_sensitive_data(data):
    """
    Recursively mask sensitive data in the given data structure.
    Sensitive keys include 'serialno', 'id', 'deviceid', 'serialstring'.

    :param data: The data structure (dict or list) to mask.
    :return: The masked data structure.
    """
    sensitive_keys = {'serialno', 'id', 'deviceid', 'serialstring'}
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                masked_data[key] = '***MASKED***'
            else:
                masked_data[key] = mask_sensitive_data(value)
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data


def get_navigable_items(current_structure, category, level):
    """
    Identify and return navigable items within the current structure based on the category and level.
    Navigable items are those that are dictionaries or lists,
    following the navigation rules defined in CATEGORY_NAVIGATION.

    :param current_structure: The current data structure (dict or list).
    :param category: The current category being navigated.
    :param level: The current depth level in the navigation hierarchy.
    :return: List of tuples containing (identifier, data).
    """
    navigable_items = []

    if isinstance(current_structure, dict):
        # Determine navigable keys based on the level
        navigable_keys = []
        if level == 0:
            # Top-level navigable keys (e.g., "Sections" for Humidity)
            navigable_keys = CATEGORY_NAVIGATION.get(category, {}).get("navigable_keys", [])
        elif level == 1:
            # Sub-level navigable keys (e.g., "Places" within "Sections")
            navigable_keys = CATEGORY_NAVIGATION.get(category, {}).get("sub_navigable_keys", [])
        elif level == 2:
            # Further sub-level navigable keys (e.g., "Components" within "Places")
            navigable_keys = CATEGORY_NAVIGATION.get(category, {}).get("sub_sub_navigable_keys", [])

        # Traverse navigable keys
        for key, value in current_structure.items():
            if key in navigable_keys and isinstance(value, (dict, list)):
                if isinstance(value, list):
                    # Iterate over each item in the list
                    for item in value:
                        if isinstance(item, dict):
                            identifier = get_identifier(item)
                            navigable_items.append((identifier, item))
                elif isinstance(value, dict):
                    identifier = get_identifier(value)
                    navigable_items.append((identifier, value))

    elif isinstance(current_structure, list):
        # For lists, each dict item is navigable
        for item in current_structure:
            if isinstance(item, dict):
                identifier = get_identifier(item)
                navigable_items.append((identifier, item))

    return navigable_items


def contains_navigable(value):
    """
    Check if the given value contains further navigable items.
    A navigable item is a dict or list that contains at least one dict or list.

    :param value: The value to check (dict or list).
    :return: True if navigable, False otherwise.
    """
    if isinstance(value, dict):
        return any(isinstance(v, (dict, list)) for v in value.values())
    elif isinstance(value, list):
        return any(isinstance(item, (dict, list)) for item in value)
    else:
        return False


def fetch_direct_data(api, direct_data_oids):
    """
    Fetch and output data for the specified OIDs.

    :param api: Instance of SectorAlarmAPI.
    :param direct_data_oids: List of OIDs to fetch data for directly.
    """
    for oid in direct_data_oids:
        data = fetch_data_by_oid(api, oid)
        if data is not None:
            if api.mask_sensitive:
                data = mask_sensitive_data(data)
            print(f"Data for OID '{oid}':")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            print("-" * 40)
        else:
            print(f"OID '{oid}' not found.")
            print("-" * 40)


def fetch_data_by_oid(api, oid):
    """
    Fetch data from the API based on the OID.

    :param api: Instance of SectorAlarmAPI.
    :param oid: The OID string (e.g., '1.2.3').
    :return: The data retrieved from the API or None if not found.
    """
    path_indices = oid.strip().split('.')
    if not path_indices:
        return None

    categories = list(api.cache_manager.cache.keys())
    try:
        # Convert the first segment to index (1-based)
        category_index = int(path_indices[0]) - 1
        if category_index < 0 or category_index >= len(categories):
            return None
        category = categories[category_index]
        data = api.retrieve_category_data(category)
        sub_data = data

        level = 0  # Initial navigation level

        # Traverse the rest of the path using navigable items
        for idx_str in path_indices[1:]:
            if isinstance(sub_data, dict):
                navigable_items = get_navigable_items(sub_data, category, level)
                if not navigable_items:
                    return None
                idx = int(idx_str) - 1
                if idx < 0 or idx >= len(navigable_items):
                    return None
                _, sub_data = navigable_items[idx]
                level += 1
            elif isinstance(sub_data, list):
                idx = int(idx_str) - 1
                if idx < 0 or idx >= len(sub_data):
                    return None
                sub_data = sub_data[idx]
                level += 1
            else:
                return None  # Cannot traverse further

        # Return the final sub_data, whether it's a leaf node or not
        return sub_data

    except (ValueError, IndexError):
        return None


def interactive_mode(api):
    """
    Starts the interactive navigation mode, presenting the main menu
    and handling user selections.

    :param api: Instance of SectorAlarmAPI.
    """
    while True:
        print("\nMain Menu:")
        print("1. Select a category")
        print("2. Rebuild cache")
        print("3. Show cache statistics")
        print("4. Lock/Unlock Doors")
        print("5. Arm/Disarm System")
        print("F. Fetch all data")
        print("0. Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            select_category(api)
        elif choice == "2":
            api.cache_manager.rebuild_cache()
            print("Cache rebuilt successfully.")
        elif choice == "3":
            cache_statistics(api)
        elif choice == "4":
            lock_unlock_doors(api)
        elif choice == "5":
            arm_disarm_system(api)
        elif choice.upper() == "F":
            fetch_all_data(api)
        elif choice == "0":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please select a valid option.")


def select_category(api):
    """
    Displays the list of categories and handles user selection.

    :param api: Instance of SectorAlarmAPI.
    """
    print("\nCategories:")
    categories = list(api.cache_manager.cache.keys())
    for idx, cat in enumerate(categories, start=1):
        oid = str(idx)
        print(f"{idx}. {cat} [{oid}]")
    print("0. Back")
    try:
        choice = input("Select a category (by number): ").strip()
        if choice == "0":
            return
        choice_num = int(choice)
        if 1 <= choice_num <= len(categories):
            category = categories[choice_num - 1]
            # Retrieve data for the selected category
            data = api.retrieve_category_data(category)
            if data is None:
                print(f"Failed to retrieve data for category '{category}'.")
                input("Press Enter to continue...")
                return
            oid_path = [str(choice_num)]
            path = [{'key': category, 'display': category}]
            level = 0  # Initial navigation level
            navigate_structure(
                api,
                data,
                path,
                key_path=[],
                oid_path=oid_path,
                category=category,
                level=level
            )
        else:
            print("Invalid choice. Please select a valid number.")
    except ValueError:
        print("Invalid input. Please enter a number.")


def navigate_structure(api, current_structure, path, key_path, oid_path, category, level):
    """
    Recursively navigate through the data structure based on user input.

    :param api: Instance of SectorAlarmAPI.
    :param current_structure: The current level of the data structure being navigated.
    :param path: List representing the navigation path for display purposes.
    :param key_path: List representing the keys traversed for data retrieval.
    :param oid_path: List representing the OID segments for data retrieval.
    :param category: The current category being navigated.
    :param level: The current depth level in the navigation hierarchy.
    """
    # Identify navigable items using the helper function with category and level
    navigable_items = get_navigable_items(current_structure, category, level)

    # Check if the current structure is a leaf node
    if not navigable_items:
        # Leaf node detected; display data directly
        if api.mask_sensitive:
            current_structure = mask_sensitive_data(current_structure)
        print(f"\n{get_display_path(path)}")
        print(json.dumps(current_structure, indent=4, ensure_ascii=False))
        input("Press Enter to go back...")
        return  # Return to the previous menu level

    if navigable_items:
        while True:
            print(f"\n{get_display_path(path)}")
            print("Items:")
            for idx, (key, _) in enumerate(navigable_items, start=1):
                oid = '.'.join(oid_path + [str(idx)])
                print(f"{idx}. {key} [{oid}]")
            print("0. Back")
            print("F. Fetch data for this level")

            choice = input("Select an item (by number) or F to fetch data: ").strip()
            if choice == "0":
                return  # Go back to the previous menu level
            elif choice.upper() == "F":
                data = fetch_data_at_path(api, path, category)
                if data is not None:
                    if api.mask_sensitive:
                        data = mask_sensitive_data(data)
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                else:
                    print("Failed to fetch data for this level.")
                input("Press Enter to continue...")
            elif choice.isdigit():
                idx_choice = int(choice)
                if 1 <= idx_choice <= len(navigable_items):
                    selected_item = navigable_items[idx_choice - 1][1]
                    identifier = navigable_items[idx_choice - 1][0]
                    new_path = path + [{'key': identifier, 'display': identifier}]
                    new_oid_path = oid_path + [str(idx_choice)]
                    new_level = level + 1

                    navigate_structure(
                        api,
                        selected_item,
                        new_path,
                        key_path + [identifier],
                        new_oid_path,
                        category,
                        new_level
                    )
                else:
                    print("Invalid choice. Please select a valid number.")
            else:
                print("Invalid input. Please enter a number or 'F'.")


def get_identifier(item):
    """
    Get a meaningful identifier for list items.
    Prioritize certain keys for identification.

    :param item: The item from the list.
    :return: A string identifier for the item.
    """
    if isinstance(item, dict):
        for key in ['Name', 'Label', 'Id', 'Key']:
            if key in item and item[key]:
                return str(item[key])
        return "Item"  # Fallback identifier
    else:
        return str(item)


def get_display_path(path):
    """
    Construct the display path from the path list.

    :param path: List of dictionaries representing the navigation path.
    :return: A string representing the navigation path.
    """
    return ' > '.join([p['display'] for p in path])


def fetch_data_at_path(api, path, category):
    """
    Fetch data from the API based on the current navigation path.

    :param api: Instance of SectorAlarmAPI.
    :param path: List representing the navigation path.
    :param category: The current category being navigated.
    :return: The data retrieved from the API or None if not found.
    """
    data = api.retrieve_category_data(category)
    if data is None:
        return None

    sub_data = data
    level = 0  # Initial navigation level
    for p in path[1:]:
        key = p['key']
        if isinstance(sub_data, dict):
            navigable_items = get_navigable_items(sub_data, category, level)
            if not navigable_items:
                return None
            # Find the item with the matching identifier
            matched = False
            for item in navigable_items:
                if item[0] == key:
                    sub_data = item[1]
                    matched = True
                    break
            if not matched:
                return None
            level += 1
        elif isinstance(sub_data, list):
            try:
                index = int(key) - 1
                sub_data = sub_data[index]
                level += 1
            except (ValueError, IndexError):
                return None
        else:
            return None  # Cannot traverse further
    return sub_data


def fetch_all_data(api):
    """
    Fetch all data from all categories and display it.

    :param api: Instance of SectorAlarmAPI.
    """
    all_data = {}
    for category in api.cache_manager.cache.keys():
        data = api.retrieve_category_data(category)
        if data is not None:
            if api.mask_sensitive:
                data = mask_sensitive_data(data)
            all_data[category] = data
    print(json.dumps(all_data, indent=4, ensure_ascii=False))
    input("Press Enter to continue...")


def cache_statistics(api):
    """
    Display statistics of the cache, including the number of categories,
    sections, and items.

    :param api: Instance of SectorAlarmAPI.
    """
    num_categories = len(api.cache_manager.cache)
    num_sections = 0
    num_items = 0

    def traverse(node):
        """
        Recursively traverse the data structure to count sections and items.

        :param node: The current node in the data structure.
        """
        nonlocal num_sections, num_items
        if isinstance(node, dict):
            num_sections += len(node)
            for value in node.values():
                traverse(value)
        elif isinstance(node, list):
            num_items += len(node)
            for item in node:
                traverse(item)

    for category in api.cache_manager.cache.values():
        traverse(category)

    print("\nCache Statistics:")
    print(f"Total Categories: {num_categories}")
    print(f"Total Sections: {num_sections}")
    print(f"Total Items: {num_items}")
    input("Press Enter to continue...")


def lock_unlock_doors(api):
    """
    Allow the user to lock or unlock doors based on the available locks.

    :param api: Instance of SectorAlarmAPI.
    """
    # Retrieve lock status to get the list of locks
    locks_data = api.retrieve_category_data("Lock Status")
    if locks_data is None or not locks_data:
        print("No locks found.")
        input("Press Enter to return to the main menu.")
        return

    locks = locks_data  # Assuming locks_data is a list of locks
    # Display the list of locks
    print("\nAvailable Locks:")
    for idx, lock in enumerate(locks, start=1):
        lock_name = lock.get("Label", f"Lock {idx}")
        status = lock.get("Status", "Unknown")
        print(f"{idx}. {lock_name} (Status: {status})")
    print("0. Back")
    try:
        choice = input("Select a lock to control (by number): ").strip()
        if choice == "0":
            return
        choice_num = int(choice)
        if 1 <= choice_num <= len(locks):
            selected_lock = locks[choice_num - 1]
            lock_serial = selected_lock.get("Serial")
            lock_label = selected_lock.get("Label", "Unknown")
            # Ask for action
            action = input(f"Do you want to (L)ock or (U)nlock '{lock_label}'? ").strip().upper()
            if action == "L":
                success = api.actions_manager.lock_door(lock_serial)
                if success:
                    print("Door locked successfully.")
                else:
                    print("Failed to lock the door.")
            elif action == "U":
                success = api.actions_manager.unlock_door(lock_serial)
                if success:
                    print("Door unlocked successfully.")
                else:
                    print("Failed to unlock the door.")
            else:
                print("Invalid action. Please enter 'L' to Lock or 'U' to Unlock.")
        else:
            print("Invalid choice. Please select a valid number.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    input("Press Enter to continue...")


def arm_disarm_system(api):
    """
    Allow the user to arm or disarm the security system or check its status.

    :param api: Instance of SectorAlarmAPI.
    """
    while True:
        print("\nArm/Disarm Menu:")
        print("1. Arm System")
        print("2. Disarm System")
        print("3. Get System Status")
        print("0. Back")
        choice = input("Select an option: ").strip()
        if choice == "1":
            success = api.actions_manager.arm_system()
            if success:
                print("System armed successfully.")
            else:
                print("Failed to arm the system.")
            input("Press Enter to continue...")
        elif choice == "2":
            success = api.actions_manager.disarm_system()
            if success:
                print("System disarmed successfully.")
            else:
                print("Failed to disarm the system.")
            input("Press Enter to continue...")
        elif choice == "3":
            status = api.actions_manager.get_system_status()
            if status:
                if api.mask_sensitive:
                    status = mask_sensitive_data(status)
                print("System Status:")
                print(json.dumps(status, indent=4, ensure_ascii=False))
            else:
                print("Failed to retrieve system status.")
            input("Press Enter to continue...")
        elif choice == "0":
            break
        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
