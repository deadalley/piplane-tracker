#!/usr/bin/env python3
# pyright: reportPossiblyUnboundVariable=false, reportMissingImports=false
"""
Aircraft Display Module
Handles formatting and displaying aircraft information
"""

from datetime import datetime
from typing import Dict, List, Optional
from get_country_from_icao import get_country_from_icao
from formatters import (
    format_coordinate,
    format_altitude,
    format_speed,
    format_heading,
    format_squawk,
    format_vertical_rate,
    format_signal_strength,
    format_last_seen,
    format_messages,
)

# Optional: Import flight enhancer for additional data
try:
    from flight_enhancer import enhance_aircraft_list

    ENHANCER_AVAILABLE = True
except ImportError:
    ENHANCER_AVAILABLE = False

# Optional: Import OpenSky API for enhanced data
try:
    from opensky_api import get_enhanced_aircraft_info

    OPENSKY_AVAILABLE = True
except ImportError:
    OPENSKY_AVAILABLE = False


def filter_aircraft_by_callsign(aircraft_list: List[Dict]) -> List[Dict]:
    """
    Filter aircraft list to only include those with callsigns

    Args:
        aircraft_list (List[Dict]): List of aircraft data

    Returns:
        List[Dict]: Filtered aircraft list
    """
    filtered_aircraft = []
    for aircraft in aircraft_list:
        flight = aircraft.get("flight", "").strip()
        if flight:  # Only include aircraft with a valid flight/callsign
            filtered_aircraft.append(aircraft)
    return filtered_aircraft


def display_aircraft_header(
    aircraft_count: int, filtered_count: int = 0, filtered: bool = False
):
    """Display header information"""
    print(f"\n{'='*80}")
    print(f"Aircraft Data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total aircraft detected: {aircraft_count}")
    if filtered and filtered_count is not 0:
        print(f"Aircraft with flight/callsign: {filtered_count}")
    print(f"{'='*80}")


def display_single_aircraft(
    aircraft: Dict, index: int, use_api: bool = False, rate_limit: float = 1.0
):
    """
    Display information for a single aircraft

    Args:
        aircraft (Dict): Aircraft data
        index (int): Aircraft number for display
        use_api (bool): Whether to fetch enhanced data from API
        rate_limit (float): Rate limit for API requests
    """
    # Flight/callsign
    flight = aircraft.get("flight", "").strip()
    hex_code = aircraft.get("hex", "Unknown")

    # Header with flight name or ICAO
    if flight:
        print(f"\n--- Aircraft {index}: {flight} ---")
    else:
        print(f"\n--- Aircraft {index}: ICAO {hex_code} ---")

    # Basic identification
    if flight:
        print(f"Flight/Callsign: {flight}")
    else:
        print("Flight/Callsign: N/A")

    # ICAO identifier and country
    country = get_country_from_icao(hex_code)
    print(f"ICAO ID (Hex): {hex_code}")
    print(f"Country: {country}")

    # Enhanced flight information (if available)
    display_enhanced_info(aircraft, use_api, rate_limit)

    # Position and movement data
    display_position_data(aircraft)

    # Technical data
    display_technical_data(aircraft)


def display_enhanced_info(
    aircraft: Dict, use_api: bool = True, rate_limit: float = 1.0
):
    """
    Display enhanced flight information using OpenSky Network API

    Args:
        aircraft (Dict): Aircraft data
        use_api (bool): Whether to fetch additional data from OpenSky API
        rate_limit (float): Rate limit for API requests
    """
    if not use_api or not OPENSKY_AVAILABLE:
        return

    hex_code = aircraft.get("hex")
    if not hex_code:
        return

    # Try to get enhanced info from OpenSky Network
    enhanced_data = get_enhanced_aircraft_info(hex_code, rate_limit)

    if enhanced_data:
        print("\n--- Enhanced Flight Information ---")

        # Enhanced callsign (might be more complete than local data)
        if (
            enhanced_data.get("callsign")
            and enhanced_data["callsign"] != aircraft.get("flight", "").strip()
        ):
            print(f"Enhanced Callsign: {enhanced_data['callsign']}")

        # Origin country from OpenSky
        if enhanced_data.get("origin_country"):
            print(f"Origin Country: {enhanced_data['origin_country']}")

        # Ground status
        if enhanced_data.get("status"):
            print(f"Status: {enhanced_data['status']}")

        # Last contact time
        if enhanced_data.get("last_contact"):
            print(f"Last Contact: {enhanced_data['last_contact']}")

        # Position source
        if enhanced_data.get("position_source"):
            print(f"Position Source: {enhanced_data['position_source']}")

        print("--- End Enhanced Information ---")
    else:
        print("\n--- No enhanced information available ---")


def display_position_data(aircraft: Dict):
    """Display position and movement data"""
    # Position
    lat = aircraft.get("lat")
    lon = aircraft.get("lon")
    print(f"Position: {format_coordinate(lat)}, {format_coordinate(lon)}")

    # Altitude
    altitude = aircraft.get("alt_baro") or aircraft.get("alt_geom")
    print(f"Altitude: {format_altitude(altitude)}")

    # Speed and heading
    ground_speed = aircraft.get("gs")
    print(f"Ground Speed: {format_speed(ground_speed)}")

    track = aircraft.get("track")
    print(f"Track/Heading: {format_heading(track)}")

    # Vertical rate
    vert_rate = aircraft.get("baro_rate") or aircraft.get("geom_rate")
    print(f"Vertical Rate: {format_vertical_rate(vert_rate)}")


def display_technical_data(aircraft: Dict):
    """Display technical aircraft data"""
    # Squawk code
    squawk = aircraft.get("squawk")
    print(f"Squawk: {format_squawk(squawk)}")

    # Signal strength
    rssi = aircraft.get("rssi")
    if rssi is not None:
        print(f"Signal Strength: {format_signal_strength(rssi)}")

    # Last seen and message count
    seen = aircraft.get("seen")
    if seen is not None:
        print(f"Last seen: {format_last_seen(seen)}")

    messages = aircraft.get("messages")
    if messages is not None:
        print(f"Messages received: {format_messages(messages)}")


def display_aircraft_info(
    aircraft_data: Dict,
    config=None,
    filter_by_callsign: bool = False,
    enhance_data: bool = False,
    use_api: bool = False,
):
    """
    Display formatted aircraft information

    Args:
        aircraft_data (Dict): Aircraft data from dump1090-fa
        config: Configuration object (optional)
        filter_by_callsign (bool): Whether to filter out aircraft without flight/callsign
        enhance_data (bool): Whether to enhance data with flight_enhancer module
        use_api (bool): Whether to enhance data with OpenSky Network API (overrides config if specified)
    """
    if not aircraft_data or "aircraft" not in aircraft_data:
        print("No aircraft data available.")
        return

    aircraft_list = aircraft_data["aircraft"]

    if not aircraft_list:
        print("No aircraft currently detected.")
        return

    # Determine API usage from config if not explicitly specified
    if use_api is None and config:
        use_api = config.get_bool("opensky_enabled", False)
    elif use_api is None:
        use_api = False

    # Get rate limit from config
    rate_limit = 1.0
    if config:
        rate_limit = config.get_float("opensky_rate_limit", 1.0)

    # Enhance data if requested and available
    if enhance_data and ENHANCER_AVAILABLE:
        print("Enhancing aircraft data with additional information...")
        aircraft_list = enhance_aircraft_list(aircraft_list)
    elif enhance_data and not ENHANCER_AVAILABLE:
        print(
            "Warning: Flight enhancer not available. Install requests module for enhanced data."
        )

    # Filter aircraft if requested
    if filter_by_callsign:
        aircraft_to_display = filter_aircraft_by_callsign(aircraft_list)

        if not aircraft_to_display:
            print("No aircraft with flight/callsign currently detected.")
            return
    else:
        aircraft_to_display = aircraft_list

    # Display header
    display_aircraft_header(
        aircraft_count=len(aircraft_list),
        filtered_count=len(aircraft_to_display) if filter_by_callsign else 0,
        filtered=filter_by_callsign,
    )

    # Display each aircraft
    for i, aircraft in enumerate(aircraft_to_display, 1):
        display_single_aircraft(aircraft, i, use_api, rate_limit)
