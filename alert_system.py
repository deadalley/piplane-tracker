#!/usr/bin/env python3
"""
Airplane Tracker Alert System
Tracks new airplanes entering range and provides alerts
"""

import time
from datetime import datetime
from typing import Set, Dict, List
import threading
from aircraft_data import read_aircraft_data


class AirplaneAlertSystem:
    def __init__(self):
        """
        Initialize the alert system
        """
        self.known_aircraft: Set[str] = set()
        self.aircraft_history: Dict[str, dict] = {}
        self.alert_callbacks = []
        self.running = False

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
        Start monitoring for new aircraft

        Args:
            data_source_func: Function that returns aircraft data
            interval (int): Check interval in seconds
        """
        self.running = True

        def monitor_loop():
            while self.running:
                try:
                    aircraft_data = read_aircraft_data()
                    if aircraft_data:
                        self.check_for_new_aircraft(aircraft_data)
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(interval)

        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
