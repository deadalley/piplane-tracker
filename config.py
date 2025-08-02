#!/usr/bin/env python3
"""
Configuration Management System for PiPlane Tracker

This module provides comprehensive configuration management for the PiPlane Tracker
aircraft monitoring system. It handles loading, parsing, and accessing configuration
data from a flat file format.

Key Features:
- Flat file configuration with key=value pairs
- Automatic type conversion (bool, int, float, string)
- Comment and empty line support
- Default value handling
- Singleton pattern for global configuration access
- Type-safe getter methods with validation
- Comprehensive error handling and validation

Configuration Categories:
- Data Source: File paths, update intervals, timeouts
- Display Settings: LCD/OLED enable/disable, update rates
- OLED Hardware: Dimensions, I2C address settings
- Alert System: Enable/disable, filtering, timeouts
- Logging: File paths, levels, enable/disable
- API Enhancement: OpenSky Network integration settings

Usage:
    # Get global configuration instance
    config = get_config()

    # Access configuration values
    data_path = config.get_data_source_path()
    is_lcd_enabled = config.is_lcd_enabled()

    # Reload configuration
    reload_config()

Author: Your Name
Version: 1.0
License: MIT
Created: 2024
"""

import os
from typing import Dict, Any, Optional


class PiPlaneTrackerConfig:
    """
    Main configuration manager for PiPlane Tracker.

    This class handles all aspects of configuration management including:
    - Loading configuration from flat files
    - Type conversion and validation
    - Default value management
    - Error handling for missing or invalid configurations

    The configuration file uses a simple key=value format with support for:
    - Comments (lines starting with #)
    - Empty lines (ignored)
    - Boolean values (true/false, yes/no, 1/0, on/off)
    - Numeric values (integers and floats)
    - String values (everything else)
    """

    def __init__(self, config_file_path="config"):
        """
        Initialize configuration manager.

        Args:
            config_file_path (str): Path to configuration file (default: "config")
        """
        self.config_file_path = config_file_path
        self.config = {}
        self.load_config()

    def load_config(self):
        """
        Load configuration from flat config file.

        Parses the configuration file line by line, handling:
        - Comment lines (starting with #)
        - Empty lines
        - Key=value pairs with automatic type conversion
        - Error reporting for invalid lines

        The configuration is stored in self.config dictionary with
        automatic type conversion applied to values.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
        """
        if not os.path.exists(self.config_file_path):
            print(f"Warning: Config file '{self.config_file_path}' not found.")
            raise FileNotFoundError(
                f"Configuration file '{self.config_file_path}' does not exist."
            )

        try:
            with open(self.config_file_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse key=value pairs
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Convert value to appropriate type
                        self.config[key] = self._convert_value(value)
                    else:
                        print(f"Warning: Invalid config line {line_num}: {line}")

            print(f"Configuration loaded from '{self.config_file_path}'")

        except Exception as e:
            print(f"Error loading config file: {e}")

    def _convert_value(self, value: str) -> Any:
        """
        Convert string configuration value to appropriate Python type.

        Conversion hierarchy:
        1. Empty strings remain as empty strings
        2. Boolean values (true/false, yes/no, 1/0, on/off) → bool
        3. Numeric values without decimal point → int
        4. Numeric values with decimal point → float
        5. Everything else → string

        Args:
            value (str): Raw string value from configuration file

        Returns:
            Any: Converted value (bool, int, float, or str)
        """
        # Handle empty values
        if not value:
            return ""

        # Handle boolean values (case-insensitive)
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False

        # Handle numeric values
        try:
            # Try integer first (no decimal point)
            if "." not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass

        # Return as string if no other type matches
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with optional default.

        Args:
            key (str): Configuration key to retrieve
            default (Any): Default value if key doesn't exist

        Returns:
            Any: Configuration value or default if not found
        """
        return self.config.get(key, default)

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean configuration value with type validation.

        Args:
            key (str): Configuration key
            default (bool): Default value if key doesn't exist or isn't boolean

        Returns:
            bool: Boolean configuration value
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return bool(value)

    def _get_int(self, key: str, default: int = 0) -> int:
        """
        Get integer configuration value with type validation.

        Args:
            key (str): Configuration key
            default (int): Default value if key doesn't exist or isn't numeric

        Returns:
            int: Integer configuration value
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get float configuration value with type validation.

        Args:
            key (str): Configuration key
            default (float): Default value if key doesn't exist or isn't numeric

        Returns:
            float: Float configuration value
        """
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _get_str(self, key: str, default: str = "") -> str:
        """
        Get string configuration value with type validation.

        Args:
            key (str): Configuration key
            default (str): Default value if key doesn't exist

        Returns:
            str: String configuration value
        """
        value = self.get(key, default)
        return str(value) if value is not None else default

    # === DATA SOURCE CONFIGURATION METHODS ===

    def get_data_source_path(self) -> str:
        """
        Get aircraft data source file path.

        This is typically the path to dump1090-fa's aircraft.json file
        that contains real-time ADS-B aircraft data.

        Returns:
            str: Path to aircraft data JSON file
        """
        return self._get_str("data_source_file_path")

    def get_data_source_update_interval(self) -> int:
        """
        Get data source update interval in seconds.

        Controls how frequently the system checks for new aircraft data.
        Lower values provide more real-time updates but use more CPU.

        Returns:
            int: Update interval in seconds (default: 5)
        """
        return self._get_int("data_source_update_interval", 5)

    def get_data_source_timeout(self) -> int:
        """
        Get data source timeout in seconds.

        Maximum time to wait when reading the data source file.

        Returns:
            int: Timeout in seconds (default: 10)
        """
        return self._get_int("data_source_timeout", 10)

    # === DISPLAY CONFIGURATION METHODS ===

    def is_lcd_enabled(self) -> bool:
        """
        Check if LCD display is enabled.

        Returns:
            bool: True if LCD display should be used (default: True)
        """
        return self._get_bool("display_lcd_enabled", True)

    def is_oled_enabled(self) -> bool:
        """
        Check if OLED display is enabled.

        Returns:
            bool: True if OLED display should be used (default: True)
        """
        return self._get_bool("display_oled_enabled", True)

    def get_lcd_update_interval(self) -> int:
        """
        Get LCD update interval in seconds.

        Controls how frequently the LCD display is refreshed with new information.

        Returns:
            int: LCD update interval in seconds (default: 5)
        """
        return self._get_int("lcd_update_interval", 5)

    # === OLED CONFIGURATION METHODS ===

    def get_oled_width(self) -> int:
        """
        Get OLED display width in pixels.

        Returns:
            int: OLED width in pixels (default: 128)
        """
        return self._get_int("oled_width", 128)

    def get_oled_height(self) -> int:
        """
        Get OLED display height in pixels.

        Returns:
            int: OLED height in pixels (default: 32)
        """
        return self._get_int("oled_height", 32)

    def get_oled_i2c_address(self) -> int:
        """
        Get OLED I2C address.

        Most SSD1306 OLED displays use address 0x3C (60 decimal).

        Returns:
            int: I2C address for OLED display (default: 60)
        """
        return self._get_int("oled_i2c_address", 60)

    def get_oled_update_interval(self) -> int:
        """
        Get OLED update interval in seconds.

        Controls how frequently the OLED display is refreshed with new information.

        Returns:
            int: OLED update interval in seconds (default: 3)
        """
        return self._get_int("oled_update_interval", 3)

    # === ALERT SYSTEM CONFIGURATION METHODS ===

    def are_alerts_enabled(self) -> bool:
        """
        Check if alert system is enabled.

        Returns:
            bool: True if alerts should be shown (default: True)
        """
        return self._get_bool("alerts_enabled", True)

    def should_filter_by_callsign(self) -> bool:
        """
        Check if alerts should be filtered by callsign presence.

        When enabled, only aircraft with valid callsigns trigger alerts.

        Returns:
            bool: True if callsign filtering is enabled (default: True)
        """
        return self._get_bool("alerts_filter_by_callsign", True)

    def get_aircraft_timeout(self) -> int:
        """
        Get aircraft timeout in seconds.

        Aircraft not seen for this duration are removed from tracking history.

        Returns:
            int: Aircraft timeout in seconds (default: 300 = 5 minutes)
        """
        return self._get_int("alerts_aircraft_timeout", 300)

    # === LOGGING CONFIGURATION METHODS ===

    def is_logging_enabled(self) -> bool:
        """
        Check if logging is enabled.

        Returns:
            bool: True if logging should be enabled (default: False)
        """
        return self._get_bool("logging_enabled", False)

    def get_log_file_path(self) -> str:
        """
        Get log file path.

        Returns:
            str: Path to log file (default: "aircraft_log.txt")
        """
        return self._get_str("logging_file_path", "aircraft_log.txt")

    def get_log_level(self) -> str:
        """
        Get logging level.

        Returns:
            str: Logging level (default: "INFO")
        """
        return self._get_str("logging_level", "INFO")

    # === API ENHANCEMENT CONFIGURATION METHODS ===

    def is_enhancement_enabled(self) -> bool:
        """
        Check if flight enhancement via APIs is enabled.

        When enabled, additional aircraft information is fetched from
        external APIs like OpenSky Network.

        Returns:
            bool: True if API enhancement is enabled (default: False)
        """
        return self._get_bool("enhancement_enabled", False)

    def get_enhancement_cache_timeout(self) -> int:
        """
        Get enhancement cache timeout in seconds.

        How long to cache API enhancement data before refetching.

        Returns:
            int: Cache timeout in seconds (default: 300 = 5 minutes)
        """
        return self._get_int("enhancement_cache_timeout", 300)

    def get_enhancement_api_rate_limit(self) -> int:
        """
        Get enhancement API rate limit in seconds.

        Minimum time between API calls to respect rate limits.

        Returns:
            int: Rate limit in seconds (default: 1)
        """
        return self._get_int("enhancement_api_rate_limit", 1)


# === GLOBAL CONFIGURATION MANAGEMENT ===

# Global configuration instance (singleton pattern)
_config_instance = None


def get_config() -> PiPlaneTrackerConfig:
    """
    Get global configuration instance (singleton pattern).

    This ensures that configuration is loaded only once and shared
    across the entire application.

    Returns:
        PiPlaneTrackerConfig: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = PiPlaneTrackerConfig()
    return _config_instance


def reload_config():
    """
    Reload configuration from file.

    Forces a reload of the configuration file, useful for applying
    configuration changes without restarting the application.

    Returns:
        PiPlaneTrackerConfig: The reloaded configuration instance
    """
    global _config_instance
    _config_instance = PiPlaneTrackerConfig()
    return _config_instance
