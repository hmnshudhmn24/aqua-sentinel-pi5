# Aqua Sentinel Pi5 💧

A smart water quality monitoring system built on Raspberry Pi 5 that continuously measures pH, turbidity, and temperature to detect pollution events. The system classifies water conditions in real time and supports environmental monitoring using low-cost IoT hardware.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)

## 🌊 Features

- **Real-time Water Quality Monitoring**
  - pH Level Measurement (0-14 scale)
  - Turbidity Detection (NTU units)
  - Water Temperature (°C/°F)

- **Intelligent Analysis**
  - Automatic water quality classification
  - Pollution event detection
  - Trend analysis and prediction
  - Historical data comparison

- **Multi-level Classification**
  - Excellent: Safe for all uses
  - Good: Generally safe
  - Fair: Monitor closely
  - Poor: Action recommended
  - Critical: Immediate attention required

- **Alert System**
  - Email notifications
  - SMS alerts (Twilio)
  - Local buzzer and LED indicators
  - Configurable thresholds

- **Data Management**
  - SQLite database for historical data
  - CSV/JSON export functionality
  - Automatic data backup
  - Configurable retention policies

- **Web Dashboard**
  - Real-time monitoring interface
  - Interactive graphs and charts
  - Historical data visualization
  - Water quality trends
  - Alert history

## 📋 Hardware Requirements

### Required Components

| Component | Model/Type | Purpose |
|-----------|------------|---------|
| Microcontroller | Raspberry Pi 5 (4GB+ RAM) | Main processing unit |
| pH Sensor | Analog pH Sensor (0-14) | pH measurement |
| Turbidity Sensor | Analog Turbidity Sensor | Water clarity measurement |
| Temperature Sensor | DS18B20 (waterproof) | Water temperature |
| ADC | ADS1115 16-bit ADC | Analog-to-digital conversion |
| Buzzer | Active 5V Buzzer | Audio alerts |
| LEDs | RGB LED or 3x single LEDs | Visual status indicators |
| Display (Optional) | 0.96" OLED (SSD1306) | Local data display |

### Wiring Diagram

```
ADS1115 ADC (I2C):
- VDD → 3.3V (Pin 1)
- GND → GND (Pin 6)
- SCL → GPIO 3 (Pin 5)
- SDA → GPIO 2 (Pin 3)

pH Sensor (Analog):
- VCC → 5V (Pin 2)
- GND → GND (Pin 6)
- OUT → ADS1115 A0

Turbidity Sensor (Analog):
- VCC → 5V (Pin 4)
- GND → GND (Pin 14)
- OUT → ADS1115 A1

DS18B20 Temperature Sensor (1-Wire):
- VCC  → 3.3V (Pin 17)
- GND  → GND (Pin 20)
- DATA → GPIO 4 (Pin 7)
- 4.7kΩ resistor between VCC and DATA

Buzzer:
- Positive → GPIO 17 (Pin 11)
- Negative → GND (Pin 9)

RGB LED:
- Red    → GPIO 22 (Pin 15) + 220Ω resistor
- Green  → GPIO 27 (Pin 13) + 220Ω resistor
- Blue   → GPIO 23 (Pin 16) + 220Ω resistor
- Common → GND (Pin 25)
```

## 🚀 Installation

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev git i2c-tools

# Enable I2C and 1-Wire interfaces
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Navigate to: Interface Options → 1-Wire → Enable

# Reboot to apply changes
sudo reboot
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/aquasentinel-pi5.git
cd aquasentinel-pi5
```

### 3. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Sensor Calibration

**IMPORTANT**: Sensors must be calibrated before first use!

```bash
# Run calibration wizard
python3 calibrate.py

# Follow on-screen instructions:
# 1. pH calibration with pH 4.0, 7.0, and 10.0 solutions
# 2. Turbidity calibration with distilled water and known standards
# 3. Temperature verification
```

### 5. Configuration

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration
nano config.yaml
```

Configure:
- Water quality thresholds
- Alert settings (email/SMS)
- Monitoring intervals
- Data retention policies

### 6. Test Installation

```bash
# Verify I2C devices
sudo i2cdetect -y 1
# Should show ADS1115 at address 0x48

# Test sensors
python3 -m src.sensors --test

# Test complete system
python3 main.py --test
```

### 7. Run the System

```bash
# Run in foreground (testing)
python3 main.py

# Run as background service
sudo ./setup.sh install
sudo systemctl start aquasentinel
sudo systemctl enable aquasentinel
```

## 📖 Usage

### Starting the Monitor

```bash
# Start monitoring
python3 main.py

# Start with custom config
python3 main.py --config /path/to/config.yaml

# Start in verbose mode
python3 main.py --verbose

# Run calibration
python3 calibrate.py
```

### Web Dashboard

Access at: `http://raspberrypi.local:8080` or `http://<PI_IP_ADDRESS>:8080`

Dashboard features:
- **Live View**: Real-time sensor readings
- **Quality Index**: Overall water quality score
- **History**: 24-hour trend graphs
- **Events**: Pollution event log
- **Alerts**: Alert history and status
- **Export**: Download data as CSV/JSON

### Command Line Interface

```bash
# View current readings
python3 main.py --status

# Export data
python3 main.py --export --format csv
python3 main.py --export --format json --start-date 2024-01-01

# Generate report
python3 main.py --report --days 7

# Test alerts
python3 main.py --test-alerts

# Clean old data
python3 main.py --cleanup --days 30

# Recalibrate sensors
python3 calibrate.py
```

## ⚙️ Configuration

### Water Quality Thresholds (`config.yaml`)

```yaml
thresholds:
  pH:
    excellent: [6.5, 8.5]    # Ideal pH range
    good: [6.0, 9.0]         # Acceptable range
    fair: [5.5, 9.5]         # Monitor closely
    # Outside ranges = poor/critical
  
  turbidity:
    excellent: [0, 5]        # NTU
    good: [5, 10]
    fair: [10, 25]
    poor: [25, 100]
    # Above 100 = critical
  
  temperature:
    excellent: [15, 25]      # °C
    good: [10, 30]
    fair: [5, 35]
    # Outside ranges = poor/critical
```

### Water Quality Classification

| Class | Description | Action |
|-------|-------------|--------|
| Excellent | All parameters optimal | Normal monitoring |
| Good | Within acceptable limits | Continue monitoring |
| Fair | Some parameters elevated | Increased monitoring |
| Poor | Parameters concerning | Investigation needed |
| Critical | Immediate pollution risk | Immediate action required |

### Pollution Event Detection

The system automatically detects:
- **Rapid pH changes** (>0.5 in 10 minutes)
- **Turbidity spikes** (>50% increase)
- **Temperature anomalies** (>5°C change)
- **Combined parameter degradation**
- **Sustained poor quality** (>1 hour)

### Alert Configuration

```yaml
alerts:
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: your-email@gmail.com
    password: your-app-password
    recipients:
      - alert1@example.com
      - alert2@example.com
  
  sms:
    enabled: true
    provider: twilio
    account_sid: your-sid
    auth_token: your-token
    from_number: +1234567890
    to_numbers:
      - +0987654321
  
  local:
    buzzer_enabled: true
    led_enabled: true
```

## 📊 Data Management

### Database Schema

```sql
-- Water quality readings
CREATE TABLE readings (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    pH REAL,
    turbidity REAL,
    temperature REAL,
    quality_class TEXT,
    quality_score INTEGER
);

-- Pollution events
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT,
    severity TEXT,
    description TEXT,
    pH REAL,
    turbidity REAL,
    temperature REAL,
    resolved INTEGER DEFAULT 0
);

-- Sensor calibration data
CREATE TABLE calibration (
    id INTEGER PRIMARY KEY,
    sensor_type TEXT,
    timestamp DATETIME,
    calibration_data TEXT
);
```

### Data Export

```bash
# Export all data
python3 main.py --export --output water_quality_data.csv

# Export specific date range
python3 main.py --export --start-date 2024-01-01 --end-date 2024-01-31

# Export as JSON
python3 main.py --export --format json

# Generate weekly report
python3 main.py --report --days 7 --output weekly_report.pdf
```

## 🔧 Troubleshooting

### Sensors Not Detected

```bash
# Check I2C connection
sudo i2cdetect -y 1

# If ADS1115 not showing at 0x48:
# 1. Check wiring
# 2. Verify 3.3V power supply
# 3. Try alternate address (0x49, 0x4A, 0x4B)

# Check 1-Wire devices
ls /sys/bus/w1/devices/
```

### Inaccurate Readings

1. **pH Sensor**:
   - Recalibrate with fresh buffer solutions
   - Check electrode condition
   - Ensure proper storage in KCl solution
   - Verify sensor is submerged in water

2. **Turbidity Sensor**:
   - Clean optical components
   - Recalibrate with distilled water
   - Check for ambient light interference
   - Verify proper orientation

3. **Temperature Sensor**:
   - Check waterproof seal
   - Verify proper submersion
   - Apply calibration offset if needed

### Calibration Issues

```bash
# Reset calibration
python3 calibrate.py --reset

# Verify calibration
python3 calibrate.py --verify

# View current calibration
python3 main.py --show-calibration
```

### Service Issues

```bash
# Check service status
sudo systemctl status aquasentinel

# View logs
sudo journalctl -u aquasentinel -f

# Restart service
sudo systemctl restart aquasentinel

# Check configuration
python3 main.py --validate-config
```

## 🏗️ Project Structure

```
aquasentinel-pi5/
│
├── main.py                 # Main application
├── calibrate.py           # Sensor calibration utility
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── setup.sh              # Installation script
├── aquasentinel.service  # Systemd service file
│
├── src/
│   ├── __init__.py
│   ├── sensors.py        # Sensor interfaces
│   ├── analyzer.py       # Water quality analysis
│   ├── classifier.py     # Quality classification
│   ├── alerts.py         # Alert system
│   ├── data_handler.py   # Database operations
│   └── web_dashboard.py  # Flask web interface
│
├── tests/
│   ├── test_sensors.py
│   ├── test_analyzer.py
│   └── test_classifier.py
│
├── docs/
│   ├── API.md
│   ├── CALIBRATION.md
│   └── DEPLOYMENT.md
│
├── logs/                  # Application logs
├── data/                  # Database and exports
└── static/               # Web dashboard assets
```

## 📈 Performance

- **Measurement Frequency**: 10 seconds (configurable)
- **Processing Latency**: < 50ms
- **Alert Response Time**: < 1 second
- **Data Storage**: ~500KB per day
- **CPU Usage**: < 10% on Raspberry Pi 5
- **Memory Usage**: ~120MB

## 🌍 Use Cases

### Environmental Monitoring
- Rivers and streams
- Lakes and reservoirs
- Coastal waters
- Wetlands

### Aquaculture
- Fish farms
- Shrimp ponds
- Aquaponics systems
- Hatcheries

### Industrial Applications
- Wastewater treatment
- Cooling systems
- Process water monitoring
- Compliance monitoring

### Research & Education
- Water quality studies
- Environmental science projects
- IoT and sensor technology education
- Citizen science initiatives

## 🔒 Security & Privacy

- All data stored locally (no cloud required)
- Optional encrypted database
- Password-protected web dashboard
- Network security best practices
- Secure API endpoints

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_sensors.py

# Run with coverage
pytest --cov=src tests/

# Test calibration
python3 calibrate.py --test
```

## 🛠️ Customization

### Adding Custom Sensors

1. Create sensor class in `src/sensors.py`
2. Implement `read()` method
3. Add calibration routine in `calibrate.py`
4. Update `config.yaml` with thresholds
5. Modify analyzer for new parameter

### Custom Water Quality Indexes

Edit `src/classifier.py` to implement custom classification algorithms based on local regulations or specific requirements.

### Integration with External Systems

The system provides REST API endpoints for integration:
- `GET /api/current` - Current readings
- `GET /api/history` - Historical data
- `GET /api/events` - Pollution events
- `GET /api/quality` - Water quality index

