"""
Sensor Interface Module
Handles pH, Turbidity, and Temperature sensors
"""

import time
import logging
import json
from typing import Dict, Optional
import random

logger = logging.getLogger(__name__)

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
    HAS_ADS1115 = True
except ImportError:
    logger.warning("ADS1115 library not available, using simulation mode")
    HAS_ADS1115 = False

try:
    from w1thermsensor import W1ThermSensor
    HAS_DS18B20 = True
except ImportError:
    logger.warning("DS18B20 library not available, using simulation mode")
    HAS_DS18B20 = False

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    logger.warning("GPIO library not available, using simulation mode")
    HAS_GPIO = False


class PHSensor:
    """pH Sensor (Analog via ADS1115)"""
    
    def __init__(self, adc, channel, config: Dict):
        """Initialize pH sensor"""
        self.adc = adc
        self.channel = channel
        self.config = config
        self.simulation_mode = adc is None
        
        # Load calibration data
        self.calibration = config.get('calibration', {
            'slope': 3.5,  # Default: 3.5V per pH unit
            'offset': 7.0,  # Default: pH 7 at 2.5V
            'voltage_at_7': 2.5
        })
        
        if self.simulation_mode:
            logger.info("pH sensor running in simulation mode")
        else:
            logger.info("pH sensor initialized on channel {}".format(channel))
    
    def read(self) -> Optional[float]:
        """
        Read pH value
        
        Returns:
            pH value (0-14), or None if read fails
        """
        if self.simulation_mode:
            return self._simulate_reading()
        
        try:
            # Read voltage from ADC
            voltage = self.adc.voltage
            
            # Convert voltage to pH using calibration
            pH = self._voltage_to_pH(voltage)
            
            # Validate reading
            if 0 <= pH <= 14:
                return round(pH, 2)
            else:
                logger.warning(f"Invalid pH reading: {pH}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading pH sensor: {e}")
            return None
    
    def _voltage_to_pH(self, voltage: float) -> float:
        """Convert voltage to pH using calibration data"""
        # Linear conversion: pH = (voltage - voltage_at_7) / slope + 7
        slope = self.calibration['slope'] / 7.0  # Voltage per pH unit
        offset_voltage = self.calibration['voltage_at_7']
        
        pH = ((voltage - offset_voltage) / slope) + 7.0
        return pH
    
    def calibrate(self, calibration_points: Dict):
        """
        Calibrate sensor with known pH buffers
        
        Args:
            calibration_points: Dict of {pH: voltage} pairs
        """
        if len(calibration_points) < 2:
            logger.error("Need at least 2 calibration points")
            return False
        
        try:
            # Use linear regression for calibration
            pH_values = list(calibration_points.keys())
            voltages = list(calibration_points.values())
            
            # Calculate slope and offset
            n = len(pH_values)
            sum_pH = sum(pH_values)
            sum_v = sum(voltages)
            sum_pH_v = sum(pH * v for pH, v in zip(pH_values, voltages))
            sum_pH_sq = sum(pH * pH for pH in pH_values)
            
            slope = (n * sum_pH_v - sum_pH * sum_v) / (n * sum_pH_sq - sum_pH * sum_pH)
            offset = (sum_v - slope * sum_pH) / n
            
            self.calibration['slope'] = slope
            self.calibration['offset'] = offset
            self.calibration['voltage_at_7'] = offset + 7.0 * slope
            
            logger.info(f"pH sensor calibrated: slope={slope:.4f}, offset={offset:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return False
    
    def _simulate_reading(self) -> float:
        """Simulate pH reading for testing"""
        base_pH = 7.2
        return round(base_pH + random.uniform(-0.3, 0.3), 2)


class TurbiditySensor:
    """Turbidity Sensor (Analog via ADS1115)"""
    
    def __init__(self, adc, channel, config: Dict):
        """Initialize turbidity sensor"""
        self.adc = adc
        self.channel = channel
        self.config = config
        self.simulation_mode = adc is None
        
        # Load calibration data
        self.calibration = config.get('calibration', {
            'clear_water_voltage': 4.2,  # Voltage for clear water
            'max_turbidity': 3000,  # Maximum NTU
            'min_voltage': 0.5  # Voltage at max turbidity
        })
        
        if self.simulation_mode:
            logger.info("Turbidity sensor running in simulation mode")
        else:
            logger.info("Turbidity sensor initialized on channel {}".format(channel))
    
    def read(self) -> Optional[float]:
        """
        Read turbidity value
        
        Returns:
            Turbidity in NTU, or None if read fails
        """
        if self.simulation_mode:
            return self._simulate_reading()
        
        try:
            # Read voltage from ADC
            voltage = self.adc.voltage
            
            # Convert voltage to NTU using calibration
            turbidity = self._voltage_to_ntu(voltage)
            
            # Validate reading
            if 0 <= turbidity <= 5000:
                return round(turbidity, 1)
            else:
                logger.warning(f"Invalid turbidity reading: {turbidity}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading turbidity sensor: {e}")
            return None
    
    def _voltage_to_ntu(self, voltage: float) -> float:
        """Convert voltage to NTU using calibration data"""
        clear_voltage = self.calibration['clear_water_voltage']
        min_voltage = self.calibration['min_voltage']
        max_turbidity = self.calibration['max_turbidity']
        
        # Inverse relationship: lower voltage = higher turbidity
        if voltage >= clear_voltage:
            return 0.0
        
        # Linear mapping
        ntu = max_turbidity * (clear_voltage - voltage) / (clear_voltage - min_voltage)
        return max(0, ntu)
    
    def calibrate(self, clear_water_voltage: float):
        """
        Calibrate sensor with clear water reading
        
        Args:
            clear_water_voltage: Voltage reading in clear/distilled water
        """
        self.calibration['clear_water_voltage'] = clear_water_voltage
        logger.info(f"Turbidity sensor calibrated: clear={clear_water_voltage:.2f}V")
        return True
    
    def _simulate_reading(self) -> float:
        """Simulate turbidity reading for testing"""
        base_ntu = 8.5
        return round(base_ntu + random.uniform(-2, 4), 1)


class TemperatureSensor:
    """DS18B20 Waterproof Temperature Sensor"""
    
    def __init__(self, config: Dict):
        """Initialize temperature sensor"""
        self.config = config
        self.sensor = None
        self.simulation_mode = not HAS_DS18B20
        
        if not self.simulation_mode:
            try:
                self.sensor = W1ThermSensor()
                logger.info(f"Temperature sensor initialized: {self.sensor.id}")
            except Exception as e:
                logger.error(f"Failed to initialize DS18B20: {e}")
                self.simulation_mode = True
        
        if self.simulation_mode:
            logger.info("Temperature sensor running in simulation mode")
    
    def read(self) -> Optional[float]:
        """
        Read temperature value
        
        Returns:
            Temperature in Celsius, or None if read fails
        """
        if self.simulation_mode:
            return self._simulate_reading()
        
        try:
            temperature = self.sensor.get_temperature()
            
            # Apply calibration offset
            offset = self.config.get('calibration_offset', 0.0)
            temperature += offset
            
            # Validate reading
            if -10 <= temperature <= 50:
                return round(temperature, 1)
            else:
                logger.warning(f"Invalid temperature reading: {temperature}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading temperature sensor: {e}")
            return None
    
    def _simulate_reading(self) -> float:
        """Simulate temperature reading for testing"""
        base_temp = 22.5
        return round(base_temp + random.uniform(-1, 2), 1)


class StatusIndicators:
    """LED and Buzzer indicators"""
    
    def __init__(self, config: Dict):
        """Initialize GPIO indicators"""
        self.config = config
        self.simulation_mode = not HAS_GPIO
        
        if not self.simulation_mode:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setwarnings(False)
                
                self.led_red = config.get('led_red_pin', 22)
                self.led_green = config.get('led_green_pin', 27)
                self.led_blue = config.get('led_blue_pin', 23)
                self.buzzer = config.get('buzzer_pin', 17)
                
                GPIO.setup(self.led_red, GPIO.OUT)
                GPIO.setup(self.led_green, GPIO.OUT)
                GPIO.setup(self.led_blue, GPIO.OUT)
                GPIO.setup(self.buzzer, GPIO.OUT)
                
                self.set_led('off')
                GPIO.output(self.buzzer, GPIO.LOW)
                
                logger.info("Status indicators initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GPIO: {e}")
                self.simulation_mode = True
        
        if self.simulation_mode:
            logger.info("Status indicators in simulation mode")
    
    def set_led(self, color: str):
        """Set LED color based on water quality"""
        if self.simulation_mode:
            logger.debug(f"[SIM] LED: {color}")
            return
        
        colors = {
            'off': (0, 0, 0),
            'red': (1, 0, 0),      # Critical
            'yellow': (1, 1, 0),    # Poor
            'orange': (1, 0.5, 0),  # Fair
            'green': (0, 1, 0),     # Good
            'blue': (0, 0, 1),      # Excellent
            'white': (1, 1, 1)
        }
        
        if color in colors:
            r, g, b = colors[color]
            GPIO.output(self.led_red, r)
            GPIO.output(self.led_green, g)
            GPIO.output(self.led_blue, b)
    
    def beep(self, duration=0.2, count=1):
        """Sound buzzer"""
        if self.simulation_mode:
            logger.debug(f"[SIM] Beep: {count}x")
            return
        
        for _ in range(count):
            GPIO.output(self.buzzer, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.buzzer, GPIO.LOW)
            time.sleep(duration)
    
    def cleanup(self):
        """Cleanup GPIO"""
        if not self.simulation_mode:
            GPIO.cleanup()


class SensorManager:
    """Manages all water quality sensors"""
    
    def __init__(self, config: Dict):
        """Initialize all sensors"""
        self.config = config
        self.simulation_mode = not HAS_ADS1115
        
        # Initialize ADC
        if not self.simulation_mode:
            try:
                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                
                # Create analog input channels
                self.pH_adc = AnalogIn(ads, ADS.P0)
                self.turbidity_adc = AnalogIn(ads, ADS.P1)
                
                logger.info("ADS1115 ADC initialized")
            except Exception as e:
                logger.error(f"Failed to initialize ADS1115: {e}")
                self.simulation_mode = True
                self.pH_adc = None
                self.turbidity_adc = None
        else:
            self.pH_adc = None
            self.turbidity_adc = None
        
        # Initialize sensors
        self.pH_sensor = PHSensor(
            self.pH_adc,
            config.get('pH', {}).get('channel', 0),
            config.get('pH', {})
        )
        
        self.turbidity_sensor = TurbiditySensor(
            self.turbidity_adc,
            config.get('turbidity', {}).get('channel', 1),
            config.get('turbidity', {})
        )
        
        self.temperature_sensor = TemperatureSensor(
            config.get('temperature', {})
        )
        
        self.indicators = StatusIndicators(
            config.get('indicators', {})
        )
        
        logger.info("Sensor manager initialized")
    
    def read_all(self) -> Optional[Dict]:
        """Read all sensors"""
        try:
            # Read all sensors
            pH = self.pH_sensor.read()
            turbidity = self.turbidity_sensor.read()
            temperature = self.temperature_sensor.read()
            
            # Verify all readings are valid
            if pH is not None and turbidity is not None and temperature is not None:
                readings = {
                    'pH': pH,
                    'turbidity': turbidity,
                    'temperature': temperature,
                    'timestamp': time.time()
                }
                
                return readings
            else:
                logger.warning("Failed to read one or more sensors")
                return None
                
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
            return None
    
    def get_calibration(self) -> Dict:
        """Get calibration data for all sensors"""
        return {
            'pH': self.pH_sensor.calibration,
            'turbidity': self.turbidity_sensor.calibration,
            'temperature': self.temperature_sensor.config.get('calibration_offset', 0.0)
        }
    
    def save_calibration(self, filepath='data/calibration.json'):
        """Save calibration data to file"""
        try:
            calibration = self.get_calibration()
            with open(filepath, 'w') as f:
                json.dump(calibration, f, indent=2)
            logger.info(f"Calibration saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return False
    
    def load_calibration(self, filepath='data/calibration.json'):
        """Load calibration data from file"""
        try:
            with open(filepath, 'r') as f:
                calibration = json.load(f)
            
            self.pH_sensor.calibration = calibration.get('pH', {})
            self.turbidity_sensor.calibration = calibration.get('turbidity', {})
            
            logger.info(f"Calibration loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return False
    
    def cleanup(self):
        """Cleanup all sensors"""
        logger.info("Cleaning up sensors")
        self.indicators.cleanup()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Test sensors')
    args = parser.parse_args()
    
    if args.test:
        print("Testing AquaSentinel-Pi5 Sensors\n")
        
        config = {
            'pH': {'channel': 0, 'calibration': {}},
            'turbidity': {'channel': 1, 'calibration': {}},
            'temperature': {'calibration_offset': 0.0},
            'indicators': {}
        }
        
        manager = SensorManager(config)
        
        print("Reading sensors for 10 seconds...\n")
        for i in range(10):
            readings = manager.read_all()
            if readings:
                print(f"Reading {i+1}:")
                print(f"  pH: {readings['pH']:.2f}")
                print(f"  Turbidity: {readings['turbidity']:.1f} NTU")
                print(f"  Temperature: {readings['temperature']:.1f}°C")
                print()
            else:
                print(f"Reading {i+1}: Failed\n")
            
            time.sleep(1)
        
        manager.cleanup()
        print("Test complete")
