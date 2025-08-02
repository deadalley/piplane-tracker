#!/usr/bin/env python3
"""
Aircraft Display Utilities
Formatting functions for displaying aircraft information
"""

from typing import Any, Optional

def format_coordinate(coord: Optional[float]) -> str:
    """Format coordinate for display"""
    if coord is None:
        return "N/A"
    return f"{coord:.6f}"

def format_altitude(alt: Optional[int]) -> str:
    """Format altitude for display"""
    if alt is None:
        return "N/A"
    return f"{alt} ft"

def format_speed(speed: Optional[int]) -> str:
    """Format speed for display"""
    if speed is None:
        return "N/A"
    return f"{speed} kt"

def format_heading(heading: Optional[float]) -> str:
    """Format heading for display"""
    if heading is None:
        return "N/A"
    return f"{heading}°"

def format_squawk(squawk: Optional[Any]) -> str:
    """Format squawk code for display"""
    if squawk is None:
        return "N/A"
    return str(squawk)

def format_vertical_rate(vert_rate: Optional[int]) -> str:
    """Format vertical rate with direction"""
    if vert_rate is None:
        return "N/A"
    
    direction = "climbing" if vert_rate > 0 else "descending" if vert_rate < 0 else "level"
    return f"{vert_rate} ft/min ({direction})"

def format_signal_strength(rssi: Optional[float]) -> str:
    """Format signal strength for display"""
    if rssi is None:
        return "N/A"
    return f"{rssi} dBFS"

def format_last_seen(seen: Optional[float]) -> str:
    """Format last seen time"""
    if seen is None:
        return "N/A"
    return f"{seen} seconds ago"

def format_messages(messages: Optional[int]) -> str:
    """Format message count"""
    if messages is None:
        return "N/A"
    return str(messages)
