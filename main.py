#!/usr/bin/env python3
"""
Main PiPlane Tracker Application
"""

import sys
import signal
import os
from datetime import datetime
from config import get_config

from monitor import PiPlaneMonitor
from lcd_controller import PiPlaneLCDController
from oled_controller import PiPlaneOLEDController


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down airplane tracker...")
    sys.exit(0)


def main():
    """Main application entry point"""
    print("=" * 60)
    print("🛩️  PiPlane Tracker v1.0")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load configuration
    config = get_config()
    print(f"📁 Data source: {config.get_data_source_path()}")
    print()

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Parse command line arguments (override config)
    lcd_enabled = config.is_lcd_enabled()
    oled_enabled = config.is_oled_enabled()

    # Check for command line arguments
    for arg in sys.argv[1:]:
        if arg in ["--help", "-h"]:
            print("Usage: python3 main.py [options]")
            print("\nOptions:")
            print("  --help, -h        Show this help message")
            print("\nConfiguration:")
            print("  - Edit the 'config' file to change default settings")
            print("  - Data source, display options, and more can be configured")
            print("\nDefault behavior:")
            print("  - Runs in console mode")
            print("  - Enables both LCD and OLED displays (if hardware available)")
            print("  - Monitors for new aircraft with alerts")
            print("  - Updates every 5 seconds")
            return

    # Initialize LCD controller (if enabled)
    lcd_controller = None
    if lcd_enabled:
        try:
            lcd_controller = PiPlaneLCDController()
            lcd_controller.display_startup_message()
            print("✅ LCD controller initialized")
        except Exception as e:
            print(f"⚠️  LCD controller initialization failed: {e}")
            lcd_controller = None

    # Initialize OLED controller (if enabled)
    oled_controller = None
    if oled_enabled:
        try:
            oled_controller = PiPlaneOLEDController()
            print("✅ OLED controller initialized")
        except Exception as e:
            print(f"⚠️  OLED controller initialization failed: {e}")
            oled_controller = None

    # Initialize monitor system with display controllers
    try:
        monitor = PiPlaneMonitor(
            lcd_controller=lcd_controller, oled_controller=oled_controller
        )
        print("✅ Monitor system initialized")
    except Exception as e:
        print(f"⚠️  Monitor system initialization failed: {e}")
        monitor = None

    # Test initial data connection
    print("\nTesting data connection...")
    try:
        config = get_config()
        data_file_path = config.get_data_source_path()
        if os.path.exists(data_file_path):
            print(f"✅ Data file found at {data_file_path}")
        else:
            print(f"⚠️  Data file not found at {data_file_path}")
            print("   Make sure dump1090-fa is running and the data file exists")
    except Exception as e:
        print(f"❌ Data connection test failed: {e}")
        print("   The application will continue but may not function properly")

    print("\nStarting application...")
    print("Press Ctrl+C to stop")

    try:
        # Start unified monitoring loop
        if monitor:
            monitor.start_monitoring(interval=5)  # Single interval for all updates
            print("Monitoring started...")

        # Main application loop - just keep alive
        import time

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cleanup
        if monitor:
            monitor.stop_monitoring()
        if lcd_controller:
            lcd_controller.cleanup()
        if oled_controller:
            oled_controller.cleanup()

    print("PiPlane Tracker stopped.")


if __name__ == "__main__":
    main()
