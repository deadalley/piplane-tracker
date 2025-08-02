#!/usr/bin/env python3
# pyright: reportPossiblyUnboundVariable=false, reportMissingImports=false, reportOptionalMemberAccess=false
"""
OLED Display Controller for PiPlane Tracker
Uses 0.91 inch I2C OLED display (typically SSD1306 128x32)
"""

try:
    import board
    import busio
    from adafruit_ssd1306 import SSD1306_I2C
    from PIL import Image, ImageDraw, ImageFont

    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print(
        "Warning: OLED libraries not available. Install adafruit-circuitpython-ssd1306 and pillow"
    )

import time
from datetime import datetime
import threading
from config import get_config


class PiPlaneOLEDController:
    def __init__(self, width=None, height=None, i2c_address=None):
        """
        Initialize OLED controller for 0.91 inch display

        Args:
            width (int): Display width in pixels (uses config if None)
            height (int): Display height in pixels (uses config if None)
            i2c_address (int): I2C address of the display (uses config if None)
        """
        # Get configuration
        config = get_config()

        self.width = width or config.get_oled_width()
        self.height = height or config.get_oled_height()
        i2c_address = i2c_address or config.get_oled_i2c_address()

        self.display = None
        self.display_active = False
        self.current_page = 0
        self.total_pages = 0
        self.aircraft_data = []

        if OLED_AVAILABLE:
            try:
                # Initialize I2C
                i2c = busio.I2C(board.SCL, board.SDA)

                # Initialize display
                self.display = SSD1306_I2C(
                    self.width, self.height, i2c, addr=i2c_address
                )

                # Clear display
                self.display.fill(0)
                self.display.show()

                # Create image for drawing
                self.image = Image.new("1", (self.width, self.height))
                self.draw = ImageDraw.Draw(self.image)

                # Try to load a font (fallback to default if not available)
                try:
                    self.font_small = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8
                    )
                    self.font_medium = ImageFont.truetype(
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
                    )
                except:
                    self.font_small = ImageFont.load_default()
                    self.font_medium = ImageFont.load_default()

                self.display_startup_message()
                print("OLED initialized successfully")

            except Exception as e:
                self.display = None
                raise e

    def clear_display(self):
        if self.display:
            self.display.fill(0)
            self.display.show()

    def draw_text(self, text, x, y, font=None):
        if not font:
            font = self.font_small
        self.draw.text((x, y), text, font=font, fill=255)

    def show_display(self):
        """Update the physical display"""
        if self.display:
            # Clear the image
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def display_startup_message(self):
        """Display startup message"""
        if not self.show_display():
            print("OLED: PiPlane Tracker | Starting...")
            return

        self.draw_text("PiPlane Tracker", 0, 0, self.font_medium)
        self.draw_text("Initializing...", 0, 12, self.font_small)
        self.draw_text(
            f"v1.0 {datetime.now().strftime('%H:%M')}", 0, 22, self.font_small
        )

        self.display.image(self.image)
        self.display.show()
        time.sleep(2)

    def display_aircraft_count(self, total_count, new_count=0):
        """
        Display aircraft count summary

        Args:
            total_count (int): Total aircraft detected
            new_count (int): New aircraft count
        """
        if not self.show_display():
            print(f"OLED: Aircraft: {total_count} | New: {new_count}")
            return

        # Title
        self.draw_text("AIRCRAFT TRACKER", 0, 0, self.font_small)

        # Aircraft count
        self.draw_text(f"Total: {total_count}", 0, 10, self.font_medium)

        # New aircraft (if any)
        if new_count > 0:
            self.draw_text(f"NEW: {new_count}!", 70, 10, self.font_medium)

        # Time
        time_str = datetime.now().strftime("%H:%M:%S")
        self.draw_text(f"Time: {time_str}", 0, 22, self.font_small)

        self.display.image(self.image)
        self.display.show()

    def display_aircraft_info(self, aircraft, page_info=""):
        """
        Display individual aircraft information

        Args:
            aircraft (dict): Aircraft data
            page_info (str): Page information (e.g., "1/3")
        """
        if not self.show_display():
            flight = aircraft.get("flight", "").strip()
            hex_code = aircraft.get("hex", "")
            alt = aircraft.get("alt_baro") or aircraft.get("alt_geom")
            speed = aircraft.get("gs")
            print(f"OLED: {flight or hex_code[:6]} | {alt}ft {speed}kt | {page_info}")
            return

        flight = aircraft.get("flight", "").strip()
        hex_code = aircraft.get("hex", "")

        # Line 1: Flight/Callsign or ICAO
        if flight:
            self.draw_text(f"✈ {flight}", 0, 0, self.font_medium)
        else:
            self.draw_text(f"✈ {hex_code[:8]}", 0, 0, self.font_small)

        # Page indicator
        if page_info:
            page_width = len(page_info) * 6
            self.draw_text(page_info, self.width - page_width, 0, self.font_small)

        # Line 2: Altitude and Speed
        altitude = aircraft.get("alt_baro") or aircraft.get("alt_geom")
        speed = aircraft.get("gs")

        alt_text = f"{altitude}ft" if altitude else "N/A"
        speed_text = f"{speed}kt" if speed else "N/A"

        self.draw_text(f"Alt: {alt_text}", 0, 11, self.font_small)
        self.draw_text(f"Spd: {speed_text}", 64, 11, self.font_small)

        # Line 3: Heading and Position status
        track = aircraft.get("track")
        lat = aircraft.get("lat")
        lon = aircraft.get("lon")

        if track is not None:
            self.draw_text(f"Hdg: {int(track)}°", 0, 22, self.font_small)
        else:
            self.draw_text("Hdg: N/A", 0, 22, self.font_small)

        # Position indicator
        if lat and lon:
            self.draw_text("GPS✓", 88, 22, self.font_small)
        else:
            self.draw_text("GPS✗", 88, 22, self.font_small)

        self.display.image(self.image)
        self.display.show()

    def display_alert(self, new_aircraft_count, flight_name=""):
        """
        Display alert for new aircraft

        Args:
            new_aircraft_count (int): Number of new aircraft
            flight_name (str): Flight name if available
        """
        if not self.show_display():
            print(f"OLED: 🚨 ALERT! New: {new_aircraft_count} ({flight_name})")
            return

        # Alert header
        self.draw_text("🚨 AIRCRAFT ALERT 🚨", 0, 0, self.font_small)

        # New aircraft count
        self.draw_text(f"New Aircraft: {new_aircraft_count}", 0, 11, self.font_medium)

        # Flight name if available
        if flight_name:
            flight_display = flight_name[:16]  # Truncate if too long
            self.draw_text(f"Flight: {flight_display}", 0, 22, self.font_small)
        else:
            self.draw_text("Unknown flight", 0, 22, self.font_small)

        self.display.image(self.image)
        self.display.show()
        time.sleep(3)  # Show alert for 3 seconds

    def display_no_aircraft(self):
        """Display message when no aircraft are detected"""
        if not self.show_display():
            print(f"OLED: No Aircraft | {datetime.now().strftime('%H:%M:%S')}")
            return

        self.draw_text("AIRPLANE TRACKER", 0, 0, self.font_small)
        self.draw_text("No Aircraft", 0, 11, self.font_medium)
        self.draw_text(
            f"Scanning... {datetime.now().strftime('%H:%M:%S')}", 0, 22, self.font_small
        )

        self.display.image(self.image)
        self.display.show()

    def display_error(self, error_msg):
        """
        Display error message

        Args:
            error_msg (str): Error message to display
        """
        if not self.show_display():
            print(f"OLED: ERROR - {error_msg}")
            return

        self.draw_text("ERROR", 0, 0, self.font_medium)

        # Split long error messages
        if len(error_msg) > 20:
            self.draw_text(error_msg[:20], 0, 11, self.font_small)
            if len(error_msg) > 20:
                self.draw_text(error_msg[20:40], 0, 22, self.font_small)
        else:
            self.draw_text(error_msg, 0, 11, self.font_small)

        self.display.image(self.image)
        self.display.show()

    def display_system_info(self):
        """Display system information"""
        if not self.show_display():
            print("OLED: System Info")
            return

        self.draw_text("SYSTEM INFO", 0, 0, self.font_small)
        self.draw_text(
            f"Time: {datetime.now().strftime('%H:%M:%S')}", 0, 10, self.font_small
        )
        self.draw_text(
            f"Date: {datetime.now().strftime('%m/%d')}", 0, 20, self.font_small
        )

        self.display.image(self.image)
        self.display.show()

    def cleanup(self):
        """Cleanup OLED resources"""
        if self.display:
            try:
                if not self.show_display():
                    return

                self.draw_text("PiPlane Tracker", 0, 5, self.font_medium)
                self.draw_text("Shutting down...", 0, 20, self.font_small)

                self.display.image(self.image)
                self.display.show()
                time.sleep(1)
                self.clear_display()
            except Exception as e:
                print(f"Error during OLED cleanup: {e}")
