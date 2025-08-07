#!/bin/bash

#######################################################################
# PiPlane Tracker - One-Click Installation Script
# 
# This script automates the complete installation and setup of
# PiPlane Tracker on Raspberry Pi systems.
#
# What this script does:
# 1. Updates system packages
# 2. Installs dump1090-fa for ADS-B reception
# 3. Installs Python dependencies
# 4. Enables I2C for display hardware
# 5. Sets up systemd service for auto-start
# 6. Configures permissions and directories
#
# Usage: curl -sSL https://raw.githubusercontent.com/deadalley/piplane-tracker/main/scripts/install.sh | bash
# Or: wget -O install.sh https://raw.githubusercontent.com/deadalley/piplane-tracker/main/scripts/install.sh && chmod +x install.sh && ./install.sh
#
# Requirements:
# - Raspberry Pi running Raspberry Pi OS
# - Internet connection
# - sudo privileges
#
# Author: PiPlane Tracker Team
# Version: 1.0
# License: MIT
#######################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/piplane-tracker"
SERVICE_NAME="piplane-tracker"
USER_NAME="piplane"
REPO_URL="https://github.com/deadalley/piplane-tracker.git"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BOLD}$1${NC}"
}

# Function to check if running on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi\|BCM" /proc/cpuinfo 2>/dev/null; then
        print_warning "This doesn't appear to be a Raspberry Pi. Some features may not work correctly."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to check sudo privileges
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        print_error "This script requires sudo privileges. Please run with a user that has sudo access."
        exit 1
    fi
}

# Function to detect package manager
detect_package_manager() {
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        PKG_UPDATE="sudo apt update"
        PKG_INSTALL="sudo apt install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="sudo dnf update -y"
        PKG_INSTALL="sudo dnf install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        PKG_UPDATE="sudo yum update -y"
        PKG_INSTALL="sudo yum install -y"
    else
        print_error "Unsupported package manager. This script supports apt, dnf, and yum."
        exit 1
    fi
}

# Function to update system packages
update_system() {
    print_header "🔄 Updating system packages..."
    $PKG_UPDATE
    print_success "System packages updated"
}

# Function to install system dependencies
install_system_dependencies() {
    print_header "📦 Installing system dependencies..."
    
    case $PKG_MANAGER in
        "apt")
            $PKG_INSTALL \
                python3 \
                python3-pip \
                python3-venv \
                git \
                curl \
                wget \
                i2c-tools \
                python3-dev \
                python3-setuptools \
                build-essential \
                libasound2-dev \
                mpg123
            ;;
        "dnf"|"yum")
            $PKG_INSTALL \
                python3 \
                python3-pip \
                git \
                curl \
                wget \
                i2c-tools \
                python3-devel \
                python3-setuptools \
                gcc \
                gcc-c++ \
                make \
                alsa-lib-devel \
                mpg123
            ;;
    esac
    
    print_success "System dependencies installed"
}

# Function to install dump1090-fa
install_dump1090() {
    print_header "📡 Installing dump1090-fa (ADS-B decoder)..."
    
    if command -v dump1090-fa &> /dev/null; then
        print_warning "dump1090-fa is already installed"
        return
    fi
    
    case $PKG_MANAGER in
        "apt")
            # Add FlightAware repository
            wget -O - https://flightaware.com/adsb/piaware/files/flightaware-apt-repository.pub | sudo apt-key add -
            echo 'deb https://flightaware.com/adsb/piaware/repository flightaware-bullseye main' | sudo tee /etc/apt/sources.list.d/flightaware.list
            sudo apt update
            $PKG_INSTALL dump1090-fa
            ;;
        *)
            print_warning "dump1090-fa automatic installation not supported for $PKG_MANAGER"
            print_status "Please install dump1090-fa manually and ensure it's running"
            ;;
    esac
    
    print_success "dump1090-fa installation completed"
}

# Function to enable I2C
enable_i2c() {
    print_header "🔧 Enabling I2C interface..."
    
    # Enable I2C in config.txt (Raspberry Pi specific)
    if [[ -f /boot/config.txt ]]; then
        if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
            echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
            I2C_ENABLED=true
        fi
    elif [[ -f /boot/firmware/config.txt ]]; then
        if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt; then
            echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt
            I2C_ENABLED=true
        fi
    fi
    
    # Enable I2C module
    if ! grep -q "^i2c-dev" /etc/modules; then
        echo "i2c-dev" | sudo tee -a /etc/modules
    fi
    
    # Load I2C module immediately
    sudo modprobe i2c-dev || true
    
    print_success "I2C interface enabled"
}

# Function to create user
create_user() {
    print_header "👤 Creating piplane user..."
    
    if id "$USER_NAME" &>/dev/null; then
        print_warning "User $USER_NAME already exists"
    else
        sudo useradd -r -s /bin/false -d $INSTALL_DIR $USER_NAME
        print_success "User $USER_NAME created"
    fi
    
    # Add user to required groups
    sudo usermod -a -G i2c,gpio,spi $USER_NAME 2>/dev/null || true
}

# Function to clone or update repository
setup_application() {
    print_header "📁 Setting up PiPlane Tracker application..."
    
    # Create installation directory
    sudo mkdir -p $INSTALL_DIR
    
    # Clone or update repository
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        print_status "Updating existing installation..."
        cd $INSTALL_DIR
        sudo git pull
    else
        print_status "Cloning PiPlane Tracker repository..."
        sudo git clone $REPO_URL $INSTALL_DIR
    fi
    
    # Set ownership
    sudo chown -R $USER_NAME:$USER_NAME $INSTALL_DIR
    
    print_success "Application setup completed"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_header "🐍 Installing Python dependencies..."
    
    cd $INSTALL_DIR
    
    # Create virtual environment
    sudo -u $USER_NAME python3 -m venv venv
    
    # Install dependencies
    sudo -u $USER_NAME ./venv/bin/pip install --upgrade pip
    sudo -u $USER_NAME ./venv/bin/pip install -r requirements
    
    print_success "Python dependencies installed"
}

# Function to create systemd service
create_systemd_service() {
    print_header "⚙️  Creating systemd service..."
    
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=PiPlane Tracker - Aircraft Monitoring System
Documentation=https://github.com/deadalley/piplane-tracker
After=network.target dump1090-fa.service
Wants=dump1090-fa.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=piplane-tracker

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Systemd service created and enabled"
}

# Function to configure dump1090-fa
configure_dump1090() {
    print_header "📡 Configuring dump1090-fa..."
    
    if [[ -f /etc/default/dump1090-fa ]]; then
        # Backup original configuration
        sudo cp /etc/default/dump1090-fa /etc/default/dump1090-fa.backup
        
        # Ensure JSON output is enabled
        if ! grep -q "^JSON_INTERVAL=" /etc/default/dump1090-fa; then
            echo "JSON_INTERVAL=1" | sudo tee -a /etc/default/dump1090-fa
        fi
        
        # Start and enable dump1090-fa service
        sudo systemctl enable dump1090-fa
        sudo systemctl restart dump1090-fa
        
        print_success "dump1090-fa configured and started"
    else
        print_warning "dump1090-fa configuration file not found"
    fi
}

# Function to create initial configuration
create_initial_config() {
    print_header "⚙️  Creating initial configuration..."
    
    # Create config file if it doesn't exist
    if [[ ! -f "$INSTALL_DIR/config" ]]; then
        sudo -u $USER_NAME cp "$INSTALL_DIR/config" "$INSTALL_DIR/config.example"
    fi
    
    print_success "Initial configuration created"
}

# Function to test installation
test_installation() {
    print_header "🧪 Testing installation..."
    
    # Test Python script syntax
    cd $INSTALL_DIR
    if sudo -u $USER_NAME ./venv/bin/python -m py_compile main.py; then
        print_success "Python script syntax is valid"
    else
        print_error "Python script has syntax errors"
        return 1
    fi
    
    # Test I2C (if available)
    if command -v i2cdetect &> /dev/null; then
        print_status "I2C interface test:"
        sudo i2cdetect -y 1 2>/dev/null || print_warning "I2C test failed or no devices found"
    fi
    
    # Test data source
    if [[ -f /var/run/dump1090-fa/aircraft.json ]]; then
        print_success "ADS-B data source is available"
    else
        print_warning "ADS-B data source not found. Make sure dump1090-fa is running."
    fi
    
    print_success "Installation test completed"
}

# Function to display post-installation information
show_post_install_info() {
    print_header "🎉 Installation Complete!"
    echo
    print_success "PiPlane Tracker has been successfully installed!"
    echo
    echo -e "${BOLD}Installation Summary:${NC}"
    echo "  • Installation directory: $INSTALL_DIR"
    echo "  • Service name: $SERVICE_NAME"
    echo "  • User: $USER_NAME"
    echo "  • Configuration file: $INSTALL_DIR/config"
    echo
    echo -e "${BOLD}Next Steps:${NC}"
    echo "  1. Review and edit the configuration file if needed:"
    echo "     sudo nano $INSTALL_DIR/config"
    echo
    echo "  2. Start the service:"
    echo "     sudo systemctl start $SERVICE_NAME"
    echo
    echo "  3. Check service status:"
    echo "     sudo systemctl status $SERVICE_NAME"
    echo
    echo "  4. View logs:"
    echo "     sudo journalctl -u $SERVICE_NAME -f"
    echo
    echo -e "${BOLD}Management Commands:${NC}"
    echo "  • Start service:   sudo systemctl start $SERVICE_NAME"
    echo "  • Stop service:    sudo systemctl stop $SERVICE_NAME"
    echo "  • Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  • Service status:  sudo systemctl status $SERVICE_NAME"
    echo "  • View logs:       sudo journalctl -u $SERVICE_NAME -f"
    echo
    
    if [[ $I2C_ENABLED == true ]]; then
        print_warning "A reboot is recommended to ensure I2C changes take effect."
        echo "  Run: sudo reboot"
        echo
    fi
    
    echo -e "${BOLD}Documentation:${NC}"
    echo "  • GitHub: https://github.com/deadalley/piplane-tracker"
    echo "  • Configuration: $INSTALL_DIR/README.md"
    echo
    print_status "Happy plane tracking! ✈️"
}

# Main installation function
main() {
    clear
    echo "==============================================================================="
    echo "                        🛩️  PiPlane Tracker Installer"
    echo "==============================================================================="
    echo
    echo "This script will install and configure PiPlane Tracker on your Raspberry Pi."
    echo "The installation includes:"
    echo "  • System dependencies and Python packages"
    echo "  • dump1090-fa for ADS-B data reception"
    echo "  • I2C interface configuration for displays"
    echo "  • Systemd service for automatic startup"
    echo
    echo "Installation directory: $INSTALL_DIR"
    echo "Service name: $SERVICE_NAME"
    echo
    read -p "Continue with installation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo
    
    # Pre-installation checks
    print_header "🔍 Pre-installation checks..."
    check_root
    check_sudo
    check_raspberry_pi
    detect_package_manager
    print_success "Pre-installation checks passed"
    echo
    
    # Installation steps
    I2C_ENABLED=false
    
    update_system
    echo
    
    install_system_dependencies
    echo
    
    install_dump1090
    echo
    
    enable_i2c
    echo
    
    create_user
    echo
    
    setup_application
    echo
    
    install_python_dependencies
    echo
    
    create_systemd_service
    echo
    
    configure_dump1090
    echo
    
    create_initial_config
    echo
    
    test_installation
    echo
    
    show_post_install_info
}

# Run main function
main "$@"
