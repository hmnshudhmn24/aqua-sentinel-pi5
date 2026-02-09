"""
AquaSentinel-Pi5 Source Package
Smart Water Quality Monitoring System
"""

__version__ = '1.0.0'
__author__ = 'AquaSentinel Team'

from .sensors import SensorManager
from .analyzer import WaterQualityAnalyzer
from .classifier import WaterQualityClassifier
from .alerts import AlertManager
from .data_handler import DataHandler

__all__ = [
    'SensorManager',
    'WaterQualityAnalyzer',
    'WaterQualityClassifier',
    'AlertManager',
    'DataHandler'
]
