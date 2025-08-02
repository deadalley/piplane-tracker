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
import sys
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
        self.aircraft_history: Dict[str, dict] = {}
        self.alert_callbacks = []
        self.running = False

        # Display controllers
        self.lcd_controller = lcd_controller
        self.oled_controller = oled_controller

        # New aircraft display state
        self.new_aircraft_queue: List[dict] = []
        self.showing_new_aircraft = False
        self.new_aircraft_display_time = 10  # seconds to show new aircraft info
        self.new_aircraft_start_time = None

        # Keyboard input handling
        self.exit_requested = False
        self.keyboard_thread = None

        # Set up data source path
        if file_path is None:
            config = get_config()
            self.file_path = config.get_data_source_path()
        else:
            self.file_path = file_path

    def set_new_aircraft_display_time(self, seconds: int):
        """Set how long to display new aircraft information"""
        self.new_aircraft_display_time = seconds

    def clear_new_aircraft_display(self):
        """Manually clear the new aircraft display and return to count display"""
        self.showing_new_aircraft = False
        self.new_aircraft_queue.clear()
        self.new_aircraft_start_time = None

    def _should_show_new_aircraft(self) -> bool:
        """Check if we should still be showing new aircraft"""
        if not self.showing_new_aircraft or not self.new_aircraft_start_time:
            return False

        current_time = datetime.now()
        elapsed = (current_time - self.new_aircraft_start_time).total_seconds()
        return elapsed <= self.new_aircraft_display_time

    def _update_display_state(self):
        """Update the display state based on timing"""
        if self.showing_new_aircraft and not self._should_show_new_aircraft():
            self.showing_new_aircraft = False
            self.new_aircraft_queue.clear()

    def _update_lcd_display(
        self, aircraft_list: List[dict], current_new_aircraft_index: int
    ):
        """Update LCD display based on current state"""
        if not self.lcd_controller:
            return

        try:
            if not aircraft_list:
                self.lcd_controller.display_no_aircraft()
            elif self.showing_new_aircraft and self.new_aircraft_queue:
                # Show new aircraft information
                aircraft_to_show = self.new_aircraft_queue[
                    current_new_aircraft_index % len(self.new_aircraft_queue)
                ]
                self.lcd_controller.display_aircraft_info(aircraft_to_show)
            else:
                # Default: show aircraft count
                new_count = (
                    len(self.new_aircraft_queue) if self.showing_new_aircraft else 0
                )
                self.lcd_controller.display_aircraft_count(
                    len(aircraft_list), new_count
                )
        except Exception as e:
            print(f"Error updating LCD: {e}")

    def _update_oled_display(
        self, aircraft_list: List[dict], current_new_aircraft_index: int
    ):
        """Update OLED display based on current state"""
        if not self.oled_controller:
            return

        try:
            if not aircraft_list:
                self.oled_controller.display_no_aircraft()
            elif self.showing_new_aircraft and self.new_aircraft_queue:
                # Show new aircraft information
                aircraft_to_show = self.new_aircraft_queue[
                    current_new_aircraft_index % len(self.new_aircraft_queue)
                ]
                page_info = (
                    f"{(current_new_aircraft_index % len(self.new_aircraft_queue)) + 1}/{len(self.new_aircraft_queue)}"
                    if len(self.new_aircraft_queue) > 1
                    else ""
                )
                self.oled_controller.display_aircraft_info(aircraft_to_show, page_info)
            else:
                # Default: show aircraft count
                new_count = (
                    len(self.new_aircraft_queue) if self.showing_new_aircraft else 0
                )
                self.oled_controller.display_aircraft_count(
                    len(aircraft_list), new_count
                )
        except Exception as e:
            print(f"Error updating OLED: {e}")

    def _update_console(self, aircraft_list: List[dict]):
        """Update console output"""
        try:
            aircraft_count = len(aircraft_list)
            timestamp = datetime.now().strftime("%H:%M:%S")
            status = " [SHOWING NEW]" if self.showing_new_aircraft else ""
            print(f"[{timestamp}] Aircraft detected: {aircraft_count}{status}")

            # Show aircraft with callsigns
            with_callsign = [a for a in aircraft_list if a.get("flight", "").strip()]
            if with_callsign:
                print(f"  Aircraft with callsigns: {len(with_callsign)}")
                for aircraft in with_callsign[:5]:  # Show first 5
                    flight = aircraft.get("flight", "").strip()
                    alt = aircraft.get("alt_baro") or aircraft.get("alt_geom")
                    alt_str = f"{alt}ft" if alt else "N/A"
                    print(f"    {flight} - {alt_str}")
        except Exception as e:
            print(f"Error updating console: {e}")

    def _check_keyboard_input(self):
        """Check for keyboard input - simplified approach"""
        # For this implementation, we'll rely on the main thread to handle ESC
        # The keyboard checking will be done externally
        return self.exit_requested

    def _keyboard_listener(self):
        """Background thread to listen for exit requests"""
        while self.running and not self.exit_requested:
            time.sleep(0.1)

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

    def _cleanup_old_aircraft(self, current_aircraft: set):
        """Remove aircraft that haven't been seen for 5 minutes"""
        current_time = datetime.now()
        aircraft_to_remove = []

        for hex_code in self.aircraft_history:
            if hex_code not in current_aircraft:
                last_seen = self.aircraft_history[hex_code]["last_seen"]
                if (current_time - last_seen).total_seconds() > 300:  # 5 minutes
                    aircraft_to_remove.append(hex_code)

        for hex_code in aircraft_to_remove:
            del self.aircraft_history[hex_code]

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
            if hex_code not in self.aircraft_history:
                # Only alert for aircraft with flight names/callsigns
                flight = aircraft.get("flight", "").strip()
                if flight:  # Only add to new_aircraft list if it has a flight name
                    new_aircraft.append(aircraft)

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

        # Remove old aircraft that are no longer in range
        self._cleanup_old_aircraft(current_aircraft)

        # Trigger alerts for new aircraft
        if new_aircraft:
            # Add new aircraft to display queue
            self.new_aircraft_queue.extend(new_aircraft)
            self.showing_new_aircraft = True
            self.new_aircraft_start_time = datetime.now()

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
            "total_tracked": len(self.aircraft_history),
            "aircraft_history": self.aircraft_history.copy(),
        }

    def start_monitoring(self, interval=5):
        """
        Start monitoring for new aircraft and updating displays

        Args:
            interval (int): Update interval in seconds for all components
        """
        self.running = True
        self.exit_requested = False

        # Start keyboard listener thread
        self.keyboard_thread = threading.Thread(
            target=self._keyboard_listener, daemon=True
        )
        self.keyboard_thread.start()

        def monitor_loop():
            current_new_aircraft_index = 0

            while self.running and not self.exit_requested:
                try:
                    aircraft_data = self.read_aircraft_data()

                    if aircraft_data:
                        # Check for new aircraft and update displays
                        self.check_for_new_aircraft(aircraft_data)
                        aircraft_list = aircraft_data.get("aircraft", [])

                        # Update display state based on timing
                        self._update_display_state()

                        # Update all displays
                        self._update_lcd_display(
                            aircraft_list, current_new_aircraft_index
                        )
                        self._update_oled_display(
                            aircraft_list, current_new_aircraft_index
                        )
                        self._update_console(aircraft_list)

                        # Cycle through new aircraft if showing multiple
                        if (
                            self.showing_new_aircraft
                            and len(self.new_aircraft_queue) > 1
                        ):
                            current_new_aircraft_index = (
                                current_new_aircraft_index + 1
                            ) % len(self.new_aircraft_queue)
                        else:
                            current_new_aircraft_index = 0

                    else:
                        # No data available, show error on displays
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

        # Wait for exit signal
        try:
            while self.running and not self.exit_requested:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.exit_requested = True

        print("\n⏹️  Monitoring stopped (ESC pressed or interrupted)")
        return self.exit_requested

    def request_exit(self):
        """Request monitoring to stop (called externally)"""
        self.exit_requested = True

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.exit_requested = True
