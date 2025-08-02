#!/usr/bin/env python3
"""
Aircraft Data Reader Module
Core functionality for reading aircraft data from dump1090-fa
"""

import json
import os
from typing import Dict, Optional
from config import get_config


def read_aircraft_data(file_path: Optional[str] = None) -> Optional[Dict]:
    """
    Read aircraft data from the dump1090-fa JSON file

    Args:
        file_path (str, optional): Path to the aircraft.json file.
                                 If None, uses path from configuration.

    Returns:
        dict: Aircraft data or None if file cannot be read
    """
    # Use config file path if none provided
    if file_path is None:
        config = get_config()
        file_path = config.get_data_source_path()

    try:
        if not os.path.exists(file_path):
            print(f"Error: Aircraft data file not found at {file_path}")
            print("Make sure dump1090-fa is running and the file path is correct.")
            print("You can change the file path in the 'config' file")
            return None

        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {file_path}: {e}")
        return None
    except PermissionError:
        print(f"Error: Permission denied reading {file_path}")
        print("You may need to run this script with appropriate permissions.")
        return None
    except Exception as e:
        print(f"Error reading aircraft data: {e}")
        return None
