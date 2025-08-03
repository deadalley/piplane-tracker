#!/usr/bin/env python3
"""
HexDB.io API Integration
Simple aircraft information lookup using HexDB.io API
"""

import requests
from typing import Dict, Optional
import time


def get_aircraft_info(icao_hex: str) -> Optional[Dict]:
    """
    Get aircraft information from HexDB.io API

    Args:
        icao_hex (str): ICAO24 hex code (e.g., "4010ee")

    Returns:
        Optional[Dict]: Aircraft information or None if not found
    """
    try:
        url = f"https://hexdb.io/api/v1/aircraft/{icao_hex.lower()}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Check if response contains an error
            if "status" in data and data["status"] == "404":
                return None
            return data
        elif response.status_code == 404:
            return None
        else:
            print(f"HexDB API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error fetching HexDB data for {icao_hex}: {e}")
        return None


def enhance_aircraft_data(aircraft: Dict) -> Dict:
    """
    Enhance aircraft data with HexDB.io information

    Args:
        aircraft (Dict): Basic aircraft data from dump1090

    Returns:
        Dict: Enhanced aircraft data
    """
    hex_code = aircraft.get("hex")
    if not hex_code:
        return aircraft

    # Get enhanced info from HexDB
    hexdb_info = get_aircraft_info(hex_code)
    if not hexdb_info:
        return aircraft

    # Add enhanced fields to aircraft data
    enhanced = aircraft.copy()

    if hexdb_info.get("Type"):
        enhanced["aircraft_type"] = hexdb_info["Type"]

    if hexdb_info.get("Manufacturer"):
        enhanced["manufacturer"] = hexdb_info["Manufacturer"]

    if hexdb_info.get("Registration"):
        enhanced["registration"] = hexdb_info["Registration"]

    if hexdb_info.get("RegisteredOwners"):
        enhanced["operator"] = hexdb_info["RegisteredOwners"]

    return enhanced
