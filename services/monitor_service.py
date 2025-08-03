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

from config import get_config
from .display_services import (
    LCDDisplayService,
    OLEDDisplayService,
)
from .sound_alert_service import PiPlaneSoundAlertService
from .visualization_service import PiPlaneVisualizationService


class PiPlaneMonitorService:
    def __init__(
        self,
        lcd_controller=None,
        oled_controller=None,
        enable_visualization: bool = True,
    ):
        """
        Initialize the monitor service

        Args:
            file_path (str): Path to the aircraft.json file
            audio_file_path (str, optional): Path to audio file for alerts
            alert_cooldown (float): Minimum time between alerts in seconds
            volume (int): Audio volume (0-100)
            lcd_controller: LCD controller instance (optional)
            oled_controller: OLED controller instance (optional)
            enable_visualization (bool): Whether to enable the interactive visualization service
        """
        self.aircraft_history: Dict[str, dict] = {}
        self.running = False
        self.enable_visualization = enable_visualization

        config = get_config()

        # Set up data source path
        self.file_path = config.get_data_source_path()

        # Initialize display services
        self.lcd_service = None
        if lcd_controller:
            self.lcd_service = LCDDisplayService(lcd_controller)

        self.oled_service = None
        if oled_controller:
            self.oled_service = OLEDDisplayService(oled_controller)

        # Initialize visualization service for interactive console (optional)
        self.visualization_service = None
        if enable_visualization:
            self.visualization_service = PiPlaneVisualizationService()

        # Initalize sound alert service
        try:
            self.sound_alert_service = PiPlaneSoundAlertService(
                audio_file_path=config.get_sound_alert_audio_file(),
                alert_cooldown=config.get_sound_alert_cooldown(),
                volume=config.get_sound_alert_volume(),
            )
            print("✅ Sound alert service initialized")
        except Exception as e:
            print(f"⚠️  Sound alert service initialization failed: {e}")
            self.sound_alert_service = None

        # Set aircraft history reference for all services
        if self.lcd_service:
            self.lcd_service.aircraft_history = self.aircraft_history
        if self.oled_service:
            self.oled_service.aircraft_history = self.aircraft_history
        if self.visualization_service:
            self.visualization_service.update_aircraft_history(self.aircraft_history)

        # Keyboard input handling
        self.exit_requested = False

        # Start display services
        self._start_display_services()

    def _start_display_services(self):
        """Start all display services"""
        if self.lcd_service:
            self.lcd_service.start()

        if self.oled_service:
            self.oled_service.start()

        # Visualization service will be started in main monitoring loop

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

        # Use list() to create a copy of keys to avoid modification during iteration
        for hex_code in list(self.aircraft_history.keys()):
            if hex_code not in current_hex_codes:
                aircraft_to_remove = self.aircraft_history[hex_code]
                last_seen = aircraft_to_remove["last_seen"]
                if (current_time - last_seen).total_seconds() > 300:  # 5 minutes
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

        all_current_aircrafts = new_aircrafts + existing_aircrafts
        self._cleanup_old_aircrafts(all_current_aircrafts)

    def _update_new_aircrafts_queue(self, new_aircrafts: List[dict]):
        """Distribute new aircrafts to all display services"""
        if not new_aircrafts:
            return

        for aircraft in new_aircrafts:
            hex_code = aircraft.get("hex")
            if not hex_code:
                continue

            # Add to all active display services
            if self.lcd_service:
                self.lcd_service.add_aircraft(aircraft)

            if self.oled_service:
                self.oled_service.add_aircraft(aircraft)

    def _cleanup_queues_for_removed_aircraft(self, removed_hex_codes: set):
        """Remove aircraft from all display service queues when they're removed from history"""
        if not removed_hex_codes:
            return

        if self.lcd_service:
            self.lcd_service.remove_aircraft(removed_hex_codes)

        if self.oled_service:
            self.oled_service.remove_aircraft(removed_hex_codes)

        if self.visualization_service:
            self.visualization_service.remove_aircraft(removed_hex_codes)

    def start_monitoring(self, interval=1):
        """
        Start monitoring for new aircraft and updating displays

        Args:
            interval (int): Update interval in seconds for all components
        """
        self.running = True
        self.exit_requested = False

        def monitor_loop():
            print(
                f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring started"
            )

            while self.running and not self.exit_requested:
                aircraft_data = self._read_aircraft_data()

                if aircraft_data:
                    # Get new and existing aircrafts from current data set
                    new_aircrafts, existing_aircrafts = (
                        self._get_new_and_existing_aircrafts(aircraft_data)
                    )

                    # Add new aircrafts, update position, and remove old aircrafts from history
                    self._update_aircraft_history(new_aircrafts, existing_aircrafts)

                    # Push new aircrafts to all display queues
                    self._update_new_aircrafts_queue(new_aircrafts)

                    # Log new aircraft detections
                    if len(new_aircrafts) > 0:
                        # Mark new aircraft in visualization service if enabled
                        if self.visualization_service:
                            for aircraft in new_aircrafts:
                                hex_code = aircraft.get("hex")
                                if hex_code:
                                    self.visualization_service.add_new_aircraft(
                                        hex_code
                                    )

                        # Trigger sound alert for new aircraft
                        if self.sound_alert_service:
                            self.sound_alert_service.play_aircraft_alert()

                    time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

        # Start the visualization service if enabled (this will block until user quits)
        if self.visualization_service:
            self.visualization_service.start()
            # When visualization stops, stop monitoring
            self.running = False
            self.exit_requested = True
        else:
            # If no visualization service, just wait for the monitor thread
            try:
                while self.running and not self.exit_requested:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.running = False
                self.exit_requested = True

        return self.exit_requested

    def request_exit(self):
        """Request monitoring to stop (called externally)"""
        self.exit_requested = True
        self._stop_display_services()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.exit_requested = True
        self._stop_display_services()

    def _stop_display_services(self):
        """Stop all display services"""
        if self.lcd_service:
            self.lcd_service.stop()

        if self.oled_service:
            self.oled_service.stop()

        # Stop visualization service if enabled
        if self.visualization_service:
            self.visualization_service.stop()

    def cleanup(self):
        """Cleanup all services"""
        self.stop_monitoring()
        if self.visualization_service:
            self.visualization_service.cleanup()
