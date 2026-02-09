# AquaSentinel-Pi5 Quick Start Guide

## 🚀 Installation (3 Steps)

### 1. Extract and Navigate
```bash
tar -xzf aquasentinel-pi5.tar.gz
cd aquasentinel-pi5
```

### 2. Install
```bash
chmod +x setup.sh
sudo ./setup.sh install
```

### 3. Configure and Start
```bash
# Edit configuration
nano config.yaml

# Calibrate sensors (IMPORTANT!)
python3 calibrate.py

# Reboot for I2C/1-Wire
sudo reboot

# Start service
sudo systemctl start aquasentinel
sudo systemctl enable aquasentinel
```

## 📊 Access Dashboard
Open browser: http://raspberrypi.local:8080

## ⚙️ Quick Commands

```bash
# Check status
python3 main.py --status

# Export data
python3 main.py --export --format csv

# Generate report
python3 main.py --report --days 7

# Test alerts
python3 main.py --test-alerts

# View logs
sudo journalctl -u aquasentinel -f
```

## 🔧 Troubleshooting

### Sensors Not Detected
```bash
# Check I2C
sudo i2cdetect -y 1

# Check 1-Wire
ls /sys/bus/w1/devices/
```

### Service Issues
```bash
# Check status
sudo systemctl status aquasentinel

# Restart
sudo systemctl restart aquasentinel
```

## ⚠️ Important Notes

1. **Calibration Required**: Run `python3 calibrate.py` before first use
2. **Water Quality**: Not for official testing - educational/monitoring only
3. **Sensor Maintenance**: Clean sensors regularly for accurate readings

For full documentation, see README.md
