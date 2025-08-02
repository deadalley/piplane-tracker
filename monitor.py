#!/usr/bin/env python3
"""
PiPlane Tracker Monitor
Tracks new airplanes entering range and provides alerts
"""

import time
from datetime import datetime
from typing import Set, Dict, List, Optional
import threading
import json
import os
from config import get_config


class PiPlaneMonitor:
    def __init__(
        self, file_path: Optional[str] = None, lcd_controller=None, oled_controller=None
    ):
        """
        Initialize the alert system

        Args:
            file_path (str, optional): Path to the aircraft.json file.
                                     If None, uses path from configuration.
            lcd_controller: LCD controller instance
            oled_controller: OLED controller instance
        """
        self.known_aircraft: Set[str] = set()
        self.aircraft_history: Dict[str, dict] = {}
        self.alert_callbacks = []
        self.running = False

        # Display controllers
        self.lcd_controller = lcd_controller
        self.oled_controller = oled_controller
        self.console_enabled = True

        # Set up data source path
        if file_path is None:
            config = get_config()
            self.file_path = config.get_data_source_path()
        else:
            self.file_path = file_path

    def set_console_enabled(self, enabled: bool):
        """Enable or disable console output"""
        self.console_enabled = enabled

    def read_aircraft_data(self) -> Optional[Dict]:
        """
        Read aircraft data from the dump1090-fa JSON file

        Returns:
            dict: Aircraft data or None if file cannot be read
        """
        try:
            if not os.path.exists(self.file_path):
                print(f"Error: Aircraft data file not found at {self.file_path}")
                print("Make sure dump1090-fa is running and the file path is correct.")
                print("You can change the file path in the 'config' file")
                return None

            with open(self.file_path, "r") as file:
                data = json.load(file)
                return data
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in {self.file_path}: {e}")
            return None
        except PermissionError:
            print(f"Error: Permission denied reading {self.file_path}")
            return None
        except Exception as e:
            print(f"Error reading aircraft data: {e}")
            return None

    def add_alert_callback(self, callback):
        """Add a callback function to be called when new aircraft are detected"""
        self.alert_callbacks.append(callback)

    def _trigger_alerts(self, new_aircraft: List[dict]):
        """Trigger all registered alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(new_aircraft)
            except Exception as e:
                print(f"Error in alert callback: {e}")

    def check_for_new_aircraft(self, aircraft_data: dict) -> List[dict]:
        """
        Check for new aircraft and return list of new ones

        Args:
            aircraft_data (dict): Aircraft data from dump1090-fa

        Returns:
            List[dict]: List of new aircraft detected
        """
        if not aircraft_data or "aircraft" not in aircraft_data:
            return []

        current_aircraft = set()
        new_aircraft = []

        for aircraft in aircraft_data["aircraft"]:
            hex_code = aircraft.get("hex")
            if not hex_code:
                continue

            current_aircraft.add(hex_code)

            # Check if this is a new aircraft
            if hex_code not in self.known_aircraft:
                # Only alert for aircraft with flight names/callsigns
                flight = aircraft.get("flight", "").strip()
                if flight:  # Only add to new_aircraft list if it has a flight name
                    new_aircraft.append(aircraft)
                self.known_aircraft.add(hex_code)

                # Store aircraft info in history
                self.aircraft_history[hex_code] = {
                    "first_seen": datetime.now(),
                    "last_seen": datetime.now(),
                    "flight": aircraft.get("flight", "").strip(),
                    "positions": [],
                }

                if aircraft.get("lat") and aircraft.get("lon"):
                    self.aircraft_history[hex_code]["positions"].append(
                        {
                            "lat": aircraft["lat"],
                            "lon": aircraft["lon"],
                            "timestamp": datetime.now(),
                        }
                    )
            else:
                # Update last seen time
                if hex_code in self.aircraft_history:
                    self.aircraft_history[hex_code]["last_seen"] = datetime.now()

                    # Add position if available
                    if aircraft.get("lat") and aircraft.get("lon"):
                        self.aircraft_history[hex_code]["positions"].append(
                            {
                                "lat": aircraft["lat"],
                                "lon": aircraft["lon"],
                                "timestamp": datetime.now(),
                            }
                        )

        # Remove aircraft that are no longer in range (haven't been seen for 5 minutes)
        current_time = datetime.now()
        aircraft_to_remove = []

        for hex_code in self.aircraft_history:
            if hex_code not in current_aircraft:
                last_seen = self.aircraft_history[hex_code]["last_seen"]
                if (current_time - last_seen).total_seconds() > 300:  # 5 minutes
                    aircraft_to_remove.append(hex_code)

        for hex_code in aircraft_to_remove:
            self.known_aircraft.discard(hex_code)
            del self.aircraft_history[hex_code]

        # Trigger alerts for new aircraft
        if new_aircraft:
            self._trigger_alerts(new_aircraft)

            # Print alert to console
            print(f"\n🚨 ALERT: {len(new_aircraft)} new aircraft detected!")
            for aircraft in new_aircraft:
                flight = aircraft.get("flight", "").strip()
                hex_code = aircraft.get("hex", "Unknown")
                print(
                    f"  - {flight if flight else 'Unknown Flight'} (ICAO: {hex_code})"
                )

        return new_aircraft

    def get_aircraft_summary(self) -> dict:
        """Get summary of tracked aircraft"""
        return {
            "total_tracked": len(self.known_aircraft),
            "aircraft_history": self.aircraft_history.copy(),
        }

    def start_monitoring(self, interval=5):
        """
        Start monitoring for new aircraft and updating displays

        Args:
            interval (int): Update interval in seconds for all components
        """
        self.running = True

        lcd_display_index = 0
        oled_display_index = 0

        def monitor_loop():
            nonlocal lcd_display_index, oled_display_index

            while self.running:
                try:
                    aircraft_data = self.read_aircraft_data()

                    if aircraft_data:
                        # Always check for new aircraft
                        self.check_for_new_aircraft(aircraft_data)

                        aircraft_list = aircraft_data.get("aircraft", [])

                        # Update LCD display
                        if self.lcd_controller:
                            try:
                                if not aircraft_list:
                                    self.lcd_controller.display_no_aircraft()
                                else:
                                    # Cycle through aircraft count and individual aircraft
                                    if lcd_display_index == 0:
                                        self.lcd_controller.display_aircraft_count(
                                            len(aircraft_list)
                                        )
                                    else:
                                        aircraft_idx = (lcd_display_index - 1) % len(
                                            aircraft_list
                                        )
                                        self.lcd_controller.display_aircraft_info(
                                            aircraft_list[aircraft_idx]
                                        )

                                    lcd_display_index = (lcd_display_index + 1) % (
                                        len(aircraft_list) + 1
                                    )
                            except Exception as e:
                                print(f"Error updating LCD: {e}")

                        # Update OLED display
                        if self.oled_controller:
                            try:
                                if not aircraft_list:
                                    self.oled_controller.display_no_aircraft()
                                else:
                                    # Cycle through aircraft count and individual aircraft
                                    if oled_display_index == 0:
                                        self.oled_controller.display_aircraft_count(
                                            len(aircraft_list)
                                        )
                                    else:
                                        aircraft_idx = (oled_display_index - 1) % len(
                                            aircraft_list
                                        )
                                        self.oled_controller.display_aircraft_info(
                                            aircraft_list[aircraft_idx]
                                        )

                                    oled_display_index = (oled_display_index + 1) % (
                                        len(aircraft_list) + 1
                                    )
                            except Exception as e:
                                print(f"Error updating OLED: {e}")

                        # Update console
                        if self.console_enabled:
                            try:
                                aircraft_count = len(aircraft_list)
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                print(
                                    f"[{timestamp}] Aircraft detected: {aircraft_count}"
                                )

                                # Show aircraft with callsigns
                                with_callsign = [
                                    a
                                    for a in aircraft_list
                                    if a.get("flight", "").strip()
                                ]
                                if with_callsign:
                                    print(
                                        f"  Aircraft with callsigns: {len(with_callsign)}"
                                    )
                                    for aircraft in with_callsign[:5]:  # Show first 5
                                        flight = aircraft.get("flight", "").strip()
                                        alt = aircraft.get("alt_baro") or aircraft.get(
                                            "alt_geom"
                                        )
                                        alt_str = f"{alt}ft" if alt else "N/A"
                                        print(f"    {flight} - {alt_str}")
                            except Exception as e:
                                print(f"Error updating console: {e}")
                    else:
                        # No data available, update displays with error state
                        if self.lcd_controller:
                            try:
                                self.lcd_controller.display_error("No data")
                            except Exception as e:
                                print(f"Error updating LCD with error: {e}")

                        if self.oled_controller:
                            try:
                                self.oled_controller.display_error("No data")
                            except Exception as e:
                                print(f"Error updating OLED with error: {e}")

                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
