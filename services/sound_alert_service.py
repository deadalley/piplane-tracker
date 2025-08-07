#!/usr/bin/env python3
"""
Sound Alert Service for PiPlane Tracker
Provides audio alerts when new aircraft are detected
"""

import os
import subprocess
import threading
import time
from datetime import datetime
from gpiozero import DigitalOutputDevice
from time import sleep


class PiPlaneSoundAlertService:
    """
    Sound alert service for aircraft detection alerts

    Supports multiple alert methods:
    - System beep (simple beep through PC speaker)
    - Audio file playback (WAV, MP3, etc.)
    - Text-to-speech announcements
    """

    def __init__(
        self,
        audio_file_path: str,
        alert_cooldown: float = 1.0,
        volume: int = 70,
        alert_type: str = "mp3",
    ):
        """Initialize the sound alert service"""
        # Check if mpg123 is available
        try:
            subprocess.run(
                ["mpg123", "--version"], capture_output=True, check=True, timeout=5
            )
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ):
            raise RuntimeError(
                "❌ Could not find mpg123. Please install it to use audio alerts."
            )

        self.alert_cooldown = alert_cooldown
        self.audio_file_path = audio_file_path
        self.volume = volume
        self.last_alert_time = 0
        self.alert_type = alert_type

        self.buzzer = DigitalOutputDevice(17)

    def _can_play_alert(self) -> bool:
        """Check if enough time has passed since last alert (cooldown)"""
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        return True

    def _play_buzzer(self):
        """Play a simple buzzer sound"""
        if not self.buzzer.is_active:
            self.buzzer.on()
            sleep(0.1)
            self.buzzer.off()

    def _play_mp3(self, file_path: str) -> bool:
        """Play MP3 file with mpg123"""
        subprocess.run(
            ["mpg123", "-q", file_path],
            check=True,
            capture_output=True,
            timeout=10,
        )
        return True

    def _play_alert(self, file_path: str):
        """
        Play an alert

        Args:
            file_path (str): Path to audio file
        """
        if not os.path.exists(file_path):
            print(f"Audio file not found: {file_path}")
            return

        def audio_thread():
            try:
                if self.alert_type == "buzzer":
                    self._play_buzzer()
                elif self.alert_type == "mp3":
                    if not self._play_mp3(file_path):
                        print(f"Failed to play MP3 file: {file_path}")
                        return
                else:
                    print(f"Unknown alert type: {self.alert_type}")
                    return

            except Exception as e:
                print(f"Error playing audio file: {e}")

        thread = threading.Thread(target=audio_thread, daemon=True)
        thread.start()

    def play_aircraft_alert(self):
        """
        Play alert sound for new aircraft detection
        """

        if not self._can_play_alert():
            return

        self.last_alert_time = time.time()

        timestamp = datetime.now().strftime("%H:%M:%S")

        self._play_alert(self.audio_file_path)
