#!/usr/bin/env python3
"""
Configuration Management for Airplane Tracker
Handles loading and managing configuration from flat config file
"""

import os
from typing import Dict, Any, Optional


class AirplaneTrackerConfig:
    """Configuration manager for airplane tracker"""

    def __init__(self, config_file_path="config"):
        """
        Initialize configuration

        Args:
            config_file_path (str): Path to configuration file (default: "config")
        """
        self.config_file_path = config_file_path
        self.config = {}
        self.load_config()

    def load_config(self):
        """Load configuration from flat config file"""
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
        """Convert string value to appropriate Python type"""
        # Handle empty values
        if not value:
            return ""

        # Handle boolean values
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False

        # Handle numeric values
        try:
            # Try integer first
            if "." not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return bool(value)

    def _get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value"""
        value = self.get(key, default)
        return str(value) if value is not None else default

    # Data Source methods
    def get_data_source_path(self) -> str:
        """Get aircraft data source file path"""
        return self._get_str("data_source_file_path")

    def get_data_source_update_interval(self) -> int:
        """Get data source update interval in seconds"""
        return self._get_int("data_source_update_interval", 5)

    def get_data_source_timeout(self) -> int:
        """Get data source timeout in seconds"""
        return self._get_int("data_source_timeout", 10)

    # Display methods
    def is_lcd_enabled(self) -> bool:
        """Check if LCD display is enabled"""
        return self._get_bool("display_lcd_enabled", True)

    def is_oled_enabled(self) -> bool:
        """Check if OLED display is enabled"""
        return self._get_bool("display_oled_enabled", True)

    def get_lcd_update_interval(self) -> int:
        """Get LCD update interval in seconds"""
        return self._get_int("lcd_update_interval", 5)

    # OLED methods
    def get_oled_width(self) -> int:
        """Get OLED display width"""
        return self._get_int("oled_width", 128)

    def get_oled_height(self) -> int:
        """Get OLED display height"""
        return self._get_int("oled_height", 32)

    def get_oled_i2c_address(self) -> int:
        """Get OLED I2C address"""
        return self._get_int("oled_i2c_address", 60)

    def get_oled_update_interval(self) -> int:
        """Get OLED update interval in seconds"""
        return self._get_int("oled_update_interval", 3)

    # Alert methods
    def are_alerts_enabled(self) -> bool:
        """Check if alerts are enabled"""
        return self._get_bool("alerts_enabled", True)

    def should_filter_by_callsign(self) -> bool:
        """Check if should filter alerts by callsign"""
        return self._get_bool("alerts_filter_by_callsign", True)

    def get_aircraft_timeout(self) -> int:
        """Get aircraft timeout in seconds"""
        return self._get_int("alerts_aircraft_timeout", 300)

    # Logging methods
    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled"""
        return self._get_bool("logging_enabled", False)

    def get_log_file_path(self) -> str:
        """Get log file path"""
        return self._get_str("logging_file_path", "aircraft_log.txt")

    def get_log_level(self) -> str:
        """Get logging level"""
        return self._get_str("logging_level", "INFO")

    # Enhancement methods
    def is_enhancement_enabled(self) -> bool:
        """Check if flight enhancement is enabled"""
        return self._get_bool("enhancement_enabled", False)

    def get_enhancement_cache_timeout(self) -> int:
        """Get enhancement cache timeout in seconds"""
        return self._get_int("enhancement_cache_timeout", 300)

    def get_enhancement_api_rate_limit(self) -> int:
        """Get enhancement API rate limit in seconds"""
        return self._get_int("enhancement_api_rate_limit", 1)


# Global configuration instance
_config_instance = None


def get_config() -> AirplaneTrackerConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AirplaneTrackerConfig()
    return _config_instance


def reload_config():
    """Reload configuration from file"""
    global _config_instance
    _config_instance = AirplaneTrackerConfig()
    return _config_instance
