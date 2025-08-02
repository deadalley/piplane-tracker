#!/usr/bin/env python3
"""
Aircraft Data Reader Module
Core functionality for reading aircraft data from dump1090-fa
"""

import json
import os
from typing import Dict, Optional

def read_aircraft_data(file_path="/var/run/dump1090-fa/aircraft.json") -> Optional[Dict]:
    """
    Read aircraft data from the dump1090-fa JSON file
    
    Args:
        file_path (str): Path to the aircraft.json file
        
    Returns:
        dict: Aircraft data or None if file cannot be read
    """
    try:
        if not os.path.exists(file_path):
            print(f"Error: Aircraft data file not found at {file_path}")
            print("Make sure dump1090-fa is running and the file path is correct.")
            return None
            
        with open(file_path, 'r') as file:
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

def get_country_from_icao(hex_code: str) -> str:
    """
    Get country from ICAO hex code (basic implementation)
    This is a simplified version - for full accuracy, use a proper ICAO database
    
    Args:
        hex_code (str): ICAO hex identifier
        
    Returns:
        str: Country name or "Unknown"
    """
    if not hex_code or len(hex_code) < 6:
        return "Unknown"
    
    # Basic country code mapping based on ICAO allocation
    # This is simplified - real implementation would need full ICAO database
    first_char = hex_code[0].upper()
    
    country_mappings = {
        'A': 'United States',
        '0': 'United States', '1': 'United States', '2': 'United States', 
        '3': 'United States', '4': 'United States', '5': 'United States',
        '6': 'United States', '7': 'United States',
        'C': 'Canada',
        '4B': 'Mexico', '4C': 'Mexico',
        '40': 'United Kingdom', '41': 'United Kingdom', '42': 'United Kingdom', 
        '43': 'United Kingdom',
        '44': 'Austria', '45': 'Belgium', '46': 'Bulgaria', '47': 'Denmark',
        '48': 'Finland', '49': 'France', '4A': 'Germany',
        '50': 'Netherlands', '51': 'Norway', '52': 'Poland', '53': 'Portugal',
        '54': 'Czech Republic', '55': 'Sweden', '56': 'Switzerland', '57': 'Turkey',
        '58': 'Yugoslavia', '59': 'Romania', '5A': 'Libya', '5B': 'Cyprus',
        '78': 'China', '79': 'South Korea', '7A': 'North Korea', '7B': 'Japan',
        '7C': 'Australia', '7D': 'New Zealand',
        '88': 'India', '89': 'Iran', '8A': 'Afghanistan', '8B': 'Indonesia',
        '8C': 'Thailand', '8D': 'Philippines', '8E': 'Malaysia', '8F': 'Singapore',
        'E': 'Brazil', 'F': 'Argentina'
    }
    
    # Check for two-character prefixes first
    prefix_2 = hex_code[:2].upper()
    if prefix_2 in country_mappings:
        return country_mappings[prefix_2]
    
    # Check single character
    if first_char in country_mappings:
        return country_mappings[first_char]
    
    return "Unknown"
