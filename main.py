#!/usr/bin/env python3
"""
PiPlane Tracker - Main Application Entry Point

A comprehensive aircraft tracking system for Raspberry Pi that monitors ADS-B data
in real-time and displays information on LCD/OLED screens.

This module provides:
- Direct aircraft monitoring startup
- Display controller initialization and management
- Data source validation and connection testing
- Graceful shutdown handling and cleanup

Features:
- Real-time aircraft monitoring with new aircraft alerts
- Dual display support (16x2 LCD and 128x32 OLED)
- Aircraft history tracking and review
- Configurable settings via flat-file configuration

Author: Your Name
Version: 1.0
License: MIT
Created: 2024
"""

import sys
import signal
import os

from services.monitor_service import PiPlaneMonitorService
from controllers.lcd_controller import PiPlaneLCDController
from controllers.oled_controller import PiPlaneOLEDController

try:
    import termios
    import tty

    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False

from datetime import datetime
from config import get_config
from services.monitor_service import PiPlaneMonitorService
from controllers.lcd_controller import PiPlaneLCDController
from controllers.oled_controller import PiPlaneOLEDController

# Global variables for cleanup
running = True
monitor = None
lcd_controller = None
oled_controller = None


def handle_shutdown(signum, frame):
    """
    Handle shutdown signals for graceful cleanup.

    Catches SIGTERM (from systemd) and SIGINT (Ctrl+C) and performs
    clean shutdown of the application, ensuring all resources are
    properly released.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global running, monitor, lcd_controller, oled_controller

    signal_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n🛑 Shutdown signal received ({signal_name})")
    running = False

    # Perform cleanup
    print("🧹 Cleaning up...")
    if monitor:
        monitor.cleanup()
    if lcd_controller:
        lcd_controller.cleanup()
    if oled_controller:
        oled_controller.cleanup()
    print("✅ Cleanup complete")

    sys.exit(0)


def initialize_displays():
    """
    Initialize LCD and OLED display controllers.

    Attempts to initialize both display types based on configuration settings.
    Handles initialization failures gracefully and continues operation with
    available displays.

    Display initialization order:
    1. Check configuration for enabled displays
    2. Attempt LCD controller initialization (16x2 I2C)
    3. Attempt OLED controller initialization (128x32 SSD1306)
    4. Report initialization status

    Returns:
        tuple: (lcd_controller, oled_controller)
            - lcd_controller: PiPlaneLCDController instance or None
            - oled_controller: PiPlaneOLEDController instance or None
    """
    config = get_config()
    lcd_controller = None
    oled_controller = None

    # Initialize LCD controller (if enabled in configuration)
    if config.is_lcd_enabled():
        try:
            lcd_controller = PiPlaneLCDController()
            print("✅ LCD controller initialized")
        except Exception as e:
            print(f"⚠️  LCD controller initialization failed: {e}")
            lcd_controller = None

    # Initialize OLED controller (if enabled in configuration)
    if config.is_oled_enabled():
        try:
            oled_controller = PiPlaneOLEDController()
            print("✅ OLED controller initialized")
        except Exception as e:
            print(f"⚠️  OLED controller initialization failed: {e}")
            oled_controller = None

    return lcd_controller, oled_controller


def test_data_connection():
    """
    Test connectivity to the ADS-B data source.

    Verifies that the configured data source file (typically from dump1090-fa)
    exists and is accessible. This is crucial for the monitoring system to
    function properly.

    The test checks:
    - Data source file path from configuration
    - File existence and accessibility
    - Provides helpful error messages for troubleshooting

    Returns:
        bool: True if data source is accessible

    Raises:
        FileNotFoundError: If data source file doesn't exist
        Exception: For other data connection issues
    """
    print("\n🔍 Testing data connection...")
    try:
        config = get_config()
        data_file_path = config.get_data_source_path()

        if os.path.exists(data_file_path):
            print(f"✅ Data file found at {data_file_path}")
            return True
        else:
            print(f"⚠️  Data file not found at {data_file_path}")
            print("   Make sure dump1090-fa is running and the data file exists")
            raise FileNotFoundError(f"Data file not found: {data_file_path}")

    except Exception as e:
        print(f"❌ Data connection test failed: {e}")
        raise e


def main():
    """
    Main application entry point for direct aircraft monitoring.

    This is the central controller for the PiPlane Tracker application.
    It orchestrates all major components and starts monitoring immediately.

    Application flow:
    1. Display startup banner and system information
    2. Handle command line arguments (--help, -h)
    3. Register signal handlers for graceful shutdown
    4. Load and validate configuration
    5. Test data source connectivity
    6. Initialize display hardware
    7. Set up monitoring service
    8. Start aircraft monitoring directly
    9. Handle shutdown and cleanup

    Features handled:
    - Configuration loading and validation
    - Hardware initialization with fallback
    - Real-time aircraft monitoring
    - Aircraft history management
    - Graceful shutdown and cleanup

    Command line options:
    - --help, -h: Display help information and exit

    The function handles all exceptions gracefully and ensures proper
    cleanup of resources before termination.
    """
    # Display startup banner with system information
    print("=" * 60)
    print("🛩️  PiPlane Tracker v1.0")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Handle command line help requests
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\nUsage: python3 main.py [options]")
        print("\nOptions:")
        print("  --help, -h        Show this help message")
        print("\nConfiguration:")
        print("  - Edit the 'config' file to change default settings")
        print("  - Data source, display options, and more can be configured")
        print("\nOperation:")
        print("  - The application starts monitoring immediately")
        print("  - Press Ctrl+C to stop monitoring and exit")
        print("  - Interactive console available if visualization is enabled")
        return

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)  # From systemd
    signal.signal(signal.SIGINT, handle_shutdown)  # From Ctrl+C

    # Load configuration
    config = get_config()
    print(f"📁 Data source: {config.get_data_source_path()}")

    # Test data connection
    test_data_connection()

    # Initialize displays
    print("\n🔧 Initializing displays...")
    global lcd_controller, oled_controller
    lcd_controller, oled_controller = initialize_displays()

    # Initialize monitor system
    global monitor
    try:
        monitor = PiPlaneMonitorService(
            lcd_controller=lcd_controller,
            oled_controller=oled_controller,
            enable_visualization=config.is_visualization_enabled(),
        )
        print("✅ Monitor system initialized")
    except Exception as e:
        print(f"⚠️  Monitor system initialization failed: {e}")
        monitor = None
        return

    # Start monitoring directly
    try:
        print("-" * 60)
        print("🔍 Starting aircraft monitoring...")
        print("Press Ctrl+C to quit")
        print("-" * 60)

        monitor.start_monitoring(interval=5)

    except KeyboardInterrupt:
        print("\n\n🛑 PiPlane Tracker interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
    finally:
        # Cleanup (if not already done by signal handler)
        if running:
            print("\n🧹 Cleaning up...")
            if monitor:
                monitor.cleanup()
            if lcd_controller:
                lcd_controller.cleanup()
            if oled_controller:
                oled_controller.cleanup()
            print("✅ Cleanup complete")


if __name__ == "__main__":
    main()
