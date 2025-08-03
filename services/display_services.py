#!/usr/bin/env python3
"""
Display Services for PiPlane Tracker
Individual service classes for each display type
"""

import time
import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Set
from datetime import datetime


class BaseDisplayService(ABC):
    """Base class for all display services"""

    def __init__(self, name: str):
        self.name = name
        self.queue: List[dict] = []
        self.queue_lock = threading.Lock()
        self.exit_requested = False
        self.thread = None
        self.aircraft_history: Dict[str, dict] = {}  # Will be set by monitor service

    def start(self):
        """Start the display service thread"""
        if self.thread and self.thread.is_alive():
            return

        self.exit_requested = False
        self.thread = threading.Thread(
            target=self._display_loop, daemon=True, name=f"{self.name}Display"
        )
        self.thread.start()

    def stop(self):
        """Stop the display service thread"""
        self.exit_requested = True

    def add_aircraft(self, aircraft: dict):
        """Add aircraft to the display queue"""
        hex_code = aircraft.get("hex")
        if not hex_code:
            return

        with self.queue_lock:
            # Check if aircraft is already in queue
            existing_hex_codes = {a.get("hex") for a in self.queue if a.get("hex")}
            if hex_code not in existing_hex_codes:
                self.queue.append(aircraft)

    def remove_aircraft(self, removed_hex_codes: Set[str]):
        """Remove aircraft from queue when they're removed from history"""
        if not removed_hex_codes:
            return

        with self.queue_lock:
            self.queue = [
                aircraft
                for aircraft in self.queue
                if aircraft.get("hex") not in removed_hex_codes
            ]

    def get_queue_length(self) -> int:
        """Get current queue length"""
        with self.queue_lock:
            return len(self.queue)

    def _display_loop(self):
        """Main display loop - runs continuously"""
        while not self.exit_requested:
            try:
                with self.queue_lock:
                    if not self.queue:
                        aircraft = None
                    else:
                        aircraft = self.queue.pop(0)

                if aircraft:
                    # Check if aircraft is still in history
                    hex_code = aircraft.get("hex")
                    if (
                        hex_code
                        and self.aircraft_history
                        and hex_code in self.aircraft_history
                    ):
                        self._process_aircraft(aircraft)
                else:
                    # No aircraft in queue, check if we should show idle message
                    with self.queue_lock:
                        queue_empty = len(self.queue) == 0

                    if queue_empty:
                        self._show_idle_message()

                time.sleep(0.1)  # Brief sleep to prevent excessive CPU usage
            except Exception as e:
                print(f"Error in {self.name} display loop: {e}")
                time.sleep(1)

    @abstractmethod
    def _process_aircraft(self, aircraft: dict):
        """Process a single aircraft - implemented by subclasses"""
        pass

    def _show_idle_message(self):
        """Show idle message - can be overridden by subclasses"""
        pass


class LCDDisplayService(BaseDisplayService):
    """LCD display service for showing aircraft on LCD screen"""

    def __init__(self, lcd_controller):
        super().__init__("LCD")
        self.lcd_controller = lcd_controller
        self._last_state = "idle"  # Track current display state

    def _process_aircraft(self, aircraft: dict):
        """Display aircraft information on LCD"""
        if self.lcd_controller:
            self.lcd_controller.display_new_aircraft_detected(interval=2)
            self.lcd_controller.display_aircraft_info(aircraft=aircraft, interval=5)
            self._last_state = "aircraft"

    def _show_idle_message(self):
        """Show idle message on LCD if not already showing"""
        if self.lcd_controller and self._last_state != "idle":
            self.lcd_controller.display_idle_message()
            self._last_state = "idle"


class OLEDDisplayService(BaseDisplayService):
    """OLED display service for showing aircraft on OLED screen"""

    def __init__(self, oled_controller):
        super().__init__("OLED")
        self.oled_controller = oled_controller
        self._last_state = "idle"  # Track current display state

    def _process_aircraft(self, aircraft: dict):
        """Display aircraft information on OLED"""
        if self.oled_controller:
            self.oled_controller.display_new_aircraft_detected(interval=2)
            self.oled_controller.display_aircraft_info(aircraft=aircraft, interval=5)
            self._last_state = "aircraft"

    def _show_idle_message(self):
        """Show idle message on OLED if not already showing"""
        if self.oled_controller and self._last_state != "idle":
            self.oled_controller.display_idle_message()
            self._last_state = "idle"
