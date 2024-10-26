# SectorAlarm Client Application

An interactive command-line application for interacting with Sector Alarm systems using the `sectoralarm` library.

## Overview

This client application allows users to interact with their Sector Alarm systems via a command-line interface. It provides functionalities to:

- Navigate and view system categories and data
- Arm and disarm the security system
- Lock and unlock doors
- Rebuild the local cache
- Fetch and display data from the system

## Features

- **Interactive Menu**: Navigate through system categories and data interactively.
- **Control Actions**: Arm/disarm the system and lock/unlock doors directly from the CLI.
- **Data Fetching**: Fetch and display data for specific categories or the entire system.
- **Cache Management**: Rebuild and view statistics of the local data cache.

## Prerequisites

- **Python 3.6** or higher
- **sectoralarm** library installed
- **Internet Connection**: Required to communicate with the Sector Alarm API

## Installation

### Clone the Repository

```bash
git clone https://github.com/garnser/sector_alarm.git
cd sector_alarm
```

### Install Dependencies
It's recommended to use a virtual environment.

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install sectoralarm
```

## Configuration
Create a config.json file in the root directory with your Sector Alarm credentials and panel information.

`config.json`

```json
{
  "email": "your_email@example.com",
  "password": "your_password",
  "panel_id": "your_panel_id",
  "panel_code": "your_panel_code"
}
```

**Note**: Keep this file secure and do not share it, as it contains sensitive information.

## Usage
Run the client application:

```bash
python main.py
```

### Main Menu Options
1. **Select a category**: Navigate and view different data categories from your system.
2. **Rebuild cache**: Refresh the local cache of system data structures.
3. **Show cache statistics**: Display statistics about the cached data.
4. **Lock/Unlock Doors**: Control door locks.
5. **Arm/Disarm System**: Control the alarm system status.
F. **Fetch all data**: Retrieve and display all data from all categories.
0. **Exit**: Exit the application.

### Navigating Categories
- Select a category to view its sections and items.
- At each level, you can:
  - Select a section or item by number to navigate further.
  - Press F to fetch and display data for the current level.
  - Press 0 to go back to the previous menu.

### Example Session
```mathematica
Main Menu:
1. Select a category
2. Rebuild cache
3. Show cache statistics
4. Lock/Unlock Doors
5. Arm/Disarm System
F. Fetch all data
0. Exit
Select an option: 1

Categories:
1. Doors and Windows
2. Temperatures
3. Panel Status
0. Back
Select a category (by number): 1

Doors and Windows > Sections:
1. Front Door
2. Back Door
0. Back
F. Fetch data for this level
Select a section (by number) or F to fetch data: F

Fetching data...
{
  "Front Door": "Closed",
  "Back Door": "Open"
}
Press Enter to continue...
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
This client application is not affiliated with or endorsed by Sector Alarm. Use it responsibly and at your own risk.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue on GitHub.

## Contact
For questions or suggestions, please contact Jonathan Petersson <jpetersson@garnser.se>.
