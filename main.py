#!/usr/bin/env python3
"""
Main PiPlane Tracker Application
"""

import sys
import signal
import os
import time
import threading

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
    print("\nShutting down airplane tracker...")
    sys.exit(0)


def get_single_char():
    """Get a single character from stdin"""
    if TERMIOS_AVAILABLE:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char
    else:
        # Fallback for systems without termios
        return input().strip()


def keyboard_monitor(monitor):
    """Monitor for ESC key press during monitoring"""
    print("(Keyboard monitoring active - press ESC to return to menu)")
    while monitor.running and not monitor.exit_requested:
        try:
            if TERMIOS_AVAILABLE:
                char = get_single_char()
                if ord(char) == 27:  # ESC key
                    print("\n🔙 ESC pressed - returning to menu...")
                    monitor.request_exit()
                    break
            else:
                # Fallback: check every second
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.request_exit()
            break
        except:
            break


def show_menu():
    """Display the main menu"""
    print("\n" + "=" * 60)
    print("🛩️  PiPlane Tracker v1.0 - Main Menu")
    print("=" * 60)
    print("Choose an option:")
    print()
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


def initialize_controllers():
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
            return False
    except Exception as e:
        print(f"❌ Data connection test failed: {e}")
        print("   The application will continue but may not function properly")
        return False


def main():
    """Main application entry point with interactive menu"""
    print("=" * 60)
    print("🛩️  PiPlane Tracker v1.0")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load configuration
    config = get_config()
    print(f"📁 Data source: {config.get_data_source_path()}")

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

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

    # Initialize controllers
    print("\n🔧 Initializing controllers...")
    lcd_controller, oled_controller = initialize_controllers()

    # Test data connection
    data_available = test_data_connection()

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
                # List known aircraft
                monitor.list_known_aircraft()
                input("\nPress Enter to continue...")

            elif choice == "M":
                # Start monitoring
                if not data_available:
                    print(
                        "\n⚠️  Warning: Data file not available. Monitoring may not work properly."
                    )
                    cont = input("Continue anyway? (y/N): ").strip().lower()
                    if cont != "y":
                        continue

                print("\n🔍 Starting aircraft monitoring...")
                if TERMIOS_AVAILABLE:
                    print("💡 Press ESC to return to menu, or Ctrl+C to quit")
                else:
                    print("💡 Press Ctrl+C to return to menu or quit")
                print("-" * 60)

                # Start keyboard monitoring thread if available
                keyboard_thread = None
                if TERMIOS_AVAILABLE:
                    keyboard_thread = threading.Thread(
                        target=keyboard_monitor, args=(monitor,), daemon=True
                    )
                    keyboard_thread.start()

                # Start monitoring and wait for ESC or interrupt
                exit_requested = monitor.start_monitoring(interval=5)

                if not exit_requested:
                    # If we get here, it was likely a Ctrl+C
                    break

            elif choice == "Q":
                # Quit
                print("\n👋 Goodbye!")
                break

    except KeyboardInterrupt:
        print("\n\n🛑 Application interrupted by user")
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

    print("\nPiPlane Tracker stopped.")


if __name__ == "__main__":
    main()
