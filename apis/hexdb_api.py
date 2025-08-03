#!/usr/bin/env python3
"""
HexDB.io API Integration
Simple aircraft information lookup using HexDB.io API
"""

import requests
from typing import Dict, Optional
import time


class HexDBAPI:
    """HexDB.io API client with rate limiting and caching"""

    def __init__(self, rate_limit_seconds: float = 1.0, cache_timeout: int = 300):
        """
        Initialize HexDB API client

        Args:
            rate_limit_seconds (float): Minimum seconds between API calls
            cache_timeout (int): Cache timeout in seconds
        """
        self.rate_limit = rate_limit_seconds
        self._last_request_time = 0
        self._cache = {}
        self._cache_timeout = cache_timeout

    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _is_cache_valid(self, icao_hex: str) -> bool:
        """Check if cached data is still valid"""
        if icao_hex not in self._cache:
            return False

        cache_entry = self._cache[icao_hex]
        cache_time = cache_entry.get("timestamp", 0)
        current_time = time.time()

        return (current_time - cache_time) < self._cache_timeout

    def _get_cached_data(self, icao_hex: str) -> Optional[Dict]:
        """Get cached data if available and valid"""
        if self._is_cache_valid(icao_hex):
            return self._cache[icao_hex]["data"]
        return None

    def _cache_data(self, icao_hex: str, data: Dict):
        """Cache API response data"""
        self._cache[icao_hex] = {"data": data, "timestamp": time.time()}

    def get_aircraft_info(self, icao_hex: str) -> Optional[Dict]:
        """
        Get aircraft information from HexDB.io API with caching and rate limiting

        Args:
            icao_hex (str): ICAO24 hex code (e.g., "4010ee")

        Returns:
            Optional[Dict]: Aircraft information or None if not found
        """
        # Check cache first
        cached_data = self._get_cached_data(icao_hex)
        if cached_data:
            return cached_data

        try:
            # Respect rate limiting
            self._respect_rate_limit()

            url = f"https://hexdb.io/api/v1/aircraft/{icao_hex.lower()}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Check if response contains an error
                if "status" in data and data["status"] == "404":
                    return None

                # Cache the successful response
                self._cache_data(icao_hex, data)
                return data
            elif response.status_code == 404:
                return None
            else:
                print(f"HexDB API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching HexDB data for {icao_hex}: {e}")
            return None


# Global HexDB API instance
_hexdb_api = None


def get_hexdb_api(rate_limit: float = 1.0, cache_timeout: int = 300) -> HexDBAPI:
    """
    Get singleton HexDB API instance

    Args:
        rate_limit (float): Rate limit in seconds between requests
        cache_timeout (int): Cache timeout in seconds

    Returns:
        HexDBAPI: The HexDB API client instance
    """
    global _hexdb_api

    if _hexdb_api is None:
        _hexdb_api = HexDBAPI(rate_limit, cache_timeout)

    return _hexdb_api


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
    api = get_hexdb_api()
    hexdb_info = api.get_aircraft_info(hex_code)

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
