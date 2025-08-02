#!/usr/bin/env python3
"""
LCD Display Controller for Airplane Tracker
Uses rpi-lcd to display airplane information on LCD screen
"""

try:
    from rpi_lcd import LCD
    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    print("Warning: rpi-lcd not available. LCD functionality disabled.")

import time
from datetime import datetime
from typing import List, Dict
import threading

class AirplaneLCDController:
    def __init__(self, lcd_pins=None):
        """
        Initialize LCD controller
        
        Args:
            lcd_pins (dict): LCD pin configuration (optional)
                Example: {'rs': 26, 'enable': 19, 'd4': 13, 'd5': 6, 'd6': 5, 'd7': 11}
        """
        self.lcd = None
        self.display_active = False
        self.current_display_data = []
        self.display_index = 0
        self.last_update = None
        
        if LCD_AVAILABLE:
            try:
                self.lcd = LCD()
                self.lcd.clear()
                self.lcd.text("Airplane Tracker", 1)
                self.lcd.text("Initializing...", 2)
                print("LCD initialized successfully")
                time.sleep(2)
            except Exception as e:
                print(f"Failed to initialize LCD: {e}")
                self.lcd = None
        else:
            print("LCD not available - running in simulation mode")
    
    def clear_display(self):
        """Clear the LCD display"""
        if self.lcd:
            self.lcd.clear()
    
    def display_text(self, line1, line2=""):
        """
        Display text on LCD
        
        Args:
            line1 (str): Text for first line
            line2 (str): Text for second line
        """
        if self.lcd:
            try:
                self.lcd.clear()
                self.lcd.text(line1[:16], 1)  # LCD is typically 16 characters wide
                if line2:
                    self.lcd.text(line2[:16], 2)
            except Exception as e:
                print(f"Error displaying on LCD: {e}")
        else:
            # Simulate LCD output to console
            print("=" * 18)
            print(f"| {line1:<16} |")
            print(f"| {line2:<16} |")
            print("=" * 18)
    
    def display_startup_message(self):
        """Display startup message"""
        self.display_text("Airplane Tracker", "Starting up...")
        time.sleep(2)
    
    def display_aircraft_count(self, total_count, new_count=0):
        """
        Display aircraft count
        
        Args:
            total_count (int): Total aircraft detected
            new_count (int): New aircraft count (optional)
        """
        line1 = f"Aircraft: {total_count}"
        line2 = f"New: {new_count}" if new_count > 0 else f"Time: {datetime.now().strftime('%H:%M')}"
        self.display_text(line1, line2)
    
    def display_aircraft_info(self, aircraft):
        """
        Display individual aircraft information
        
        Args:
            aircraft (dict): Aircraft data
        """
        flight = aircraft.get('flight', '').strip()
        hex_code = aircraft.get('hex', '')
        
        if flight:
            line1 = flight[:16]
        else:
            line1 = f"ICAO: {hex_code[:10]}"
        
        # Display altitude and speed if available
        altitude = aircraft.get('alt_baro') or aircraft.get('alt_geom')
        speed = aircraft.get('gs')
        
        if altitude and speed:
            line2 = f"{altitude}ft {speed}kt"
        elif altitude:
            line2 = f"Alt: {altitude}ft"
        elif speed:
            line2 = f"Speed: {speed}kt"
        else:
            line2 = "No alt/speed"
        
        self.display_text(line1, line2[:16])
    
    def display_alert(self, new_aircraft_count):
        """
        Display alert for new aircraft
        
        Args:
            new_aircraft_count (int): Number of new aircraft
        """
        self.display_text("** ALERT **", f"New: {new_aircraft_count}")
        time.sleep(3)  # Show alert for 3 seconds
    
    def display_no_aircraft(self):
        """Display message when no aircraft are detected"""
        self.display_text("No Aircraft", f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    def display_error(self, error_msg):
        """
        Display error message
        
        Args:
            error_msg (str): Error message to display
        """
        self.display_text("ERROR", error_msg[:16])
    
    def start_cycling_display(self, aircraft_data_func, interval=5):
        """
        Start cycling through aircraft information on display
        
        Args:
            aircraft_data_func: Function that returns current aircraft data
            interval (int): Display cycle interval in seconds
        """
        self.display_active = True
        
        def display_loop():
            while self.display_active:
                try:
                    aircraft_data = aircraft_data_func()
                    
                    if not aircraft_data or 'aircraft' not in aircraft_data:
                        self.display_error("No data")
                        time.sleep(interval)
                        continue
                    
                    aircraft_list = aircraft_data['aircraft']
                    
                    if not aircraft_list:
                        self.display_no_aircraft()
                        time.sleep(interval)
                        continue
                    
                    # First show the count
                    self.display_aircraft_count(len(aircraft_list))
                    time.sleep(interval)
                    
                    # Then cycle through individual aircraft
                    for aircraft in aircraft_list:
                        if not self.display_active:
                            break
                        self.display_aircraft_info(aircraft)
                        time.sleep(interval)
                    
                except Exception as e:
                    print(f"Error in LCD display loop: {e}")
                    self.display_error("Display error")
                    time.sleep(interval)
        
        display_thread = threading.Thread(target=display_loop, daemon=True)
        display_thread.start()
    
    def stop_cycling_display(self):
        """Stop the cycling display"""
        self.display_active = False
        self.clear_display()
    
    def log_aircraft_event(self, event_type, aircraft_data):
        """
        Log aircraft events to console (and potentially to file later)
        
        Args:
            event_type (str): Type of event (e.g., 'NEW', 'DEPARTED')
            aircraft_data (dict): Aircraft information
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        flight = aircraft_data.get('flight', '').strip()
        hex_code = aircraft_data.get('hex', 'Unknown')
        
        log_entry = f"[{timestamp}] {event_type}: {flight if flight else 'Unknown'} (ICAO: {hex_code})"
        print(log_entry)
        
        # You could also write to a log file here
        # with open('aircraft_log.txt', 'a') as f:
        #     f.write(log_entry + '\n')
    
    def cleanup(self):
        """Cleanup LCD resources"""
        self.stop_cycling_display()
        if self.lcd:
            try:
                self.lcd.clear()
                self.lcd.text("Airplane Tracker", 1)
                self.lcd.text("Stopped", 2)
                time.sleep(1)
                self.lcd.clear()
            except Exception as e:
                print(f"Error during LCD cleanup: {e}")

# Test function for LCD
def test_lcd():
    """Test the LCD functionality"""
    lcd_controller = AirplaneLCDController()
    
    # Test basic display
    lcd_controller.display_startup_message()
    
    # Test aircraft count display
    lcd_controller.display_aircraft_count(5, 2)
    time.sleep(3)
    
    # Test individual aircraft display
    test_aircraft = {
        'flight': 'UAL123',
        'hex': 'A12345',
        'alt_baro': 35000,
        'gs': 450
    }
    lcd_controller.display_aircraft_info(test_aircraft)
    time.sleep(3)
    
    # Test alert
    lcd_controller.display_alert(2)
    
    # Test no aircraft
    lcd_controller.display_no_aircraft()
    time.sleep(3)
    
    lcd_controller.cleanup()

if __name__ == "__main__":
    test_lcd()
