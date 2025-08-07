#!/bin/bash

#######################################################################
# PiPlane Tracker - Uninstall Script
# 
# This script removes PiPlane Tracker and cleans up all installed
# components and configurations.
#
# What this script does:
# 1. Stops and disables the systemd service
# 2. Removes the service file
# 3. Removes the application directory
# 4. Removes the piplane user
# 5. Optionally removes dump1090-fa
#
# Usage: ./uninstall.sh
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

# Function to stop and disable service
remove_service() {
    print_header "🛑 Stopping and removing systemd service..."
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        sudo systemctl stop $SERVICE_NAME
        print_status "Service stopped"
    fi
    
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        sudo systemctl disable $SERVICE_NAME
        print_status "Service disabled"
    fi
    
    if [[ -f /etc/systemd/system/${SERVICE_NAME}.service ]]; then
        sudo rm /etc/systemd/system/${SERVICE_NAME}.service
        sudo systemctl daemon-reload
        print_status "Service file removed"
    fi
    
    print_success "Service removal completed"
}

# Function to remove application directory
remove_application() {
    print_header "📁 Removing application directory..."
    
    if [[ -d $INSTALL_DIR ]]; then
        sudo rm -rf $INSTALL_DIR
        print_success "Application directory removed"
    else
        print_warning "Application directory not found"
    fi
}

# Function to remove user
remove_user() {
    print_header "👤 Removing piplane user..."
    
    if id "$USER_NAME" &>/dev/null; then
        sudo userdel $USER_NAME
        print_success "User $USER_NAME removed"
    else
        print_warning "User $USER_NAME not found"
    fi
}

# Function to optionally remove dump1090-fa
remove_dump1090() {
    print_header "📡 dump1090-fa removal (optional)..."
    
    if command -v dump1090-fa &> /dev/null; then
        echo "dump1090-fa is installed on this system."
        echo "Note: dump1090-fa might be used by other applications."
        read -p "Do you want to remove dump1090-fa? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v apt &> /dev/null; then
                sudo systemctl stop dump1090-fa 2>/dev/null || true
                sudo systemctl disable dump1090-fa 2>/dev/null || true
                sudo apt remove -y dump1090-fa piaware
                print_success "dump1090-fa removed"
            else
                print_warning "Please remove dump1090-fa manually using your package manager"
            fi
        else
            print_status "Keeping dump1090-fa installed"
        fi
    else
        print_status "dump1090-fa not found"
    fi
}

# Function to clean up configuration files
cleanup_configs() {
    print_header "🧹 Cleaning up configuration files..."
    
    # Remove FlightAware repository (if added by installer)
    if [[ -f /etc/apt/sources.list.d/flightaware.list ]]; then
        read -p "Remove FlightAware APT repository? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo rm -f /etc/apt/sources.list.d/flightaware.list
            print_status "FlightAware repository removed"
        fi
    fi
    
    print_success "Cleanup completed"
}

# Function to display post-uninstall information
show_post_uninstall_info() {
    print_header "✅ Uninstallation Complete!"
    echo
    print_success "PiPlane Tracker has been successfully removed!"
    echo
    echo -e "${BOLD}What was removed:${NC}"
    echo "  • PiPlane Tracker application and files"
    echo "  • Systemd service configuration"
    echo "  • piplane user account"
    echo
    echo -e "${BOLD}What was NOT removed:${NC}"
    echo "  • System packages (Python, git, etc.)"
    echo "  • I2C configuration"
    echo "  • dump1090-fa (unless explicitly removed)"
    echo
    print_status "Thank you for using PiPlane Tracker! ✈️"
}

# Main uninstall function
main() {
    clear
    echo "==============================================================================="
    echo "                      🗑️  PiPlane Tracker Uninstaller"
    echo "==============================================================================="
    echo
    echo "This script will remove PiPlane Tracker from your system."
    echo "The following will be removed:"
    echo "  • PiPlane Tracker application files"
    echo "  • Systemd service configuration"
    echo "  • piplane user account"
    echo
    echo "The following will NOT be removed:"
    echo "  • System packages (Python, git, etc.)"
    echo "  • I2C configuration"
    echo "  • dump1090-fa (optional removal)"
    echo
    print_warning "This action cannot be undone!"
    echo
    read -p "Continue with uninstallation? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
    echo
    
    # Pre-uninstall checks
    print_header "🔍 Pre-uninstall checks..."
    check_root
    check_sudo
    print_success "Pre-uninstall checks passed"
    echo
    
    # Uninstall steps
    remove_service
    echo
    
    remove_application
    echo
    
    remove_user
    echo
    
    remove_dump1090
    echo
    
    cleanup_configs
    echo
    
    show_post_uninstall_info
}

# Run main function
main "$@"
