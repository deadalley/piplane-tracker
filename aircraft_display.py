#!/usr/bin/env python3
"""
Aircraft Display Module
Handles formatting and displaying aircraft information
"""

from datetime import datetime
from typing import Dict, List
from aircraft_data import get_country_from_icao
from display_utils import (
    format_coordinate, format_altitude, format_speed, format_heading,
    format_squawk, format_vertical_rate, format_signal_strength,
    format_last_seen, format_messages
)

# Optional: Import flight enhancer for additional data
try:
    from flight_enhancer import enhance_aircraft_list
    ENHANCER_AVAILABLE = True
except ImportError:
    ENHANCER_AVAILABLE = False

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
        flight = aircraft.get('flight', '').strip()
        if flight:  # Only include aircraft with a valid flight/callsign
            filtered_aircraft.append(aircraft)
    return filtered_aircraft

def display_aircraft_header(aircraft_count: int, filtered_count: int = None, filtered: bool = False):
    """Display header information"""
    print(f"\n{'='*80}")
    print(f"Aircraft Data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total aircraft detected: {aircraft_count}")
    if filtered and filtered_count is not None:
        print(f"Aircraft with flight/callsign: {filtered_count}")
    print(f"{'='*80}")

def display_single_aircraft(aircraft: Dict, index: int):
    """
    Display information for a single aircraft
    
    Args:
        aircraft (Dict): Aircraft data
        index (int): Aircraft number for display
    """
    # Flight/callsign
    flight = aircraft.get('flight', '').strip()
    hex_code = aircraft.get('hex', 'Unknown')
    
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
    display_enhanced_info(aircraft)
    
    # Position and movement data
    display_position_data(aircraft)
    
    # Technical data
    display_technical_data(aircraft)

def display_enhanced_info(aircraft: Dict):
    """Display enhanced flight information if available"""
    # Origin and destination
    origin = aircraft.get('origin') or aircraft.get('departure')
    destination = aircraft.get('destination') or aircraft.get('arrival')
    aircraft_type = aircraft.get('type') or aircraft.get('aircraft_type')
    registration = aircraft.get('registration') or aircraft.get('reg')
    
    if origin:
        print(f"Origin: {origin}")
    
    if destination:
        print(f"Destination: {destination}")
    
    if aircraft_type:
        print(f"Aircraft Type: {aircraft_type}")
    
    if registration:
        print(f"Registration: {registration}")
    
    # Timing information
    departure_time = aircraft.get('departure_time') or aircraft.get('dep_time')
    arrival_time = aircraft.get('arrival_time') or aircraft.get('arr_time')
    estimated_arrival = aircraft.get('estimated_arrival') or aircraft.get('eta')
    
    if departure_time:
        print(f"Departure Time: {departure_time}")
    
    if arrival_time:
        print(f"Arrival Time: {arrival_time}")
    
    if estimated_arrival:
        print(f"Estimated Arrival: {estimated_arrival}")
    
    # Airline and route information
    airline = aircraft.get('airline') or aircraft.get('operator')
    if airline:
        print(f"Airline/Operator: {airline}")
    
    route = aircraft.get('route')
    if route:
        print(f"Route: {route}")

def display_position_data(aircraft: Dict):
    """Display position and movement data"""
    # Position
    lat = aircraft.get('lat')
    lon = aircraft.get('lon')
    print(f"Position: {format_coordinate(lat)}, {format_coordinate(lon)}")
    
    # Altitude
    altitude = aircraft.get('alt_baro') or aircraft.get('alt_geom')
    print(f"Altitude: {format_altitude(altitude)}")
    
    # Speed and heading
    ground_speed = aircraft.get('gs')
    print(f"Ground Speed: {format_speed(ground_speed)}")
    
    track = aircraft.get('track')
    print(f"Track/Heading: {format_heading(track)}")
    
    # Vertical rate
    vert_rate = aircraft.get('baro_rate') or aircraft.get('geom_rate')
    print(f"Vertical Rate: {format_vertical_rate(vert_rate)}")

def display_technical_data(aircraft: Dict):
    """Display technical aircraft data"""
    # Squawk code
    squawk = aircraft.get('squawk')
    print(f"Squawk: {format_squawk(squawk)}")
    
    # Signal strength
    rssi = aircraft.get('rssi')
    if rssi is not None:
        print(f"Signal Strength: {format_signal_strength(rssi)}")
    
    # Last seen and message count
    seen = aircraft.get('seen')
    if seen is not None:
        print(f"Last seen: {format_last_seen(seen)}")
    
    messages = aircraft.get('messages')
    if messages is not None:
        print(f"Messages received: {format_messages(messages)}")

def display_aircraft_info(aircraft_data: Dict, filter_by_callsign: bool = False, enhance_data: bool = False):
    """
    Display formatted aircraft information
    
    Args:
        aircraft_data (Dict): Aircraft data from dump1090-fa
        filter_by_callsign (bool): Whether to filter out aircraft without flight/callsign
        enhance_data (bool): Whether to enhance data with additional information
    """
    if not aircraft_data or 'aircraft' not in aircraft_data:
        print("No aircraft data available.")
        return
    
    aircraft_list = aircraft_data['aircraft']
    
    if not aircraft_list:
        print("No aircraft currently detected.")
        return
    
    # Enhance data if requested and available
    if enhance_data and ENHANCER_AVAILABLE:
        print("Enhancing aircraft data with additional information...")
        aircraft_list = enhance_aircraft_list(aircraft_list)
    elif enhance_data and not ENHANCER_AVAILABLE:
        print("Warning: Flight enhancer not available. Install requests module for enhanced data.")
    
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
        filtered_count=len(aircraft_to_display) if filter_by_callsign else None,
        filtered=filter_by_callsign
    )
    
    # Display each aircraft
    for i, aircraft in enumerate(aircraft_to_display, 1):
        display_single_aircraft(aircraft, i)
