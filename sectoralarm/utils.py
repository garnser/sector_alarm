# sectoralarm/utils.py

def extract_structure(data, key_path=[]):
    """Recursively extract the structure of the data, replacing values with None, but keeping identifiers.
    For the 'Logs' category, we return the data as is to preserve all log entries and their fields.
    """
    if isinstance(data, dict):
        key_path_lower = [k.lower() for k in key_path]
        if 'logs' in key_path_lower or (not key_path and any(k.lower() == 'logs' for k in data)):
            # If we're at the 'Logs' category, return the data as is
            return data
        new_dict = {}
        for key, value in data.items():
            new_key_path = key_path + [key]
            key_lower = key.lower()
            if key_lower in ['components', 'places', 'sections']:
                new_dict[key] = extract_structure(value, new_key_path)
            elif key_lower in ['name', 'label', 'id', 'key']:
                new_dict[key] = value  # Keep these identifiers
            else:
                new_dict[key] = None  # Replace other values with None
        return new_dict
    elif isinstance(data, list):
        return [extract_structure(item, key_path) for item in data]
    else:
        return None
