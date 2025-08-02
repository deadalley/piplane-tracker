#!/usr/bin/env python3
"""
PiPlane Tracker Monitor
Tracks new airplanes entering range and provides alerts
"""

import time
from datetime import datetime
from typing import Dict, List, Optional
import threading
import json
import os
import threading


class PiPlaneMonitor:
    def __init__(self, file_path: str, lcd_controller=None, oled_controller=None):
        """
        Initialize the alert system

        Args:
            file_path (str, optional): Path to the aircraft.json file.
                                     If None, uses path from configuration.
            lcd_controller: LCD controller instance
            oled_controller: OLED controller instance
        """
        self.aircraft_history: Dict[str, dict] = {}
        self.running = False

        # Display controllers
        self.lcd_controller = lcd_controller
        self.oled_controller = oled_controller

        # New aircraft display state
        self.new_aircraft_queue: List[dict] = []
        self.showing_new_aircrafts = False

        # Keyboard input handling
        self.exit_requested = False

        # Set up data source path
        self.file_path = file_path

    def _is_valid_aircraft(self, aircraft: dict) -> bool:
        """Check if the aircraft data is valid"""
        flight = aircraft.get("flight", "").strip()
        return bool(flight)

    def _read_aircraft_data(self) -> Optional[Dict]:
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

    def _cleanup_old_aircrafts(self, current_aircrafts: List[dict]):
        """Remove aircrafts that haven't been seen for 5 minutes"""
        current_time = datetime.now()
        aircraft_to_remove = []

        current_hex_codes = {
            aircraft.get("hex") for aircraft in current_aircrafts if aircraft.get("hex")
        }

        for hex_code in self.aircraft_history:
            if hex_code not in current_hex_codes:
                last_seen = self.aircraft_history[hex_code]["last_seen"]
                if (current_time - last_seen).total_seconds() > 300:  # 5 minutes
                    aircraft_to_remove.append(hex_code)

        for hex_code in aircraft_to_remove:
            del self.aircraft_history[hex_code]

    def _create_aircraft_info(self, aircraft: dict):
        hex_code = aircraft.get("hex")

        if not hex_code:
            return

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

    def _update_aircraft_info(self, aircraft: dict):
        """Update aircraft information in the history"""
        hex_code = aircraft.get("hex")

        if not hex_code:
            return

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

    def _get_new_and_existing_aircrafts(
        self, aircraft_data: dict
    ) -> tuple[list[dict], list[dict]]:
        """
        Get new and existing aircrafts from the data

        Args:
            aircraft_data (dict): Aircraft data from dump1090-fa

        Returns:
            Tuple[List[dict], List[dict]]: New and existing aircrafts
        """
        if not aircraft_data or "aircraft" not in aircraft_data:
            return [], []

        new_aircrafts = []
        existing_aircrafts = []

        for aircraft in aircraft_data["aircraft"]:
            hex_code = aircraft.get("hex")

            if not hex_code:
                continue

            if not self._is_valid_aircraft(aircraft):
                continue

            if hex_code in self.aircraft_history:
                existing_aircrafts.append(aircraft)
            else:
                new_aircrafts.append(aircraft)

        return new_aircrafts, existing_aircrafts

    def _update_aircraft_history(
        self, new_aircrafts: List[dict], existing_aircrafts: List[dict]
    ):
        for aircraft in new_aircrafts:
            self._create_aircraft_info(aircraft)

        for aircraft in existing_aircrafts:
            self._update_aircraft_info(aircraft)

        self._cleanup_old_aircrafts(existing_aircrafts)

    def _update_new_aircrafts_queue(self, new_aircrafts: List[dict]):
        """Update the queue of new aircrafts to display"""
        if not new_aircrafts:
            return

        queued_aircraft_hex_codes = {
            aircraft.get("hex")
            for aircraft in self.new_aircraft_queue
            if aircraft.get("hex")
        }

        for aircraft in new_aircrafts:
            if aircraft.get("hex") not in queued_aircraft_hex_codes:
                self.new_aircraft_queue.append(aircraft)

    def _update_displays(self):
        """Cycle through new aircrafts in both displays"""
        while self.showing_new_aircrafts and len(self.new_aircraft_queue) > 0:
            aircraft = self.new_aircraft_queue.pop(0)
            if self.lcd_controller:
                self.lcd_controller.display_new_aircraft_detected(interval=2)
                self.lcd_controller.display_aircraft_info(aircraft=aircraft, interval=2)

            if self.oled_controller:
                self.oled_controller.display_new_aircraft_detected(interval=2)
                self.oled_controller.display_aircraft_info(
                    aircraft=aircraft, interval=5
                )

        if self.lcd_controller:
            self.lcd_controller.display_idle_message()
        if self.oled_controller:
            self.oled_controller.display_idle_message()

        self.showing_new_aircrafts = False

    def _update_console(self):
        """Update console output"""
        try:
            aircraft_count = len(self.new_aircraft_queue)
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] New aircrafts detected [{aircraft_count}]:")

            # Show aircraft with callsigns
            for aircraft in self.new_aircraft_queue:
                flight = aircraft.get("flight", "").strip()
                alt = aircraft.get("alt_baro") or aircraft.get("alt_geom")
                alt_str = f"{alt}ft" if alt else "N/A"
                print(f"    {flight} - {alt_str}")
        except Exception as e:
            print(f"Error updating console: {e}")

    def start_monitoring(self, interval=5):
        """
        Start monitoring for new aircraft and updating displays

        Args:
            interval (int): Update interval in seconds for all components
        """
        self.running = True
        self.exit_requested = False

        def monitor_loop():
            if self.lcd_controller:
                self.lcd_controller.display_idle_message()
            if self.oled_controller:
                self.oled_controller.display_idle_message()

            print(
                f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]Monitoring started"
            )

            while self.running and not self.exit_requested:
                try:
                    aircraft_data = self._read_aircraft_data()

                    if aircraft_data:
                        # Get new and existing aircrafts from current data set
                        new_aircrafts, existing_aircrafts = (
                            self._get_new_and_existing_aircrafts(aircraft_data)
                        )

                        # Add new aicrafts, update position, and remove old aircrafts from history
                        self._update_aircraft_history(new_aircrafts, existing_aircrafts)

                        # Push new aircrafts to the display queue
                        self._update_new_aircrafts_queue(new_aircrafts)

                        if self.showing_new_aircrafts:
                            pass
                        elif len(new_aircrafts):
                            self.showing_new_aircrafts = True
                            self._update_console()

                            update_displays_thread = threading.Thread(
                                target=self._update_displays,
                                daemon=True,
                            )
                            update_displays_thread.start()

                    else:
                        if self.lcd_controller:
                            self.lcd_controller.display_error("No data")

                        if self.oled_controller:
                            self.oled_controller.display_error("No data")

                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

        # Wait for exit signal
        try:
            while self.running and not self.exit_requested:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.exit_requested = True

        return self.exit_requested

    def request_exit(self):
        """Request monitoring to stop (called externally)"""
        self.exit_requested = True

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.exit_requested = True

    def list_known_aircraft(self):
        """List all known aircraft in a formatted way"""
        print("\n" + "=" * 60)
        print("📋 KNOWN AIRCRAFT HISTORY")
        print("=" * 60)

        if not self.aircraft_history:
            print("No aircraft have been detected yet.")
            return

        print(f"Total aircraft tracked: {len(self.aircraft_history)}")
        print()

        # Sort by last seen time (most recent first)
        sorted_aircraft = sorted(
            self.aircraft_history.items(), key=lambda x: x[1]["last_seen"], reverse=True
        )

        for hex_code, info in sorted_aircraft:
            flight = info.get("flight", "Unknown")
            first_seen = info["first_seen"].strftime("%Y-%m-%d %H:%M:%S")
            last_seen = info["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
            position_count = len(info.get("positions", []))

            print(f"✈️  {flight} (ICAO: {hex_code})")
            print(f"   First seen: {first_seen}")
            print(f"   Last seen:  {last_seen}")
            print(f"   Positions tracked: {position_count}")
            print()

        print("=" * 60)
