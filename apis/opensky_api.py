#!/usr/bin/env python3
"""
OpenSky Network API Integration
Provides enhanced flight information using the OpenSky Network API
"""

import requests
from typing import Dict, Optional
import time
from datetime import datetime, timedelta


class OpenSkyAPI:
    """OpenSky Network API client"""

    def __init__(self, rate_limit_seconds: float = 1.0):
        """
        Initialize OpenSky API client

        Args:
            rate_limit_seconds (float): Minimum seconds between API calls
        """
        self.base_url = "https://opensky-network.org/api"
        self.rate_limit = rate_limit_seconds
        self._last_request_time = 0
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes

    def _respect_rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _is_cache_valid(self, icao24: str) -> bool:
        """Check if cached data is still valid"""
        if icao24 not in self._cache:
            return False

        cache_entry = self._cache[icao24]
        cache_time = cache_entry.get("timestamp", 0)
        current_time = time.time()

        return (current_time - cache_time) < self._cache_timeout

    def _get_cached_data(self, icao24: str) -> Optional[Dict]:
        """Get cached data if available and valid"""
        if self._is_cache_valid(icao24):
            return self._cache[icao24]["data"]
        return None

    def _cache_data(self, icao24: str, data: Dict):
        """Cache API response data"""
        self._cache[icao24] = {"data": data, "timestamp": time.time()}

    def get_aircraft_state(self, icao24: str) -> Optional[Dict]:
        """
        Get aircraft state information from OpenSky Network API

        Args:
            icao24 (str): ICAO24 code (hex) from aircraft data

        Returns:
            Optional[Dict]: Aircraft state information or None if not found
        """
        # Check cache first
        cached_data = self._get_cached_data(icao24)
        if cached_data:
            return cached_data

        try:
            # Respect rate limiting
            self._respect_rate_limit()

            # Make API request
            url = f"{self.base_url}/states/all"
            params = {"icao24": icao24.lower()}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get("states") and len(data["states"]) > 0:
                    state = data["states"][0]

                    # Parse the state vector
                    aircraft_data = {
                        "icao24": state[0],
                        "callsign": state[1].strip() if state[1] else None,
                        "origin_country": state[2],
                        "time_position": state[3],
                        "last_contact": state[4],
                        "longitude": state[5],
                        "latitude": state[6],
                        "baro_altitude": state[7],
                        "on_ground": state[8],
                        "velocity": state[9],
                        "true_track": state[10],
                        "vertical_rate": state[11],
                        "sensors": state[12],
                        "geo_altitude": state[13],
                        "squawk": state[14],
                        "spi": state[15],
                        "position_source": state[16],
                    }

                    # Cache the data
                    self._cache_data(icao24, aircraft_data)

                    return aircraft_data
            else:
                print(f"OpenSky API returned status code: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"Timeout fetching OpenSky data for {icao24}")
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching OpenSky data for {icao24}: {e}")
        except Exception as e:
            print(f"Error fetching OpenSky data for {icao24}: {e}")

        return None

    def get_enhanced_info(self, icao24: str) -> Optional[Dict]:
        """
        Get enhanced aircraft information formatted for display

        Args:
            icao24 (str): ICAO24 code (hex) from aircraft data

        Returns:
            Optional[Dict]: Enhanced information or None if not available
        """
        state_data = self.get_aircraft_state(icao24)

        if not state_data:
            return None

        # Format data for display
        enhanced_info = {}

        # Enhanced callsign
        if state_data.get("callsign"):
            enhanced_info["callsign"] = state_data["callsign"]

        # Origin country
        if state_data.get("origin_country"):
            enhanced_info["origin_country"] = state_data["origin_country"]

        # Ground status
        if state_data.get("on_ground") is not None:
            enhanced_info["on_ground"] = state_data["on_ground"]
            enhanced_info["status"] = (
                "On Ground" if state_data["on_ground"] else "In Flight"
            )

        # Last contact time
        if state_data.get("last_contact"):
            last_contact = datetime.fromtimestamp(state_data["last_contact"])
            enhanced_info["last_contact"] = last_contact.strftime("%H:%M:%S")

        # Position source
        if state_data.get("position_source") is not None:
            source_map = {0: "ADS-B", 1: "ASTERIX", 2: "MLAT", 3: "FLARM"}
            enhanced_info["position_source"] = source_map.get(
                state_data["position_source"], "Unknown"
            )

        return enhanced_info

    def clear_cache(self):
        """Clear the API response cache"""
        self._cache.clear()

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        current_time = time.time()
        valid_entries = 0

        for icao24, cache_entry in self._cache.items():
            cache_time = cache_entry.get("timestamp", 0)
            if (current_time - cache_time) < self._cache_timeout:
                valid_entries += 1

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "cache_timeout": self._cache_timeout,
        }


# Global OpenSky API instance
_opensky_api = None


def get_opensky_api(rate_limit: float = 1.0) -> OpenSkyAPI:
    """
    Get singleton OpenSky API instance

    Args:
        rate_limit (float): Rate limit in seconds between requests

    Returns:
        OpenSkyAPI: The OpenSky API client instance
    """
    global _opensky_api

    if _opensky_api is None:
        _opensky_api = OpenSkyAPI(rate_limit)

    return _opensky_api


def get_enhanced_aircraft_info(icao24: str, rate_limit: float = 1.0) -> Optional[Dict]:
    """
    Convenience function to get enhanced aircraft information

    Args:
        icao24 (str): ICAO24 code (hex) from aircraft data
        rate_limit (float): Rate limit in seconds between requests

    Returns:
        Optional[Dict]: Enhanced information or None if not available
    """
    api = get_opensky_api(rate_limit)
    return api.get_enhanced_info(icao24)
