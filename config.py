#!/usr/bin/env python3
"""
Configuration Management for Airplane Tracker
Handles loading and managing configuration from flat config file
"""

import os
from typing import Dict, Any, Optional

class AirplaneTrackerConfig:
    """Configuration manager for airplane tracker"""
    
    def __init__(self, config_file="config"):
        """
        Initialize configuration
        
        Args:
            config_file (str): Path to configuration file (default: "config")
        """
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from flat config file"""
        if not os.path.exists(self.config_file):
            print(f"Warning: Config file '{self.config_file}' not found. Using defaults.")
            self._load_defaults()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert value to appropriate type
                        self.config[key] = self._convert_value(value)
                    else:
                        print(f"Warning: Invalid config line {line_num}: {line}")
            
            print(f"Configuration loaded from '{self.config_file}'")
            
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration.")
            self._load_defaults()
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate Python type"""
        # Handle empty values
        if not value:
            return ""
        
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Handle numeric values
        try:
            # Try integer first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _load_defaults(self):
        """Load default configuration values"""
        self.config = {
            # Data Source
            'data_source_file_path': '/var/run/dump1090-fa/aircraft.json',
            'data_source_update_interval': 5,
            'data_source_timeout': 10,
            
            # Display
            'display_lcd_enabled': True,
            'display_oled_enabled': True,
            'display_gui_enabled': True,
            
            # LCD
            'lcd_pin_rs': 26,
            'lcd_pin_enable': 19,
            'lcd_pin_d4': 13,
            'lcd_pin_d5': 6,
            'lcd_pin_d6': 5,
            'lcd_pin_d7': 11,
            'lcd_update_interval': 5,
            
            # OLED
            'oled_width': 128,
            'oled_height': 32,
            'oled_i2c_address': 60,
            'oled_update_interval': 3,
            
            # Alerts
            'alerts_enabled': True,
            'alerts_sound_enabled': False,
            'alerts_sound_file': '',
            'alerts_filter_by_callsign': True,
            'alerts_aircraft_timeout': 300,
            
            # Logging
            'logging_enabled': False,
            'logging_file_path': 'aircraft_log.txt',
            'logging_level': 'INFO',
            
            # Enhancement
            'enhancement_enabled': False,
            'enhancement_cache_timeout': 300,
            'enhancement_api_rate_limit': 1
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return bool(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value"""
        value = self.get(key, default)
        return str(value) if value is not None else default
    
    # Data Source methods
    def get_data_source_path(self) -> str:
        """Get aircraft data source file path"""
        return self.get_str('data_source_file_path', '/var/run/dump1090-fa/aircraft.json')
    
    def get_data_source_update_interval(self) -> int:
        """Get data source update interval in seconds"""
        return self.get_int('data_source_update_interval', 5)
    
    def get_data_source_timeout(self) -> int:
        """Get data source timeout in seconds"""
        return self.get_int('data_source_timeout', 10)
    
    # Display methods
    def is_lcd_enabled(self) -> bool:
        """Check if LCD display is enabled"""
        return self.get_bool('display_lcd_enabled', True)
    
    def is_oled_enabled(self) -> bool:
        """Check if OLED display is enabled"""
        return self.get_bool('display_oled_enabled', True)
    
    def is_gui_enabled(self) -> bool:
        """Check if GUI is enabled"""
        return self.get_bool('display_gui_enabled', True)
    
    def get_lcd_update_interval(self) -> int:
        """Get LCD update interval in seconds"""
        return self.get_int('lcd_update_interval', 5)
    
    # OLED methods
    def get_oled_width(self) -> int:
        """Get OLED display width"""
        return self.get_int('oled_width', 128)
    
    def get_oled_height(self) -> int:
        """Get OLED display height"""
        return self.get_int('oled_height', 32)
    
    def get_oled_i2c_address(self) -> int:
        """Get OLED I2C address"""
        return self.get_int('oled_i2c_address', 60)
    
    def get_oled_update_interval(self) -> int:
        """Get OLED update interval in seconds"""
        return self.get_int('oled_update_interval', 3)
    
    # Alert methods
    def are_alerts_enabled(self) -> bool:
        """Check if alerts are enabled"""
        return self.get_bool('alerts_enabled', True)
    
    def is_sound_enabled(self) -> bool:
        """Check if sound alerts are enabled"""
        return self.get_bool('alerts_sound_enabled', False)
    
    def get_sound_file(self) -> str:
        """Get alert sound file path"""
        return self.get_str('alerts_sound_file', '')
    
    def should_filter_by_callsign(self) -> bool:
        """Check if should filter alerts by callsign"""
        return self.get_bool('alerts_filter_by_callsign', True)
    
    def get_aircraft_timeout(self) -> int:
        """Get aircraft timeout in seconds"""
        return self.get_int('alerts_aircraft_timeout', 300)
    
    # Logging methods
    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled"""
        return self.get_bool('logging_enabled', False)
    
    def get_log_file_path(self) -> str:
        """Get log file path"""
        return self.get_str('logging_file_path', 'aircraft_log.txt')
    
    def get_log_level(self) -> str:
        """Get logging level"""
        return self.get_str('logging_level', 'INFO')
    
    # Enhancement methods
    def is_enhancement_enabled(self) -> bool:
        """Check if flight enhancement is enabled"""
        return self.get_bool('enhancement_enabled', False)
    
    def get_enhancement_cache_timeout(self) -> int:
        """Get enhancement cache timeout in seconds"""
        return self.get_int('enhancement_cache_timeout', 300)
    
    def get_enhancement_api_rate_limit(self) -> int:
        """Get enhancement API rate limit in seconds"""
        return self.get_int('enhancement_api_rate_limit', 1)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                f.write("# Airplane Tracker Configuration\n")
                f.write("# Edit these values to customize your airplane tracker settings\n\n")
                
                # Data Source Settings
                f.write("# Data Source Settings\n")
                f.write(f"data_source_file_path={self.get_data_source_path()}\n")
                f.write(f"data_source_update_interval={self.get_data_source_update_interval()}\n")
                f.write(f"data_source_timeout={self.get_data_source_timeout()}\n\n")
                
                # Display Settings
                f.write("# Display Settings\n")
                f.write(f"display_lcd_enabled={str(self.is_lcd_enabled()).lower()}\n")
                f.write(f"display_oled_enabled={str(self.is_oled_enabled()).lower()}\n")
                f.write(f"display_gui_enabled={str(self.is_gui_enabled()).lower()}\n\n")
                
                # LCD Configuration
                f.write("# LCD Configuration\n")
                f.write(f"lcd_update_interval={self.get_lcd_update_interval()}\n\n")
                
                # OLED Configuration
                f.write("# OLED Configuration\n")
                f.write(f"oled_width={self.get_oled_width()}\n")
                f.write(f"oled_height={self.get_oled_height()}\n")
                f.write(f"oled_i2c_address={self.get_oled_i2c_address()}\n")
                f.write(f"oled_update_interval={self.get_oled_update_interval()}\n\n")
                
                # Alert Settings
                f.write("# Alert Settings\n")
                f.write(f"alerts_enabled={str(self.are_alerts_enabled()).lower()}\n")
                f.write(f"alerts_sound_enabled={str(self.is_sound_enabled()).lower()}\n")
                f.write(f"alerts_sound_file={self.get_sound_file()}\n")
                f.write(f"alerts_filter_by_callsign={str(self.should_filter_by_callsign()).lower()}\n")
                f.write(f"alerts_aircraft_timeout={self.get_aircraft_timeout()}\n\n")
                
                # Logging Settings
                f.write("# Logging Settings\n")
                f.write(f"logging_enabled={str(self.is_logging_enabled()).lower()}\n")
                f.write(f"logging_file_path={self.get_log_file_path()}\n")
                f.write(f"logging_level={self.get_log_level()}\n\n")
                
                # Enhancement Settings
                f.write("# Enhancement Settings (API data)\n")
                f.write(f"enhancement_enabled={str(self.is_enhancement_enabled()).lower()}\n")
                f.write(f"enhancement_cache_timeout={self.get_enhancement_cache_timeout()}\n")
                f.write(f"enhancement_api_rate_limit={self.get_enhancement_api_rate_limit()}\n")
                
            print(f"Configuration saved to '{self.config_file}'")
            
        except Exception as e:
            print(f"Error saving config file: {e}")

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

if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    print(f"Data source path: {config.get_data_source_path()}")
    print(f"LCD enabled: {config.is_lcd_enabled()}")
    print(f"OLED enabled: {config.is_oled_enabled()}")
    print(f"OLED size: {config.get_oled_width()}x{config.get_oled_height()}")
