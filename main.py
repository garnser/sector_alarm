# main.py

import sys
import getopt
import json
from datetime import datetime
from sectoralarm import SectorAlarmAPI, AuthenticationError

def main():
    # Parse command-line options
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "he:p:i:c:md:", ["help", "email=", "password=", "panel_id=", "panel_code=", "mask", "data="])
    except getopt.GetoptError as err:
        # Print help information and exit
        print(err)
        usage()
        sys.exit(2)

    # Default values
    config_overrides = {}
    mask_sensitive = False
    direct_data_ids = []

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
            # Assume that 'a' is a comma-separated list of IDs
            direct_data_ids = a.split(',')
        else:
            assert False, "Unhandled option"

    # Load configuration from file
    try:
        with open('config.json', 'r', encoding='utf-8') as config_file:
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
        print("Missing required configuration parameters.")
        usage()
        sys.exit(2)

    # Initialize the API client
    api = SectorAlarmAPI(email, password, panel_id, panel_code)
    try:
        api.login()
    except AuthenticationError as e:
        print(e)
        return

    # Load cache
    api.cache_manager.load_cache()

    # Set mask_sensitive flag
    api.mask_sensitive = mask_sensitive

    # If direct_data_ids are provided, fetch data for those IDs
    if direct_data_ids:
        fetch_direct_data(api, direct_data_ids)
    else:
        # Start interactive session
        interactive_mode(api)

def usage():
    print("Usage:")
    print("  main.py [options]")
    print("Options:")
    print("  -h, --help            Show this help message and exit")
    print("  -e, --email=EMAIL     Email address")
    print("  -p, --password=PWD    Password")
    print("  -i, --panel_id=ID     Panel ID")
    print("  -c, --panel_code=CODE Panel Code")
    print("  -m, --mask            Mask sensitive data in output")
    print("  -d, --data=IDS        Comma-separated list of component IDs to fetch data for")

def mask_sensitive_data(data):
    """Recursively mask sensitive data in the given data structure."""
    sensitive_keys = {'SerialNo', 'Id', 'DeviceId', 'SerialString'}
    if isinstance(data, dict):
        masked_data = {}
        for key, value in data.items():
            if key in sensitive_keys:
                masked_data[key] = '***MASKED***'
            else:
                masked_data[key] = mask_sensitive_data(value)
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data

def fetch_direct_data(api, direct_data_ids):
    """Fetch and output data for the specified component IDs."""
    all_data = {}
    for category in api.cache_manager.cache.keys():
        data = api.retrieve_category_data(category)
        if data is not None:
            all_data[category] = data

    found_items = []
    for data_id in direct_data_ids:
        found = False
        for category, data in all_data.items():
            items = find_items_by_id(data, data_id)
            if items:
                for item in items:
                    found_items.append((category, item))
                found = True
        if not found:
            print(f"ID '{data_id}' not found.")

    for category, item in found_items:
        print(f"Data for ID '{item.get('Id', 'Unknown')}' in category '{category}':")
        if api.mask_sensitive:
            item = mask_sensitive_data(item)
        print(json.dumps(item, indent=4, ensure_ascii=False))
        print("-" * 40)

def find_items_by_id(data, data_id):
    """Recursively search for items with matching 'Id' in data."""
    found_items = []
    if isinstance(data, dict):
        if str(data.get('Id', '')).lower() == data_id.lower():
            found_items.append(data)
        else:
            for value in data.values():
                found_items.extend(find_items_by_id(value, data_id))
    elif isinstance(data, list):
        for item in data:
            found_items.extend(find_items_by_id(item, data_id))
    return found_items

def interactive_mode(api):
    while True:
        print("\nMain Menu:")
        print("1. Select a category")
        print("2. Rebuild cache")
        print("3. Show cache statistics")
        print("4. Lock/Unlock Doors")
        print("5. Arm/Disarm System")
        print("F. Fetch all data")
        print("0. Exit")
        choice = input("Select an option: ")
        if choice == "1":
            select_category(api)
        elif choice == "2":
            api.cache_manager.rebuild_cache()
        elif choice == "3":
            cache_statistics(api)
        elif choice == "4":
            lock_unlock_doors(api)
        elif choice == "5":
            arm_disarm_system(api)
        elif choice.upper() == "F":
            fetch_all_data(api)
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def select_category(api):
    print("\nCategories:")
    categories = list(api.cache_manager.cache.keys())
    for idx, cat in enumerate(categories):
        print(f"{idx + 1}. {cat}")
    print("0. Back")
    try:
        choice = int(input("Select a category (by number): "))
        if choice == 0:
            pass
        elif 1 <= choice <= len(categories):
            category = categories[choice - 1]
            navigate_structure(api, category, [{'key': category, 'display': category}], key_path=[])
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a number.")

def navigate_structure(api, current_structure, path, key_path):
    if isinstance(current_structure, str):
        # At the top level, current_structure is the category name
        category = current_structure
        if category.lower() == 'logs':
            # Fetch the actual logs data from the API
            data = api.retrieve_category_data(category)
            if data is None:
                print("Failed to retrieve logs.")
                input("Press Enter to continue...")
                return
            # Assuming the logs data is a list
            structure = data
            if not isinstance(structure, list):
                print("Unexpected data format for logs.")
                input("Press Enter to continue...")
                return
            # Sort the logs by Time
            structure = sorted(structure, key=lambda x: x.get('Time', ''), reverse=True)
            # Now display the logs
            while True:
                print(f"\n{get_display_path(path)}")
                print("Items:")
                for idx, item in enumerate(structure):
                    identifier = get_identifier(item)
                    print(f"{idx + 1}. {identifier}")
                print("0. Back")
                print("F. Fetch data for this level")
                choice = input("Select an item (by number) or F to fetch data: ")
                if choice == "0":
                    break
                elif choice.upper() == "F":
                    # Fetch and display data for this level
                    data = api.retrieve_category_data(category)
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                    input("Press Enter to continue...")
                elif choice.isdigit():
                    idx_choice = int(choice)
                    if 1 <= idx_choice <= len(structure):
                        item = structure[idx_choice - 1]
                        identifier = get_identifier(item)
                        new_path = path + [{'key': str(idx_choice - 1), 'display': identifier}]
                        # Display the log entry
                        print(f"\n{get_display_path(new_path)}")
                        print(json.dumps(item, indent=4, ensure_ascii=False))
                        input("Press Enter to continue...")
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input.")
        else:
            # For other categories, proceed as before
            structure = api.cache_manager.cache.get(category)
            if structure is None:
                print(f"No data available for category '{category}'.")
                return
            navigate_structure(api, structure, path, key_path)
    elif isinstance(current_structure, dict):
        # Directly navigate into 'Places', 'Components', 'Sections' if they exist
        for key in current_structure.keys():
            if key.lower() in ['places', 'components', 'sections']:
                display_name = key
                new_path = path + [{'key': key, 'display': display_name}]
                new_key_path = key_path + [key]
                navigate_structure(api, current_structure[key], new_path, new_key_path)
                return
        # If all values are None or not dict/list, fetch and display data
        if all(not isinstance(value, (dict, list)) for value in current_structure.values()):
            data = fetch_data_at_path(api, path)
            print(f"\n{get_display_path(path)}")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            input("Press Enter to continue...")
            return
        else:
            # Else, show sections
            keys = list(current_structure.keys())
            while True:
                print(f"\n{get_display_path(path)}")
                print("Sections:")
                for idx, key in enumerate(keys):
                    print(f"{idx + 1}. {key}")
                print("0. Back")
                print("F. Fetch data for this level")
                choice = input("Select a section (by number) or F to fetch data: ")
                if choice == "0":
                    break
                elif choice.upper() == "F":
                    data = fetch_data_at_path(api, path)
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                    input("Press Enter to continue...")
                    return  # Return after fetching data
                elif choice.isdigit():
                    idx_choice = int(choice)
                    if 1 <= idx_choice <= len(keys):
                        key = keys[idx_choice - 1]
                        display_name = key
                        new_path = path + [{'key': key, 'display': display_name}]
                        new_key_path = key_path + [key]
                        sub_structure = current_structure[key]
                        navigate_structure(api, sub_structure, new_path, new_key_path)
                        return
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input.")
    elif isinstance(current_structure, list):
        if not current_structure:
            print(f"\n{get_display_path(path)}")
            print("This list is empty.")
            input("Press Enter to go back.")
            return
        # If there's only one item, automatically navigate into it
        if len(current_structure) == 1:
            item = current_structure[0]
            identifier = get_identifier(item)
            new_path = path + [{'key': '0', 'display': identifier}]
            navigate_structure(api, item, new_path, key_path)
            return
        else:
            # Display the list items
            while True:
                print(f"\n{get_display_path(path)}")
                print("Items:")
                for idx, item in enumerate(current_structure):
                    identifier = get_identifier(item)
                    print(f"{idx + 1}. {identifier}")
                print("0. Back")
                print("F. Fetch data for this level")
                choice = input("Select an item (by number) or F to fetch data: ")
                if choice == "0":
                    break
                elif choice.upper() == "F":
                    data = fetch_data_at_path(api, path)
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                    input("Press Enter to continue...")
                    return
                elif choice.isdigit():
                    idx_choice = int(choice)
                    if 1 <= idx_choice <= len(current_structure):
                        item = current_structure[idx_choice - 1]
                        identifier = get_identifier(item)
                        new_path = path + [{'key': str(idx_choice - 1), 'display': identifier}]
                        navigate_structure(api, item, new_path, key_path)
                        return
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input.")
    else:
        # Leaf node, fetch data automatically
        data = fetch_data_at_path(api, path)
        print(f"\n{get_display_path(path)}")
        print(json.dumps(data, indent=4, ensure_ascii=False))
        input("Press Enter to continue...")

def get_identifier(item):
    """Get a meaningful identifier for list items."""
    if isinstance(item, dict):
        if 'Time' in item and item['Time']:
            value = item['Time']
            # Format the time
            try:
                dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return value  # Return unformatted if parsing fails
        # Fallback to other identifiers
        for key in ['Name', 'Label', 'Id', 'Key']:
            if key in item and item[key]:
                return str(item[key])
        return "Item"
    else:
        return str(item)

def get_display_path(path):
    """Construct the display path from the path list."""
    return ' > '.join([p['display'] for p in path])

def fetch_data_at_path(api, path):
    category = path[0]['key']
    # Retrieve data from the API for the selected category
    data = api.retrieve_category_data(category)
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

def fetch_all_data(api):
    """Fetch all data from all categories."""
    all_data = {}
    for category in api.cache_manager.cache.keys():
        data = api.retrieve_category_data(category)
        if data is not None:
            all_data[category] = data
    print(json.dumps(all_data, indent=4, ensure_ascii=False))
    input("Press Enter to continue...")

def cache_statistics(api):
    """Display statistics of the cache."""
    num_categories = len(api.cache_manager.cache)
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

    for category in api.cache_manager.cache.values():
        traverse(category)

    print("\nCache Statistics:")
    print(f"Total Categories: {num_categories}")
    print(f"Total Sections: {num_sections}")
    print(f"Total Items: {num_items}")
    input("Press Enter to continue...")

def lock_unlock_doors(api):
    """Allow user to lock or unlock doors."""
    # Use api.actions_manager for action methods
    # Retrieve lock status to get the list of locks
    locks_data = api.retrieve_category_data("Lock Status")
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
                print("Invalid action.")
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a number.")
    input("Press Enter to continue...")

def arm_disarm_system(api):
    """Allow user to arm or disarm the security system."""
    while True:
        print("\nArm/Disarm Menu:")
        print("1. Arm System")
        print("2. Disarm System")
        print("3. Get System Status")
        print("0. Back")
        choice = input("Select an option: ")
        if choice == "1":
            success = api.actions_manager.arm_system()
            if success:
                print("System armed successfully.")
            else:
                print("Failed to arm the system.")
        elif choice == "2":
            success = api.actions_manager.disarm_system()
            if success:
                print("System disarmed successfully.")
            else:
                print("Failed to disarm the system.")
        elif choice == "3":
            status = api.actions_manager.get_system_status()
            if status:
                print("System Status:")
                print(json.dumps(status, indent=4, ensure_ascii=False))
            else:
                print("Failed to retrieve system status.")
        elif choice == "0":
            break
        else:
            print("Invalid choice.")
        input("Press Enter to continue...")

if __name__ == "__main__":
    main()
