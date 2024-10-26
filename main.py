from sectoralarm import SectorAlarmAPI
import json
import os
import sys

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
    interactive_mode(api)

def interactive_mode(api):
    while True:
        print("\nMain Menu:")
        print("1. Select a category")
        print("2. Rebuild cache")
        print("3. Show cache statistics")
        print("4. Lock/Unlock Doors")
        print("F. Fetch all data")
        print("0. Exit")
        choice = input("Select an option: ")
        if choice == "1":
            select_category(api)
        elif choice == "2":
            api.rebuild_cache()
        elif choice == "3":
            cache_statistics(api)
        elif choice == "4":
            lock_unlock_doors(api)
        elif choice.upper() == "F":
            fetch_all_data(api)
        elif choice == "0":
            break
        else:
            print("Invalid choice.")

def select_category(api):
    print("\nCategories:")
    categories = list(api.cache.keys())
    for idx, cat in enumerate(categories):
        print(f"{idx + 1}. {cat}")
    print("0. Back")
    try:
        choice = int(input("Select a category (by number): "))
        if choice == 0:
            pass
        elif 1 <= choice <= len(categories):
            category = categories[choice - 1]
            navigate_structure(api, api.cache[category], [{'key': category, 'display': category}], key_path=[])
        else:
            print("Invalid choice.")
    except ValueError:
        print("Invalid input. Please enter a number.")

def navigate_structure(api, structure, path, key_path):
    if isinstance(structure, dict):
        # Directly navigate into 'Places', 'Components', 'Sections' if they exist
        for key in ['Places', 'Components', 'Sections']:
            if key in structure:
                display_name = key
                new_path = path + [{'key': key, 'display': display_name}]
                new_key_path = key_path + [key]
                navigate_structure(api, structure[key], new_path, new_key_path)
                return
        # If all values are None or not dict/list, fetch and display data
        if all(not isinstance(value, (dict, list)) for value in structure.values()):
            data = fetch_data_at_path(api, path)
            print(f"\n{get_display_path(path)}")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            input("Press Enter to continue...")
            return
        else:
            # Else, show sections
            keys = list(structure.keys())
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
                        sub_structure = structure[key]
                        navigate_structure(api, sub_structure, new_path, new_key_path)
                        return
                    else:
                        print("Invalid choice.")
                else:
                    print("Invalid input.")
    elif isinstance(structure, list):
        if not structure:
            print(f"\n{get_display_path(path)}")
            print("This list is empty.")
            input("Press Enter to go back.")
            return
        # If there's only one item, automatically navigate into it
        if len(structure) == 1:
            item = structure[0]
            identifier = get_identifier(item)
            new_path = path + [{'key': '0', 'display': identifier}]
            navigate_structure(api, item, new_path, key_path)
            return
        else:
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
                    data = fetch_data_at_path(api, path)
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                    input("Press Enter to continue...")
                    return  # Return after fetching data
                elif choice.isdigit():
                    idx_choice = int(choice)
                    if 1 <= idx_choice <= len(structure):
                        item = structure[idx_choice - 1]
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
        for key in ['Name', 'Label', 'Id', 'Key']:
            if key in item and item[key]:
                return f"{item.get(key)}"
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
    for category in api.cache.keys():
        data = api.retrieve_category_data(category)
        if data is not None:
            all_data[category] = data
    print(json.dumps(all_data, indent=4, ensure_ascii=False))
    input("Press Enter to continue...")

def cache_statistics(api):
    """Display statistics of the cache."""
    num_categories = len(api.cache)
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

    for category in api.cache.values():
        traverse(category)

    print("\nCache Statistics:")
    print(f"Total Categories: {num_categories}")
    print(f"Total Sections: {num_sections}")
    print(f"Total Items: {num_items}")
    input("Press Enter to continue...")

def lock_unlock_doors(api):
    """Allow user to lock or unlock doors."""
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
                success = api.lock_door(lock_serial)
                if success:
                    print("Door locked successfully.")
                else:
                    print("Failed to lock the door.")
            elif action == "U":
                success = api.unlock_door(lock_serial)
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

if __name__ == "__main__":
    main()
