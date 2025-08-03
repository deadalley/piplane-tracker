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
- Data Source: File paths for aircraft data
- Display Settings: LCD/OLED enable/disable
- OLED Hardware: Dimensions, I2C address settings
- Sound Alert System: Audio notification settings

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

    # === SOUND ALERT CONFIGURATION METHODS ===

    def get_sound_alert_volume(self) -> int:
        """
        Get sound alert volume percentage.

        Returns:
            int: Volume percentage 0-100 (default: 70)
        """
        return self._get_int("sound_alert_volume", 70)

    def get_sound_alert_cooldown(self) -> float:
        """
        Get sound alert cooldown time in seconds.

        Minimum time between alerts to prevent spam.

        Returns:
            float: Cooldown time in seconds (default: 1.0)
        """
        return self._get_float("sound_alert_cooldown", 1.0)

    def get_sound_alert_audio_file(self) -> str:
        """
        Get path to custom audio file for alerts.

        Returns:
            str: Path to audio file (default: empty string)
        """
        return self._get_str("sound_alert_audio_file", "")


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
