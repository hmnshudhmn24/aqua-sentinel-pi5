"""Tests for water quality classifier"""
import sys
sys.path.insert(0, '..')
from src.classifier import WaterQualityClassifier

def test_excellent_quality():
    thresholds = {
        'pH': {'excellent': [6.5, 8.5]},
        'turbidity': {'excellent': [0, 5]},
        'temperature': {'excellent': [15, 25]}
    }
    classifier = WaterQualityClassifier(thresholds)
    result = classifier.classify({'pH': 7.2, 'turbidity': 3.0, 'temperature': 20.0})
    assert result['class'] == 'excellent'
    assert result['score'] >= 80

def test_poor_quality():
    thresholds = {
        'pH': {'excellent': [6.5, 8.5], 'good': [6.0, 9.0]},
        'turbidity': {'excellent': [0, 5], 'good': [5, 10]},
        'temperature': {'excellent': [15, 25], 'good': [10, 30]}
    }
    classifier = WaterQualityClassifier(thresholds)
    result = classifier.classify({'pH': 5.0, 'turbidity': 50.0, 'temperature': 35.0})
    assert result['class'] in ['poor', 'critical']
