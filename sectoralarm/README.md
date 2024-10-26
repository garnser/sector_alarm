# SectorAlarm Library

A Python client library for interacting with Sector Alarm systems.

## Overview

The `sectoralarm` library allows developers to interact with Sector Alarm systems programmatically. It provides methods to authenticate, retrieve system status, control locks, arm/disarm the alarm system, and access sensor data.

## Features

- **Authentication**: Securely log in to the Sector Alarm API.
- **System Status**: Retrieve panel status and sensor data.
- **Control Actions**: Arm/disarm the alarm system and lock/unlock doors.
- **Logs Access**: Access system logs and events.
- **Cache Management**: Efficiently cache data to minimize API calls.

## Installation

You can install the library via pip:

```bash
pip install sectoralarm
```

## Usage
### Importing the Library

```python
from sectoralarm import SectorAlarmAPI, AuthenticationError
```

### Initializing the API Client

```python
# Replace with your actual credentials
email = "your_email@example.com"
password = "your_password"
panel_id = "your_panel_id"
panel_code = "your_panel_code"

api = SectorAlarmAPI(email, password, panel_id, panel_code)
```

### Logging In

```python
try:
    api.login()
    print("Logged in successfully.")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### Retrieving Panel Status
```python
status = api.retrieve_category_data("Panel Status")
print("Panel Status:")
print(status)
```

### Arming the System
```python
success = api.actions_manager.arm_system()
if success:
    print("System armed successfully.")
else:
    print("Failed to arm the system.")
```
    
### Disarming the System
```python
success = api.actions_manager.disarm_system()
if success:
    print("System disarmed successfully.")
else:
    print("Failed to disarm the system.")
```    

### Locking a Door
```python
lock_serial = "your_lock_serial_number"
success = api.actions_manager.lock_door(lock_serial)
if success:
    print("Door locked successfully.")
else:
    print("Failed to lock the door.")
```
    
### Unlocking a Door
```python
lock_serial = "your_lock_serial_number"
success = api.actions_manager.unlock_door(lock_serial)
if success:
    print("Door unlocked successfully.")
else:
    print("Failed to unlock the door.")
```    

## API Reference
Please refer to the code documentation and docstrings within the library for more detailed information on available methods and their usage.

## Dependencies
`requests`: Used for making HTTP requests to the Sector Alarm API.
License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
This library is not affiliated with or endorsed by Sector Alarm. Use it responsibly and at your own risk.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue on GitHub.

## Contact
For questions or suggestions, please contact Jonathan Petersson <jpetersson@garnser.se>.
