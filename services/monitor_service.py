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


class PiPlaneMonitorService:
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

        # New aircraft display state - separate queues for each controller
        self.console_queue: List[dict] = []
        self.lcd_queue: List[dict] = []
        self.oled_queue: List[dict] = []

        # Thread locks for queue safety
        self.console_queue_lock = threading.Lock()
        self.lcd_queue_lock = threading.Lock()
        self.oled_queue_lock = threading.Lock()

        # Keyboard input handling
        self.exit_requested = False

        # Set up data source path
        self.file_path = file_path

    def _start_display_threads(self):
        """Start persistent background threads for each display controller"""
        # Console printing thread - always runs
        console_thread = threading.Thread(
            target=self._console_display_loop, daemon=True, name="ConsoleDisplay"
        )
        console_thread.start()

        # LCD display thread - only if controller exists
        if self.lcd_controller:
            lcd_thread = threading.Thread(
                target=self._lcd_display_loop, daemon=True, name="LCDDisplay"
            )
            lcd_thread.start()

        # OLED display thread - only if controller exists
        if self.oled_controller:
            oled_thread = threading.Thread(
                target=self._oled_display_loop, daemon=True, name="OLEDDisplay"
            )
            oled_thread.start()

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
        aircrafts_to_remove = []

        current_hex_codes = {
            aircraft.get("hex") for aircraft in current_aircrafts if aircraft.get("hex")
        }

        for hex_code in self.aircraft_history:
            if hex_code not in current_hex_codes:
                aircraft_to_remove = self.aircraft_history[hex_code]
                last_seen = aircraft_to_remove["last_seen"]
                if (current_time - last_seen).total_seconds() > 300:  # 5 minutes
                    print(
                        f"Removing old aircraft: {aircraft_to_remove['flight'] or hex_code}"
                    )
                    aircrafts_to_remove.append(hex_code)

        for hex_code in aircrafts_to_remove:
            del self.aircraft_history[hex_code]

        # Clean up queues for removed aircraft
        if aircrafts_to_remove:
            self._cleanup_queues_for_removed_aircraft(set(aircrafts_to_remove))

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
        """Distribute new aircrafts to all controller queues"""
        if not new_aircrafts:
            return

        # Define queue configurations: (queue, lock, condition)
        queue_configs = [
            (
                self.console_queue,
                self.console_queue_lock,
                True,
            ),  # Console always enabled
            (self.lcd_queue, self.lcd_queue_lock, self.lcd_controller is not None),
            (self.oled_queue, self.oled_queue_lock, self.oled_controller is not None),
        ]

        # Get existing hex codes from all queues to avoid duplicates
        existing_hex_codes = []
        for queue, lock, _ in queue_configs:
            with lock:
                hex_codes = {
                    aircraft.get("hex") for aircraft in queue if aircraft.get("hex")
                }
                existing_hex_codes.append(hex_codes)

        # Add new aircraft to appropriate queues
        for aircraft in new_aircrafts:
            hex_code = aircraft.get("hex")
            if not hex_code:
                continue

            for i, (queue, lock, enabled) in enumerate(queue_configs):
                if enabled and hex_code not in existing_hex_codes[i]:
                    with lock:
                        queue.append(aircraft)

    def _has_queued_aircraft(self) -> bool:
        """Check if any of the queues have aircrafts to process"""
        with self.console_queue_lock:
            if self.console_queue:
                return True

        with self.lcd_queue_lock:
            if self.lcd_queue:
                return True

        with self.oled_queue_lock:
            if self.oled_queue:
                return True

        return False

    def _console_display_loop(self):
        """Persistent loop for console display processing"""
        while not self.exit_requested:
            try:
                with self.console_queue_lock:
                    if not self.console_queue:
                        # No aircraft to process, sleep briefly
                        pass
                    else:
                        # Process one aircraft
                        aircraft = self.console_queue.pop(0)
                        # Check if aircraft is still in history
                        hex_code = aircraft.get("hex")
                        if hex_code and hex_code in self.aircraft_history:
                            self._print_to_console(aircraft)
                        # If aircraft no longer in history, it was already removed from queue

                time.sleep(0.1)  # Brief sleep to prevent excessive CPU usage
            except Exception as e:
                print(f"Error in console display loop: {e}")
                time.sleep(1)

    def _lcd_display_loop(self):
        """Persistent loop for LCD display processing"""
        if not self.lcd_controller:
            return

        while not self.exit_requested:
            try:
                with self.lcd_queue_lock:
                    if not self.lcd_queue:
                        # No aircraft to process, sleep briefly
                        pass
                    else:
                        # Process one aircraft
                        aircraft = self.lcd_queue.pop(0)
                        # Check if aircraft is still in history
                        hex_code = aircraft.get("hex")
                        if hex_code and hex_code in self.aircraft_history:
                            self.lcd_controller.display_new_aircraft_detected(
                                interval=2
                            )
                            self.lcd_controller.display_aircraft_info(
                                aircraft=aircraft, interval=2
                            )
                        # If aircraft no longer in history, it was already removed from queue

                time.sleep(0.1)  # Brief sleep to prevent excessive CPU usage
            except Exception as e:
                print(f"Error in LCD display loop: {e}")
                time.sleep(1)

    def _oled_display_loop(self):
        """Persistent loop for OLED display processing"""
        if not self.oled_controller:
            return

        while not self.exit_requested:
            try:
                with self.oled_queue_lock:
                    if not self.oled_queue:
                        # No aircraft to process, sleep briefly
                        pass
                    else:
                        # Process one aircraft
                        aircraft = self.oled_queue.pop(0)
                        # Check if aircraft is still in history
                        hex_code = aircraft.get("hex")
                        if hex_code and hex_code in self.aircraft_history:
                            self.oled_controller.display_new_aircraft_detected(
                                interval=2
                            )
                            self.oled_controller.display_aircraft_info(
                                aircraft=aircraft, interval=5
                            )
                        # If aircraft no longer in history, it was already removed from queue

                time.sleep(0.1)  # Brief sleep to prevent excessive CPU usage
            except Exception as e:
                print(f"Error in OLED display loop: {e}")
                time.sleep(1)

    def _cleanup_queues_for_removed_aircraft(self, removed_hex_codes: set):
        """Remove aircraft from all queues when they're removed from history"""
        if not removed_hex_codes:
            return

        # Clean console queue
        with self.console_queue_lock:
            self.console_queue = [
                aircraft
                for aircraft in self.console_queue
                if aircraft.get("hex") not in removed_hex_codes
            ]

        # Clean LCD queue
        with self.lcd_queue_lock:
            self.lcd_queue = [
                aircraft
                for aircraft in self.lcd_queue
                if aircraft.get("hex") not in removed_hex_codes
            ]

        # Clean OLED queue
        with self.oled_queue_lock:
            self.oled_queue = [
                aircraft
                for aircraft in self.oled_queue
                if aircraft.get("hex") not in removed_hex_codes
            ]

    def _print_to_console(self, aircraft: dict):
        """Update console output"""

        flight = aircraft.get("flight", "").strip()
        alt = aircraft.get("alt_baro") or aircraft.get("alt_geom")
        alt_str = f"{alt}ft" if alt else "N/A"
        print(f"    {flight} - {alt_str}")

    def start_monitoring(self, interval=1):
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
                f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring started"
            )

            # Persistent display threads
            self._start_display_threads()

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

                        # Push new aircrafts to all display queues
                        self._update_new_aircrafts_queue(new_aircrafts)

                        # Log new aircraft detections
                        if len(new_aircrafts) > 0:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(
                                f"[{timestamp}] New aircrafts detected [{len(new_aircrafts)}]:"
                            )

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
