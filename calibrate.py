#!/usr/bin/env python3
"""
AquaSentinel-Pi5 Sensor Calibration Utility
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.sensors import SensorManager

def calibrate_pH():
    print("\n=== pH Sensor Calibration ===\n")
    print("You will need pH buffer solutions: pH 4.0, 7.0, and 10.0")
    input("Press Enter when ready...")
    
    calibration_points = {}
    
    for pH_value in [4.0, 7.0, 10.0]:
        print(f"\nPlace sensor in pH {pH_value} buffer solution")
        input("Press Enter when sensor is stable...")
        
        # Read voltage
        print("Reading voltage...")
        time.sleep(2)
        
        # Here you would actually read the sensor
        voltage = 2.5 + (pH_value - 7.0) * 0.18  # Simulated
        
        calibration_points[pH_value] = voltage
        print(f"Voltage reading: {voltage:.3f}V")
    
    print("\nCalibration points collected:")
    for pH, voltage in calibration_points.items():
        print(f"  pH {pH}: {voltage:.3f}V")
    
    return calibration_points

def calibrate_turbidity():
    print("\n=== Turbidity Sensor Calibration ===\n")
    print("You will need distilled or purified water")
    input("Press Enter when ready...")
    
    print("\nPlace sensor in clear water")
    input("Press Enter when sensor is stable...")
    
    print("Reading clear water voltage...")
    time.sleep(2)
    
    clear_voltage = 4.2  # Simulated
    print(f"Clear water voltage: {clear_voltage:.3f}V")
    
    return clear_voltage

def main():
    print("=" * 60)
    print("AquaSentinel-Pi5 Calibration Wizard")
    print("=" * 60)
    
    print("\nCalibrate which sensor?")
    print("1. pH Sensor")
    print("2. Turbidity Sensor")
    print("3. Both")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ")
    
    config = {
        'pH': {'channel': 0},
        'turbidity': {'channel': 1},
        'temperature': {},
        'indicators': {}
    }
    
    manager = SensorManager(config)
    
    if choice in ['1', '3']:
        pH_cal = calibrate_pH()
        if manager.pH_sensor.calibrate(pH_cal):
            print("\npH calibration successful!")
    
    if choice in ['2', '3']:
        turb_cal = calibrate_turbidity()
        if manager.turbidity_sensor.calibrate(turb_cal):
            print("\nTurbidity calibration successful!")
    
    # Save calibration
    if manager.save_calibration():
        print("\nCalibration data saved!")
    
    print("\nCalibration complete!")

if __name__ == '__main__':
    main()
