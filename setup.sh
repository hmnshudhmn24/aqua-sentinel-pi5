#!/bin/bash
set -e

echo "======================================"
echo "AquaSentinel-Pi5 Setup Script"
echo "======================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

install_system_deps() {
    print_status "Installing system dependencies..."
    apt update
    apt install -y python3-pip python3-dev python3-venv git i2c-tools build-essential
    print_status "System dependencies installed"
}

enable_i2c() {
    print_status "Enabling I2C interface..."
    if grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
        print_status "I2C already enabled"
    else
        echo "dtparam=i2c_arm=on" >> /boot/config.txt
        print_status "I2C enabled (reboot required)"
    fi
    modprobe i2c-dev 2>/dev/null || true
}

enable_1wire() {
    print_status "Enabling 1-Wire interface..."
    if grep -q "^dtoverlay=w1-gpio" /boot/config.txt; then
        print_status "1-Wire already enabled"
    else
        echo "dtoverlay=w1-gpio" >> /boot/config.txt
        print_status "1-Wire enabled (reboot required)"
    fi
    modprobe w1-gpio 2>/dev/null || true
    modprobe w1-therm 2>/dev/null || true
}

setup_python() {
    print_status "Setting up Python environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Python environment ready"
}

create_directories() {
    print_status "Creating directories..."
    mkdir -p logs data data/exports
    print_status "Directories created"
}

install_service() {
    print_status "Installing systemd service..."
    INSTALL_DIR=$(pwd)
    cat > aquasentinel.service << EOF
[Unit]
Description=AquaSentinel-Pi5 Water Quality Monitor
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    cp aquasentinel.service /etc/systemd/system/
    systemctl daemon-reload
    print_status "Service installed"
}

test_sensors() {
    print_status "Testing sensors..."
    echo "I2C Devices:"
    i2cdetect -y 1 || true
    echo "1-Wire Devices:"
    ls /sys/bus/w1/devices/ 2>/dev/null || echo "No devices found"
}

install() {
    echo "Starting installation..."
    install_system_deps
    enable_i2c
    enable_1wire
    create_directories
    setup_python
    install_service
    echo ""
    print_status "Installation complete!"
    echo "Reboot required for I2C/1-Wire changes"
    echo "After reboot: sudo systemctl start aquasentinel"
}

case "$1" in
    install) install ;;
    service) install_service ;;
    python) setup_python ;;
    test) test_sensors ;;
    *) echo "Usage: $0 {install|service|python|test}" ; exit 1 ;;
esac
