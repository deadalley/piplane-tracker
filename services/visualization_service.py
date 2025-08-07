#!/usr/bin/env python3
"""
Console Visualization Service for PiPlane Tracker
Provides simple console interface for aircraft monitoring
"""

import os
import sys
import time
import select
from datetime import datetime
from typing import Dict, List, Optional

from config import get_config

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from common.get_country_from_icao import get_country_from_icao
from common.get_country_flag import get_country_flag


class PiPlaneVisualizationService:
    """
    Simple console visualization service for aircraft monitoring

    Features:
    - Real-time aircraft list display
    - Simple keyboard navigation
    - Detailed aircraft information view
    - New aircraft highlighting with [NEW] tags
    """

    def __init__(self):
        """Initialize the visualization service"""
        self.aircraft_history: Dict[str, dict] = {}
        self.running = False
        self.thread = None
        self.current_view = "list"  # "list" or "detail"
        self.selected_aircraft_hex = None
        self.new_aircraft_tags: Dict[str, datetime] = {}  # Track [NEW] tags
        self.new_tag_duration = 30  # seconds to show [NEW] tag
        self.last_render_time = 0
        self.render_interval = 2.0  # Render every 2 seconds for auto-refresh
        self.auto_refresh_needed = False  # Flag to trigger immediate refresh

        config = get_config()
        self.monitor_aircraft_type = config.get_monitor_aircraft_type()

        # Get terminal dimensions
        try:
            import shutil

            self.screen_width, self.screen_height = shutil.get_terminal_size()
        except:
            self.screen_width = 70
            self.screen_height = 20

    def _clear_screen(self):
        """Clear the terminal screen"""
        print(
            "\033[2J\033[H", end=""
        )  # ANSI escape codes for clear screen and move cursor to top

    def _get_sorted_aircraft_list(self) -> List[tuple]:
        """Get sorted list of aircraft (hex_code, info) tuples"""
        return sorted(
            self.aircraft_history.items(),
            key=lambda x: (x[0], -int(x[1]["last_seen"].timestamp())),
        )

    def _is_aircraft_new(self, hex_code: str) -> bool:
        """Check if aircraft should show [NEW] tag"""
        if hex_code not in self.new_aircraft_tags:
            return False

        tag_time = self.new_aircraft_tags[hex_code]
        return (datetime.now() - tag_time).total_seconds() < self.new_tag_duration

    def _cleanup_new_tags(self):
        """Remove expired [NEW] tags"""
        current_time = datetime.now()
        expired_tags = []

        for hex_code, tag_time in self.new_aircraft_tags.items():
            if (current_time - tag_time).total_seconds() >= self.new_tag_duration:
                expired_tags.append(hex_code)

        for hex_code in expired_tags:
            del self.new_aircraft_tags[hex_code]

    def _print_warnings(self):
        """Print any warnings or important messages"""
        if self.monitor_aircraft_type not in ["all", "registered"]:
            print(
                f"⚠️ Unknown monitor aircraft type: {self.monitor_aircraft_type}. "
                "Defaulting to 'all'."
            )

        if not self.running:
            print("⚠️ Visualization service is not running.")

    def _render_aircraft_list(self):
        """Render the aircraft list view"""
        self._clear_screen()
        self._cleanup_new_tags()

        print("=" * 76)
        print("🛩️  PiPlane Tracker v1.0")
        print("=" * 76)
        print()

        aircraft_list = self._get_sorted_aircraft_list()

        if aircraft_list:
            # Show aircraft list with numbers
            for i, (hex_code, info) in enumerate(
                aircraft_list[:15]
            ):  # Show max 15 aircraft
                flight = info.get("flight", "Unknown")
                last_seen = info["last_seen"].strftime("%H:%M:%S")

                # Get country flag
                country = get_country_from_icao(hex_code)
                country_flag = get_country_flag(country)

                # New aircraft indicator
                new_indicator = " [NEW]" if self._is_aircraft_new(hex_code) else ""

                # Format additional aircraft data
                altitude = info.get("altitude")
                speed = info.get("speed")
                aircraft_type = info.get("aircraft_type", "")

                # Format altitude (feet)
                alt_str = f"{altitude:,}ft" if altitude is not None else "N/A"

                # Format speed (knots)
                speed_str = f"{speed}kt" if speed is not None else "N/A"

                # Format aircraft type (truncate if too long)
                type_str = f"{aircraft_type[:8]}" if aircraft_type else ""

                print(
                    f"{i+1:2d}. {country_flag} {flight:<10} ({hex_code.upper()}) {new_indicator:<6} | {type_str:<8} | {alt_str:<8} | {speed_str:<7} | {last_seen}"
                )
        else:
            print("No aircraft detected.")

        if len(aircraft_list) > 15:
            print(f"... and {len(aircraft_list) - 15} more aircraft")

        print()
        print("-" * 76)
        self._print_warnings()
        print()
        print("  [Enter] Refresh")
        print("  [1] Aircraft Details")
        print("  [Q] Quit")
        print("=" * 76)
        print(">>> ", end="", flush=True)

    def _render_aircraft_detail(self, hex_code: str):
        """Render detailed view of a specific aircraft"""
        self._clear_screen()

        if hex_code not in self.aircraft_history:
            print("Aircraft not found!")
            print("\nPress Enter to go back")
            return

        info = self.aircraft_history[hex_code]

        print("🛩️  PiPlane Tracker - Aircraft Details")
        print("=" * 76)
        print()

        # Basic information
        flight = info.get("flight", "Unknown")

        # Get country information
        country = get_country_from_icao(hex_code)
        country_flag = get_country_flag(country)

        print(f"✈️ {flight} ({country}) {country_flag}")
        print(f"🔖 ICAO Code: {hex_code.upper()}")

        # Flight data information
        altitude = info.get("altitude")
        speed = info.get("speed")
        aircraft_type = info.get("aircraft_type", "")
        manufacturer = info.get("manufacturer", "")
        registration = info.get("registration", "")
        operator = info.get("operator", "")

        print(f"📏 Altitude: {f'{altitude:,} ft' if altitude is not None else 'N/A'}")
        print(f"🏃 Speed: {f'{speed} knots' if speed is not None else 'N/A'}")
        print(f"✈️ Aircraft Type: {aircraft_type if aircraft_type else 'N/A'}")
        print(f"🏭 Manufacturer: {manufacturer if manufacturer else 'N/A'}")
        print(f"🏷️ Registration: {registration if registration else 'N/A'}")
        print(f"🏢 Operator: {operator if operator else 'N/A'}")

        # Timing information
        first_seen = info["first_seen"].strftime("%Y-%m-%d %H:%M:%S")
        last_seen = info["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕐 First seen: {first_seen}")
        print(f"🕐 Last seen: {last_seen}")

        # Calculate tracking duration
        duration = info["last_seen"] - info["first_seen"]
        duration_str = str(duration).split(".")[0]  # Remove microseconds
        print(f"⏱️ Tracked for: {duration_str}")

        # Position information
        positions = info.get("positions", [])

        # Show recent positions if available
        if len(positions) > 1:
            print("\n📊 Recent Position History:")
            recent_positions = positions[-5:]  # Last 5 positions
            for i, pos in enumerate(recent_positions):
                time_str = pos["timestamp"].strftime("%H:%M:%S")
                print(f"   {i+1}. {time_str} - {pos['lat']:.6f}, {pos['lon']:.6f}")

        print()
        print("-" * 76)
        print("[ENTER] Return to aircraft list")
        print(">>> ", end="", flush=True)

    def _has_input_available(self) -> bool:
        """Check if there's input available without blocking"""
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def _get_non_blocking_input(self) -> Optional[str]:
        """Get input without blocking, returns None if no input available"""
        if self._has_input_available():
            try:
                return input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                return "q"
        return None

    def _handle_user_input(self) -> bool:
        """Handle user input in a non-blocking way. Returns True if input was processed."""
        user_input = self._get_non_blocking_input()

        if user_input is None:
            return False  # No input available

        if self.current_view == "list":
            if user_input in ["q", "quit", "exit"]:
                self.running = False
            elif user_input.isdigit():
                # User entered a number to view aircraft details
                aircraft_list = self._get_sorted_aircraft_list()
                index = int(user_input) - 1
                if 0 <= index < len(aircraft_list):
                    self.selected_aircraft_hex = aircraft_list[index][0]
                    self.current_view = "detail"
                    return True
            # If user just presses Enter, we refresh the list (trigger immediate refresh)
            self.auto_refresh_needed = True

        elif self.current_view == "detail":
            # Any input goes back to list
            self.current_view = "list"
            self.selected_aircraft_hex = None
            self.auto_refresh_needed = True

        return True

    def _visualization_loop(self):
        """Main visualization loop with auto-refresh"""
        try:
            # Initial render
            current_time = time.time()
            self.last_render_time = current_time

            if self.current_view == "list":
                self._render_aircraft_list()
            elif self.current_view == "detail" and self.selected_aircraft_hex:
                self._render_aircraft_detail(self.selected_aircraft_hex)

            while self.running:
                current_time = time.time()

                # Handle any user input
                input_processed = self._handle_user_input()

                # Check if we need to refresh
                should_refresh = (
                    self.auto_refresh_needed
                    or (current_time - self.last_render_time) >= self.render_interval
                    or input_processed
                )

                if should_refresh:
                    # Render current view
                    if self.current_view == "list":
                        self._render_aircraft_list()
                    elif self.current_view == "detail" and self.selected_aircraft_hex:
                        self._render_aircraft_detail(self.selected_aircraft_hex)

                    self.last_render_time = current_time
                    self.auto_refresh_needed = False

                # Small sleep to prevent high CPU usage
                time.sleep(0.1)

        except Exception as e:
            print(f"Error in visualization loop: {e}")
        finally:
            self._clear_screen()

    def start(self):
        """Start the visualization service"""
        if self.thread and self.thread.is_alive():
            return

        self.running = True
        # Don't run in a separate thread - run directly
        self._visualization_loop()

    def stop(self):
        """Stop the visualization service"""
        self.running = False

    def add_new_aircraft(self, hex_code: str):
        """Mark an aircraft as new for [NEW] tag display and trigger immediate refresh"""
        self.new_aircraft_tags[hex_code] = datetime.now()
        self.auto_refresh_needed = (
            True  # Trigger immediate refresh when new aircraft is added
        )

    def remove_aircraft(self, hex_codes: set[str]):
        """Remove aircraft from new tags when they're removed from history"""
        for hex_code in hex_codes:
            if hex_code in self.new_aircraft_tags:
                del self.new_aircraft_tags[hex_code]
        self.auto_refresh_needed = True  # Trigger refresh when aircraft are removed

    def update_aircraft_history(self, aircraft_history: Dict[str, dict]):
        """Update the aircraft history reference"""
        self.aircraft_history = aircraft_history

    def is_running(self) -> bool:
        """Check if the visualization service is running"""
        return self.running

    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        self._clear_screen()
