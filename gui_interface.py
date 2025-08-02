#!/usr/bin/env python3
"""
Simple GUI Interface for Airplane Tracker
Provides a Tkinter-based interface to view aircraft information
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
from typing import Dict, List
import json

class AirplaneTrackerGUI:
    def __init__(self, data_source_func, alert_system=None, lcd_controller=None):
        """
        Initialize the GUI
        
        Args:
            data_source_func: Function that returns aircraft data
            alert_system: AirplaneAlertSystem instance (optional)
            lcd_controller: AirplaneLCDController instance (optional)
        """
        self.data_source_func = data_source_func
        self.alert_system = alert_system
        self.lcd_controller = lcd_controller
        self.running = False
        self.update_interval = 5  # seconds
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Airplane Tracker - Live Aircraft Monitor")
        self.root.geometry("900x700")
        self.root.configure(bg='#2c3e50')
        
        # Variables for tracking
        self.total_aircraft_var = tk.StringVar(value="0")
        self.new_aircraft_var = tk.StringVar(value="0")
        self.last_update_var = tk.StringVar(value="Never")
        
        self.setup_gui()
        
        # Register alert callback if alert system is provided
        if self.alert_system:
            self.alert_system.add_alert_callback(self.on_new_aircraft_alert)
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="✈️ Airplane Tracker", 
            font=('Arial', 24, 'bold'),
            bg='#2c3e50',
            fg='#ecf0f1'
        )
        title_label.pack(pady=10)
        
        # Status frame
        status_frame = tk.Frame(self.root, bg='#34495e', relief='raised', bd=2)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # Status indicators
        status_row1 = tk.Frame(status_frame, bg='#34495e')
        status_row1.pack(fill='x', padx=10, pady=5)
        
        tk.Label(status_row1, text="Total Aircraft:", font=('Arial', 12, 'bold'), bg='#34495e', fg='#ecf0f1').pack(side='left')
        tk.Label(status_row1, textvariable=self.total_aircraft_var, font=('Arial', 12), bg='#34495e', fg='#3498db').pack(side='left', padx=(5,20))
        
        tk.Label(status_row1, text="New Aircraft:", font=('Arial', 12, 'bold'), bg='#34495e', fg='#ecf0f1').pack(side='left')
        tk.Label(status_row1, textvariable=self.new_aircraft_var, font=('Arial', 12), bg='#34495e', fg='#e74c3c').pack(side='left', padx=(5,20))
        
        tk.Label(status_row1, text="Last Update:", font=('Arial', 12, 'bold'), bg='#34495e', fg='#ecf0f1').pack(side='left')
        tk.Label(status_row1, textvariable=self.last_update_var, font=('Arial', 12), bg='#34495e', fg='#2ecc71').pack(side='left', padx=5)
        
        # Control buttons
        control_frame = tk.Frame(self.root, bg='#2c3e50')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.start_button = tk.Button(
            control_frame, 
            text="Start Monitoring", 
            command=self.start_monitoring,
            bg='#27ae60',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=2
        )
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = tk.Button(
            control_frame, 
            text="Stop Monitoring", 
            command=self.stop_monitoring,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=2,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=5)
        
        refresh_button = tk.Button(
            control_frame, 
            text="Refresh Now", 
            command=self.manual_refresh,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=2
        )
        refresh_button.pack(side='left', padx=5)
        
        # Clear alerts button
        clear_button = tk.Button(
            control_frame, 
            text="Clear Alerts", 
            command=self.clear_alerts,
            bg='#f39c12',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=2
        )
        clear_button.pack(side='left', padx=5)
        
        # Aircraft list frame
        list_frame = tk.Frame(self.root, bg='#2c3e50')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        tk.Label(list_frame, text="Current Aircraft:", font=('Arial', 14, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
        # Create Treeview for aircraft list
        columns = ('Flight', 'ICAO', 'Position', 'Altitude', 'Speed', 'Heading', 'Last Seen')
        self.aircraft_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        # Define column headings and widths
        column_widths = {'Flight': 100, 'ICAO': 80, 'Position': 150, 'Altitude': 80, 'Speed': 80, 'Heading': 80, 'Last Seen': 100}
        
        for col in columns:
            self.aircraft_tree.heading(col, text=col)
            self.aircraft_tree.column(col, width=column_widths.get(col, 100))
        
        # Add scrollbar to treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.aircraft_tree.yview)
        self.aircraft_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.aircraft_tree.pack(side='left', fill='both', expand=True)
        tree_scrollbar.pack(side='right', fill='y')
        
        # Alert log frame
        alert_frame = tk.Frame(self.root, bg='#2c3e50')
        alert_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(alert_frame, text="Alert Log:", font=('Arial', 12, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(anchor='w')
        
        self.alert_log = scrolledtext.ScrolledText(
            alert_frame, 
            height=6, 
            bg='#34495e', 
            fg='#ecf0f1',
            font=('Courier', 10)
        )
        self.alert_log.pack(fill='x', pady=5)
    
    def log_message(self, message, alert=False):
        """Add a message to the alert log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        prefix = "🚨 ALERT" if alert else "ℹ️ INFO"
        log_entry = f"[{timestamp}] {prefix}: {message}\n"
        
        self.alert_log.insert(tk.END, log_entry)
        self.alert_log.see(tk.END)  # Scroll to bottom
        
        # Limit log size (keep last 100 lines)
        lines = self.alert_log.get('1.0', tk.END).split('\n')
        if len(lines) > 100:
            self.alert_log.delete('1.0', f"{len(lines)-100}.0")
    
    def update_aircraft_display(self, aircraft_data):
        """Update the aircraft display"""
        # Clear existing data
        for item in self.aircraft_tree.get_children():
            self.aircraft_tree.delete(item)
        
        if not aircraft_data or 'aircraft' not in aircraft_data:
            self.total_aircraft_var.set("0")
            return
        
        aircraft_list = aircraft_data['aircraft']
        self.total_aircraft_var.set(str(len(aircraft_list)))
        
        # Populate treeview with aircraft data
        for aircraft in aircraft_list:
            flight = aircraft.get('flight', '').strip() or 'N/A'
            icao = aircraft.get('hex', 'Unknown')
            
            # Position
            lat = aircraft.get('lat')
            lon = aircraft.get('lon')
            if lat is not None and lon is not None:
                position = f"{lat:.4f}, {lon:.4f}"
            else:
                position = 'N/A'
            
            # Altitude
            altitude = aircraft.get('alt_baro') or aircraft.get('alt_geom')
            alt_str = f"{altitude} ft" if altitude is not None else 'N/A'
            
            # Speed
            speed = aircraft.get('gs')
            speed_str = f"{speed} kt" if speed is not None else 'N/A'
            
            # Heading
            heading = aircraft.get('track')
            heading_str = f"{heading}°" if heading is not None else 'N/A'
            
            # Last seen
            seen = aircraft.get('seen')
            seen_str = f"{seen}s ago" if seen is not None else 'N/A'
            
            # Insert into treeview
            self.aircraft_tree.insert('', 'end', values=(
                flight, icao, position, alt_str, speed_str, heading_str, seen_str
            ))
        
        # Update last update time
        self.last_update_var.set(datetime.now().strftime('%H:%M:%S'))
    
    def on_new_aircraft_alert(self, new_aircraft):
        """Callback for new aircraft alerts"""
        count = len(new_aircraft)
        self.new_aircraft_var.set(str(count))
        
        for aircraft in new_aircraft:
            flight = aircraft.get('flight', '').strip()
            icao = aircraft.get('hex', 'Unknown')
            display_name = flight if flight else f"ICAO:{icao}"
            self.log_message(f"New aircraft detected: {display_name}", alert=True)
    
    def clear_alerts(self):
        """Clear the alert counter and log"""
        self.new_aircraft_var.set("0")
        self.alert_log.delete('1.0', tk.END)
        self.log_message("Alert log cleared")
    
    def manual_refresh(self):
        """Manually refresh aircraft data"""
        try:
            aircraft_data = self.data_source_func()
            if aircraft_data:
                self.update_aircraft_display(aircraft_data)
                if self.alert_system:
                    self.alert_system.check_for_new_aircraft(aircraft_data)
                self.log_message("Manual refresh completed")
            else:
                self.log_message("Failed to retrieve aircraft data")
        except Exception as e:
            self.log_message(f"Error during manual refresh: {e}")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if not self.running:
            self.running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            monitor_thread.start()
            
            # Start alert system if available
            if self.alert_system:
                self.alert_system.start_monitoring(self.data_source_func, self.update_interval)
            
            # Start LCD cycling if available
            if self.lcd_controller:
                self.lcd_controller.start_cycling_display(self.data_source_func, self.update_interval)
            
            self.log_message("Monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        if self.running:
            self.running = False
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
            # Stop alert system
            if self.alert_system:
                self.alert_system.stop_monitoring()
            
            # Stop LCD cycling
            if self.lcd_controller:
                self.lcd_controller.stop_cycling_display()
            
            self.log_message("Monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                aircraft_data = self.data_source_func()
                if aircraft_data:
                    # Update display in main thread
                    self.root.after(0, lambda: self.update_aircraft_display(aircraft_data))
                else:
                    self.root.after(0, lambda: self.log_message("No aircraft data available"))
                
                time.sleep(self.update_interval)
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Monitoring error: {e}"))
                time.sleep(self.update_interval)
    
    def run(self):
        """Start the GUI main loop"""
        self.log_message("Airplane Tracker GUI started")
        self.log_message("Click 'Start Monitoring' to begin tracking aircraft")
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start GUI
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_monitoring()
        if self.lcd_controller:
            self.lcd_controller.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    # Test GUI with dummy data
    def dummy_data_source():
        return {
            'aircraft': [
                {
                    'hex': 'A12345',
                    'flight': 'UAL123',
                    'lat': 37.7749,
                    'lon': -122.4194,
                    'alt_baro': 35000,
                    'gs': 450,
                    'track': 270,
                    'seen': 5
                },
                {
                    'hex': 'B67890',
                    'flight': 'DAL456',
                    'lat': 37.7849,
                    'lon': -122.4094,
                    'alt_baro': 28000,
                    'gs': 380,
                    'track': 180,
                    'seen': 12
                }
            ]
        }
    
    from aircraft_data import read_aircraft_data
    gui = AirplaneTrackerGUI(read_aircraft_data)
    gui.run()
