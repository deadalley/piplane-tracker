# Airplane Tracker System

A comprehensive airplane tracking system for Raspberry Pi that monitors aircraft using dump1090-fa data, provides alerts for new aircraft, and displays information on both a GUI interface and LCD screen.

## Features

- 🛩️ **Real-time Aircraft Monitoring**: Reads aircraft data from dump1090-fa
- 🚨 **New Aircraft Alerts**: Visual and audio alerts when new aircraft enter range
- 🖥️ **GUI Interface**: User-friendly Tkinter-based interface
- 📟 **LCD Display**: Shows aircraft information on connected LCD screen (using rpi-lcd)
- � **OLED Display**: Compact display on 0.91" I2C OLED screen (SSD1306)
- �📊 **Aircraft Tracking**: Maintains history of detected aircraft
- 🔄 **Continuous Monitoring**: Automatic updates every 5 seconds
- 📱 **Console Mode**: Optional headless operation

## Requirements

### Hardware
- Raspberry Pi (any model with GPIO)
- RTL-SDR dongle for aircraft reception
- 16x2 LCD display (optional, connected via GPIO)
- 0.91" I2C OLED display (optional, typically SSD1306 128x32)
- Speaker or buzzer for audio alerts (optional)

### Software
- Python 3.6+
- dump1090-fa (for aircraft data reception)
- Required Python packages (see requirements)

## Installation

1. **Clone or download the project files**:
   ```bash
   cd /home/pi/Documents/airplane-tracker
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements
   ```

3. **Install and configure dump1090-fa** (if not already installed):
   ```bash
   sudo apt update
   sudo apt install dump1090-fa
   sudo systemctl enable dump1090-fa
   sudo systemctl start dump1090-fa
   ```

4. **Connect LCD (optional)**:
   - Connect 16x2 LCD to GPIO pins as configured in `lcd_controller.py`
   - Default pin configuration:
     - RS: GPIO 26
     - Enable: GPIO 19
     - D4: GPIO 13
     - D5: GPIO 6
     - D6: GPIO 5
     - D7: GPIO 11

5. **Connect OLED (optional)**:
   - Connect 0.91" I2C OLED display to I2C pins
   - Default connections:
     - VCC: 3.3V
     - GND: Ground
     - SDA: GPIO 2 (Pin 3)
     - SCL: GPIO 3 (Pin 5)
   - Default I2C address: 0x3C

## Usage

### GUI Mode (Recommended)
```bash
python3 main.py
```

### Console Mode
```bash
python3 main.py --no-gui
```

### Additional Options
```bash
python3 main.py --no-lcd                    # Disable LCD display
python3 main.py --no-oled                   # Disable OLED display
python3 main.py --oled-only                 # Use OLED only (disable LCD)
python3 main.py --sound=/path/to/alert.wav  # Custom alert sound
python3 main.py --help                      # Show help
```

## File Structure

```
airplane-tracker/
├── main.py               # Main application entry point (GUI + LCD + Alerts)
├── aircraft_data.py      # Core aircraft data reading and country detection
├── aircraft_display.py   # Aircraft information display and formatting
├── display_utils.py      # Utility functions for data formatting
├── alert_system.py       # New aircraft detection and alerts
├── lcd_controller.py     # LCD display management
├── oled_controller.py    # OLED display management
├── gui_interface.py      # GUI interface
├── flight_enhancer.py    # Optional flight data enhancement from APIs
├── config.py             # Configuration management
├── config                # Configuration file (editable)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

### Configuration File (config)
The application uses a flat `config` file for all settings. Edit this file to customize:

```
# Airplane Tracker Configuration
# Edit these values to customize your airplane tracker settings

# Data Source Settings
data_source_file_path=/var/run/dump1090-fa/aircraft.json
data_source_update_interval=5
data_source_timeout=10

# Display Settings
display_lcd_enabled=true
display_oled_enabled=true
display_gui_enabled=true

# LCD Configuration
lcd_pin_rs=26
lcd_pin_enable=19
lcd_pin_d4=13
lcd_pin_d5=6
lcd_pin_d6=5
lcd_pin_d7=11
lcd_update_interval=5

# OLED Configuration
oled_width=128
oled_height=32
oled_i2c_address=60
oled_update_interval=3

# Alert Settings
alerts_enabled=true
alerts_sound_enabled=false
alerts_sound_file=
alerts_filter_by_callsign=true
alerts_aircraft_timeout=300

# Logging Settings (optional)
logging_enabled=false
logging_file_path=aircraft_log.txt
logging_level=INFO

# Enhancement Settings (API data - optional)
enhancement_enabled=false
enhancement_cache_timeout=300
enhancement_api_rate_limit=1
```

### Legacy Configuration Methods
You can still override settings programmatically:

### LCD Pin Configuration
Edit `lcd_controller.py` to change LCD pin connections:
```python
lcd_controller = AirplaneLCDController({
    'rs': 26, 'enable': 19, 'd4': 13, 
    'd5': 6, 'd6': 5, 'd7': 11
})
```

### OLED Configuration
Edit `oled_controller.py` to change OLED settings:
```python
oled_controller = AirplaneOLEDController(
    width=128, height=32, i2c_address=0x3C
)
```

### Update Intervals
Modify update intervals in `main.py`:
- GUI updates: 5 seconds
- Console updates: 10 seconds
- Alert checking: 5 seconds

### Data Source
The system reads from `/var/run/dump1090-fa/aircraft.json` by default. 
Change the path in the `config` file:
```
data_source_file_path=/your/custom/path/aircraft.json
```## Features Explained

### GUI Interface
- **Aircraft List**: Displays all detected aircraft in a table
- **Status Display**: Shows total aircraft count and new aircraft alerts
- **Alert Log**: Scrollable log of all aircraft events
- **Control Buttons**: Start/stop monitoring, manual refresh, clear alerts

### LCD Display
- **Cycling Display**: Automatically cycles through aircraft information
- **Aircraft Count**: Shows total number of detected aircraft
- **Individual Aircraft**: Displays callsign, altitude, and speed
- **Alerts**: Special alert display for new aircraft

### OLED Display
- **Compact View**: Optimized for 128x32 pixel display
- **Fast Updates**: 3-second cycle time for quick information
- **Aircraft Details**: Shows flight, altitude, speed, heading, and GPS status
- **Visual Alerts**: Special alert screens for new aircraft
- **System Info**: Time and status information

### Alert System
- **New Aircraft Detection**: Identifies when aircraft first enter range
- **Audio Alerts**: Optional sound notifications
- **Visual Alerts**: GUI and LCD notifications
- **Aircraft History**: Maintains record of all detected aircraft

## Troubleshooting

### Common Issues

1. **No aircraft data**:
   - Ensure dump1090-fa is running: `sudo systemctl status dump1090-fa`
   - Check data file exists: `ls -la /var/run/dump1090-fa/aircraft.json`
   - Verify RTL-SDR dongle is connected and working

2. **LCD not working**:
   - Check GPIO connections
   - Verify rpi-lcd installation: `pip3 show rpi-lcd`
   - Run LCD test: `python3 lcd_controller.py`

3. **OLED not working**:
   - Check I2C connections (SDA/SCL)
   - Enable I2C: `sudo raspi-config` → Interface Options → I2C → Enable
   - Check I2C address: `sudo i2cdetect -y 1` (should show 0x3C)
   - Verify OLED libraries: `pip3 show adafruit-circuitpython-ssd1306`
   - Run OLED test: `python3 oled_controller.py`

4. **GUI not starting**:
   - Install tkinter: `sudo apt install python3-tk`
   - Run in console mode: `python3 main.py --no-gui`

5. **Permission errors**:
   - Run with appropriate permissions
   - Check file permissions: `ls -la /var/run/dump1090-fa/`

### Testing Individual Components

Test the LCD:
```bash
python3 lcd_controller.py
```

Test the OLED:
```bash
python3 oled_controller.py
```

Test the GUI:
```bash
python3 gui_interface.py
```

Test basic aircraft data reading:
```bash
python3 -c "from aircraft_data import read_aircraft_data; print(read_aircraft_data())"
```

## Advanced Usage

### Running as a Service
To run automatically at startup, create a systemd service:

1. Create service file:
   ```bash
   sudo nano /etc/systemd/system/airplane-tracker.service
   ```

2. Add content:
   ```ini
   [Unit]
   Description=Airplane Tracker
   After=dump1090-fa.service
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/Documents/airplane-tracker
   ExecStart=/usr/bin/python3 main.py --no-gui
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl enable airplane-tracker
   sudo systemctl start airplane-tracker
   ```

### Custom Alert Sounds
Add custom alert sounds by placing WAV files in the project directory and using:
```bash
python3 main.py --sound=alert.wav
```

## Contributing

Feel free to contribute improvements:
- Enhanced GUI features
- Additional aircraft data fields
- Database logging
- Web interface
- Mobile notifications

## License

This project is open source. Use and modify as needed for your aircraft tracking requirements.

## Support

For issues related to:
- **dump1090-fa**: Check FlightAware documentation
- **LCD connections**: Verify GPIO wiring
- **RTL-SDR**: Ensure proper drivers and antenna setup
- **This software**: Check the troubleshooting section above
