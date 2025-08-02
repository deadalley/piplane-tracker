#!/usr/bin/env python3
"""
Main PiPlane Tracker Application
"""

import sys
import signal
import os

try:
    import termios
    import tty

    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False
from datetime import datetime
from config import get_config

from monitor import PiPlaneMonitor
from lcd_controller import PiPlaneLCDController
from oled_controller import PiPlaneOLEDController


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down PiPlane Tracker...")
    sys.exit(0)


def show_menu():
    """Display the main menu"""
    print("\n" + "=" * 60)
    print("🛩️  PiPlane Tracker v1.0")
    print("=" * 60)
    print("  [L] List - Show all known aircraft history")
    print("  [M] Monitor - Start real-time aircraft monitoring")
    print("  [Q] Quit - Exit the application")
    print()
    print("Press ESC anytime during monitoring to return to this menu")
    print("=" * 60)


def get_user_choice():
    """Get user menu choice"""
    while True:
        choice = input("\nEnter your choice (L/M/Q): ").strip().upper()
        if choice in ["L", "M", "Q"]:
            return choice
        print("Invalid choice. Please enter L, M, or Q.")


def initialize_displays():
    """Initialize LCD and OLED controllers"""
    config = get_config()
    lcd_controller = None
    oled_controller = None

    # Initialize LCD controller (if enabled)
    if config.is_lcd_enabled():
        try:
            lcd_controller = PiPlaneLCDController()
            print("✅ LCD controller initialized")
        except Exception as e:
            print(f"⚠️  LCD controller initialization failed: {e}")
            lcd_controller = None

    # Initialize OLED controller (if enabled)
    if config.is_oled_enabled():
        try:
            oled_controller = PiPlaneOLEDController()
            print("✅ OLED controller initialized")
        except Exception as e:
            print(f"⚠️  OLED controller initialization failed: {e}")
            oled_controller = None

    return lcd_controller, oled_controller


def test_data_connection():
    """Test the data file connection"""
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
    """Main application entry point with interactive menu"""
    print("=" * 60)
    print("🛩️  PiPlane Tracker v1.0")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check for help argument
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\nUsage: python3 main.py [options]")
        print("\nOptions:")
        print("  --help, -h        Show this help message")
        print("\nConfiguration:")
        print("  - Edit the 'config' file to change default settings")
        print("  - Data source, display options, and more can be configured")
        print("\nInteractive Mode:")
        print("  - Choose between listing known aircraft or monitoring")
        print("  - Press ESC during monitoring to return to menu")
        return

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Load configuration
    config = get_config()
    print(f"📁 Data source: {config.get_data_source_path()}")

    # Test data connection
    test_data_connection()

    # Initialize displays
    print("\n🔧 Initializing displays...")
    lcd_controller, oled_controller = initialize_displays()

    # Initialize monitor system
    try:
        monitor = PiPlaneMonitor(
            lcd_controller=lcd_controller, oled_controller=oled_controller
        )
        print("✅ Monitor system initialized")
    except Exception as e:
        print(f"⚠️  Monitor system initialization failed: {e}")
        monitor = None
        return

    # Main interactive loop
    try:
        while True:
            show_menu()
            choice = get_user_choice()

            if choice == "L":
                monitor.list_known_aircraft()
                input("\nPress Enter to continue...")

            elif choice == "M":
                print("\n🔍 Starting aircraft monitoring...")
                print("-" * 60)

                exit_requested = monitor.start_monitoring(interval=5)

                if not exit_requested:
                    # If we get here, it was likely a Ctrl+C
                    break

            elif choice == "Q":
                print("Shutting down PiPlane Tracker...")
                break

    except KeyboardInterrupt:
        print("\n\n🛑 PiPlane Tracker interrupted by user")
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if monitor:
            monitor.stop_monitoring()
        if lcd_controller:
            lcd_controller.cleanup()
        if oled_controller:
            oled_controller.cleanup()
        print("✅ Cleanup complete")

    print("\nPiPlane Tracker stopped")


if __name__ == "__main__":
    main()
