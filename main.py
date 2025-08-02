#!/usr/bin/env python3
"""
Main Airplane Tracker Application
Console-based airplane tracker with LCD/OLED display and alert system
"""

import sys
import os
import signal
from datetime import datetime
from config import get_config

# Import our modules
from aircraft_data import read_aircraft_data
from alert_system import AirplaneAlertSystem
from lcd_controller import AirplaneLCDController
from oled_controller import AirplaneOLEDController

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\nShutting down airplane tracker...')
    sys.exit(0)

def main():
    """Main application entry point"""
    print("=" * 60)
    print("🛩️  Airplane Tracker System v1.0")
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
    alert_sound_path = config.get_sound_file()
    
    # Check for command line arguments
    for arg in sys.argv[1:]:
        if arg == "--no-lcd":
            lcd_enabled = False
        elif arg == "--no-oled":
            oled_enabled = False
        elif arg == "--oled-only":
            lcd_enabled = False
            oled_enabled = True
        elif arg.startswith("--sound="):
            alert_sound_path = arg.split("=", 1)[1]
        elif arg in ["--help", "-h"]:
            print("Usage: python3 main.py [options]")
            print("\nOptions:")
            print("  --no-lcd          Disable LCD display")
            print("  --no-oled         Disable OLED display")
            print("  --oled-only       Use OLED only (disable LCD)")
            print("  --sound=PATH      Path to alert sound file")
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
    
    # Initialize components
    print("Initializing components...")
    
    # Initialize alert system
    try:
        alert_system = AirplaneAlertSystem(alert_sound_path)
        print("✅ Alert system initialized")
    except Exception as e:
        print(f"⚠️  Alert system initialization failed: {e}")
        alert_system = None
    
    # Initialize LCD controller (if enabled)
    lcd_controller = None
    if lcd_enabled:
        try:
            lcd_controller = AirplaneLCDController()
            lcd_controller.display_startup_message()
            print("✅ LCD controller initialized")
        except Exception as e:
            print(f"⚠️  LCD controller initialization failed: {e}")
            lcd_controller = None
    
    # Initialize OLED controller (if enabled)
    oled_controller = None
    if oled_enabled:
        try:
            oled_controller = AirplaneOLEDController()
            print("✅ OLED controller initialized")
        except Exception as e:
            print(f"⚠️  OLED controller initialization failed: {e}")
            oled_controller = None
    
    # Test initial data connection
    print("\nTesting data connection...")
    try:
        test_data = read_aircraft_data()
        if test_data:
            aircraft_count = len(test_data.get('aircraft', []))
            print(f"✅ Connected to dump1090-fa - {aircraft_count} aircraft currently detected")
        else:
            print("⚠️  No data available from dump1090-fa")
            print("   Make sure dump1090-fa is running and the data file exists")
    except Exception as e:
        print(f"❌ Data connection test failed: {e}")
        print("   The application will continue but may not function properly")
    
    print("\nStarting application...")
    
    # Run in console mode
    print("📺 Running in console mode...")
    print("Press Ctrl+C to stop")
    
    try:
        # Start alert system monitoring
        if alert_system:
            alert_system.start_monitoring(read_aircraft_data, 5)
            print("Alert monitoring started")
        
        # Start LCD cycling
        if lcd_controller:
            lcd_controller.start_cycling_display(read_aircraft_data, 5)
            print("LCD display started")
        
        # Start OLED cycling
        if oled_controller:
            oled_controller.start_cycling_display(read_aircraft_data, 3)
            print("OLED display started")
        
        # Main console loop
        import time
        while True:
            aircraft_data = read_aircraft_data()
            if aircraft_data and 'aircraft' in aircraft_data:
                aircraft_count = len(aircraft_data['aircraft'])
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] Aircraft detected: {aircraft_count}")
                
                # Show aircraft with callsigns
                with_callsign = [a for a in aircraft_data['aircraft'] 
                               if a.get('flight', '').strip()]
                if with_callsign:
                    print(f"  Aircraft with callsigns: {len(with_callsign)}")
                    for aircraft in with_callsign[:5]:  # Show first 5
                        flight = aircraft.get('flight', '').strip()
                        alt = aircraft.get('alt_baro') or aircraft.get('alt_geom')
                        alt_str = f"{alt}ft" if alt else "N/A"
                        print(f"    {flight} - {alt_str}")
            
            time.sleep(10)  # Update every 10 seconds in console mode
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cleanup
        if alert_system:
            alert_system.stop_monitoring()
        if lcd_controller:
            lcd_controller.cleanup()
        if oled_controller:
            oled_controller.cleanup()
    
    print("Airplane tracker stopped.")

if __name__ == "__main__":
    main()
