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

import os
import sys
import time
from datetime import datetime
from config import get_config

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.get_country_from_icao import get_country_from_icao
from common.get_country_name import get_country_name


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
            return True
        return False

    def display_startup_message(self):
        """Display startup message"""
        if not self.show_display():
            return

        self.draw_text("PiPlane Tracker", 0, 0, self.font_medium)
        self.draw_text("Initializing...", 0, 12, self.font_small)
        self.draw_text(
            f"v1.0 {datetime.now().strftime('%H:%M')}", 0, 22, self.font_small
        )

        self.display.image(self.image)
        self.display.show()
        time.sleep(2)

    def display_idle_message(self):
        """Display idle message while monitoring running and no aircraft are detected"""
        if not self.show_display():
            return

        self.draw_text("PiPlane Tracker", 0, 0, self.font_medium)
        self.draw_text("Monitoring for new aircrafts...", 0, 12, self.font_small)

        self.display.image(self.image)
        self.display.show()

    def display_new_aircraft_detected(self, interval=2):
        """Display message when new aircraft is detected"""
        if not self.show_display():
            return

        self.draw_text("PiPlaneTracker", 0, 0, self.font_medium)
        self.draw_text("New aircraft detected!", 0, 12, self.font_small)

        self.display.image(self.image)
        self.display.show()
        time.sleep(interval)

    def display_aircraft_info(self, aircraft, interval=2):
        """
        Display individual aircraft information

        Args:
            aircraft (dict): Aircraft data
            page_info (str): Page information (e.g., "1/3")
        """
        if not self.show_display():
            return

        flight = aircraft.get("flight", "").strip()
        hex_code = aircraft.get("hex", "")
        altitude = aircraft.get("alt_baro") or aircraft.get("alt_geom")
        speed = aircraft.get("gs")
        country_code = get_country_from_icao(hex_code)
        country = get_country_name(country_code)
        aircraft_type = aircraft.get("aircraft_type")

        # Line 1: Flight/Callsign or ICAO
        if flight:
            self.draw_text(f"✈ {flight}", 0, 0, self.font_medium)
        else:
            self.draw_text(f"✈ {hex_code[:8]}", 0, 0, self.font_small)

        # Line 2: Country
        country_text = f"{country}" if country else ""
        self.draw_text(f"Country: {country_text}", 0, 11, self.font_small)

        # Line 3: Altitude and Speed
        alt_text = f"{altitude}ft" if altitude else "N/A"
        speed_text = f"{speed}kt" if speed else "N/A"

        self.draw_text(f"Alt: {alt_text}", 0, 22, self.font_small)
        self.draw_text(f"Spd: {speed_text}", 64, 22, self.font_small)

        # Line 3: Aircraft Type and Registration
        print(aircraft_type)
        if aircraft_type:
            self.draw_text(f"Aircraft: {aircraft_type}", 0, 33, self.font_small)

        self.display.image(self.image)
        self.display.show()
        time.sleep(interval)

    def display_error(self, error_msg):
        """
        Display error message

        Args:
            error_msg (str): Error message to display
        """
        if not self.show_display():
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
