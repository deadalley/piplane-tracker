#!/usr/bin/env python3
# pyright: reportPossiblyUnboundVariable=false, reportMissingImports=false
"""
LCD Display Controller for PiPlane Tracker
Uses rpi-lcd to display airplane information on LCD screen
"""

try:
    from rpi_lcd import LCD

    LCD_AVAILABLE = True
except ImportError:
    LCD_AVAILABLE = False
    print("Warning: rpi-lcd not available. LCD functionality disabled.")

import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.get_country_from_icao import get_country_from_icao


class PiPlaneLCDController:
    def __init__(self):
        self.lcd = None

        if LCD_AVAILABLE:
            try:
                self.lcd = LCD()
                self.lcd.clear()
                self.display_startup_message()
                time.sleep(2)
            except Exception as e:
                self.lcd = None
                raise e

    def display_text(self, line1, line2=""):
        if self.lcd:
            try:
                self.lcd.clear()
                self.lcd.text(line1[:16], 1)  # LCD is typically 16 characters wide
                if line2:
                    self.lcd.text(line2[:16], 2)
            except Exception as e:
                print(f"Error displaying on LCD: {e}")

    def display_startup_message(self):
        """Display startup message"""
        self.display_text("PiPlane Tracker", "Initializing...")
        time.sleep(2)

    def display_idle_message(self):
        """Display idle message while monitoring running and no aircraft are detected"""
        self.display_text("PiPlane Tracker", "Monitoring...")

    def display_new_aircraft_detected(self, interval=2):
        """Display message when new aircraft is detected"""
        self.display_text("New aircraft", "detected!")
        time.sleep(interval)

    def display_aircraft_info(self, aircraft, interval=2):
        """
        Display individual aircraft information

        Args:
            aircraft (dict): Aircraft data
        """
        flight = aircraft.get("flight", "").strip()
        hex_code = aircraft.get("hex", "")
        country = get_country_from_icao(hex_code)

        if flight:
            line1 = flight[:16]
        else:
            line1 = hex_code[:16].upper()

        line1 += f" [{country}]" if country else ""

        # Display altitude and speed if available
        altitude = aircraft.get("alt_baro") or aircraft.get("alt_geom")
        speed = aircraft.get("gs")

        if altitude and speed:
            line2 = f"{altitude}ft {speed}kt"
        elif altitude:
            line2 = f"Alt: {altitude}ft"
        elif speed:
            line2 = f"Speed: {speed}kt"
        else:
            line2 = "No alt/speed"

        self.display_text(line1, line2[:16])
        time.sleep(interval)

        aircraft_type = aircraft.get("aircraft_type")

        if aircraft_type:
            self.display_text(line1, f"{aircraft_type[:16]}")
            time.sleep(interval)

    def display_error(self, error_msg):
        self.display_text("ERROR", error_msg[:16])

    def cleanup(self):
        """Cleanup LCD resources"""
        if self.lcd:
            try:
                self.lcd.clear()
                self.lcd.text("PiPlane Tracker", 1)
                self.lcd.text("Shutting down...", 2)
                time.sleep(1)
                self.lcd.clear()
                self.lcd.backlight(False)
            except Exception as e:
                print(f"Error during LCD cleanup: {e}")
