#!/usr/bin/env python3
"""
Flight Data Enhancement Module
Provides additional flight information from external APIs
"""

import requests
import json
from typing import Dict, Optional
import time


class FlightDataEnhancer:
    """
    Class to enhance basic aircraft data with additional flight information
    """

    def __init__(self):
        """Initialize the flight data enhancer"""
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.last_api_call = 0
        self.api_rate_limit = 1  # seconds between API calls

    def get_flight_info_from_callsign(self, callsign: str) -> Optional[Dict]:
        """
        Get flight information from callsign using public APIs
        Note: This is a placeholder - you'll need API keys for real services

        Args:
            callsign (str): Aircraft callsign/flight number

        Returns:
            Dict: Flight information or None
        """
        if not callsign:
            return None

        # Check cache first
        cache_key = f"flight_{callsign}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return cached_data

        # Rate limiting
        current_time = time.time()
        if current_time - self.last_api_call < self.api_rate_limit:
            time.sleep(self.api_rate_limit - (current_time - self.last_api_call))

        try:
            # Example using a free API (you may need to register for API key)
            # This is a placeholder - replace with actual API calls

            # Option 1: FlightAware API (requires API key)
            # url = f"https://aeroapi.flightaware.com/aeroapi/flights/{callsign}"
            # headers = {"x-apikey": "YOUR_API_KEY"}

            # Option 2: AviationStack API (has free tier)
            # url = f"http://api.aviationstack.com/v1/flights"
            # params = {"access_key": "YOUR_API_KEY", "flight_iata": callsign}

            # For demo purposes, return mock data structure
            # In real implementation, uncomment API calls above
            mock_data = {
                "origin": "Unknown",
                "destination": "Unknown",
                "aircraft_type": "Unknown",
                "airline": "Unknown",
                "departure_time": "Unknown",
                "arrival_time": "Unknown",
                "registration": "Unknown",
            }

            # Cache the result
            self.cache[cache_key] = (mock_data, current_time)
            self.last_api_call = current_time

            return mock_data

        except Exception as e:
            print(f"Error fetching flight info for {callsign}: {e}")
            return None

    def get_aircraft_info_from_icao(self, hex_code: str) -> Optional[Dict]:
        """
        Get aircraft registration and type from ICAO hex code

        Args:
            hex_code (str): ICAO hex identifier

        Returns:
            Dict: Aircraft information or None
        """
        if not hex_code:
            return None

        cache_key = f"aircraft_{hex_code}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return cached_data

        try:
            # Example using OpenSky Network API (free, no key required)
            # This provides aircraft registration and some basic info
            current_time = time.time()

            # Rate limiting
            if current_time - self.last_api_call < self.api_rate_limit:
                time.sleep(self.api_rate_limit - (current_time - self.last_api_call))

            # Uncomment for real API call:
            # url = f"https://opensky-network.org/api/metadata/aircraft/icao/{hex_code}"
            # response = requests.get(url, timeout=10)
            #
            # if response.status_code == 200:
            #     data = response.json()
            #     aircraft_info = {
            #         'registration': data.get('registration', 'Unknown'),
            #         'aircraft_type': data.get('manufacturerName', '') + ' ' + data.get('model', ''),
            #         'owner': data.get('owner', 'Unknown')
            #     }
            # else:
            #     aircraft_info = None

            # Mock data for demo
            aircraft_info = {
                "registration": "N/A",
                "aircraft_type": "Unknown",
                "owner": "Unknown",
            }

            # Cache the result
            if aircraft_info:
                self.cache[cache_key] = (aircraft_info, current_time)

            self.last_api_call = current_time
            return aircraft_info

        except Exception as e:
            print(f"Error fetching aircraft info for {hex_code}: {e}")
            return None

    def enhance_aircraft_data(self, aircraft: Dict) -> Dict:
        """
        Enhance aircraft data with additional information

        Args:
            aircraft (Dict): Basic aircraft data from dump1090-fa

        Returns:
            Dict: Enhanced aircraft data
        """
        enhanced = aircraft.copy()

        # Get flight information if callsign is available
        callsign = aircraft.get("flight", "").strip()
        if callsign:
            flight_info = self.get_flight_info_from_callsign(callsign)
            if flight_info:
                enhanced.update(flight_info)

        # Get aircraft information from ICAO hex
        hex_code = aircraft.get("hex")
        if hex_code:
            aircraft_info = self.get_aircraft_info_from_icao(hex_code)
            if aircraft_info:
                enhanced.update(aircraft_info)

        return enhanced

    def clear_cache(self):
        """Clear the data cache"""
        self.cache.clear()


# Global enhancer instance
flight_enhancer = FlightDataEnhancer()


def enhance_aircraft_list(aircraft_list):
    """
    Enhance a list of aircraft with additional data

    Args:
        aircraft_list (List[Dict]): List of aircraft data

    Returns:
        List[Dict]: Enhanced aircraft data
    """
    enhanced_list = []

    for aircraft in aircraft_list:
        try:
            enhanced = flight_enhancer.enhance_aircraft_data(aircraft)
            enhanced_list.append(enhanced)
        except Exception as e:
            print(f"Error enhancing aircraft data: {e}")
            enhanced_list.append(aircraft)  # Use original data if enhancement fails

    return enhanced_list


if __name__ == "__main__":
    # Test the enhancer
    test_aircraft = {
        "hex": "A12345",
        "flight": "UAL123",
        "lat": 37.7749,
        "lon": -122.4194,
        "alt_baro": 35000,
    }

    enhancer = FlightDataEnhancer()
    enhanced = enhancer.enhance_aircraft_data(test_aircraft)

    print("Original:", test_aircraft)
    print("Enhanced:", enhanced)
