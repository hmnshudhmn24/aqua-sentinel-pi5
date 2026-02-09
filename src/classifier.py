"""
Water Quality Classifier Module
Classifies water quality based on sensor readings
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class WaterQualityClassifier:
    """Classifies water quality into categories"""
    
    QUALITY_CLASSES = ['excellent', 'good', 'fair', 'poor', 'critical']
    
    def __init__(self, thresholds: Dict):
        """
        Initialize classifier with threshold configuration
        
        Args:
            thresholds: Dictionary containing threshold values
        """
        self.thresholds = thresholds
        logger.info("Water quality classifier initialized")
    
    def classify(self, readings: Dict) -> Dict:
        """
        Classify water quality based on sensor readings
        
        Args:
            readings: Dictionary with pH, turbidity, temperature
            
        Returns:
            Dictionary with 'class', 'score', and 'details'
        """
        try:
            # Classify each parameter
            pH_class = self._classify_pH(readings.get('pH'))
            turbidity_class = self._classify_turbidity(readings.get('turbidity'))
            temp_class = self._classify_temperature(readings.get('temperature'))
            
            # Calculate overall classification (worst-case approach)
            overall_class = self._get_worst_class([pH_class, turbidity_class, temp_class])
            
            # Calculate quality score (0-100)
            score = self._calculate_score(pH_class, turbidity_class, temp_class)
            
            # Prepare details
            details = {
                'pH_class': pH_class,
                'turbidity_class': turbidity_class,
                'temperature_class': temp_class
            }
            
            return {
                'class': overall_class,
                'score': score,
                'details': details
            }
            
        except Exception as e:
            logger.error(f"Error classifying water quality: {e}")
            return {
                'class': 'unknown',
                'score': 0,
                'details': {}
            }
    
    def _classify_pH(self, pH: float) -> str:
        """Classify pH level"""
        if pH is None:
            return 'unknown'
        
        thresholds = self.thresholds.get('pH', {})
        
        excellent = thresholds.get('excellent', [6.5, 8.5])
        good = thresholds.get('good', [6.0, 9.0])
        fair = thresholds.get('fair', [5.5, 9.5])
        
        if excellent[0] <= pH <= excellent[1]:
            return 'excellent'
        elif good[0] <= pH <= good[1]:
            return 'good'
        elif fair[0] <= pH <= fair[1]:
            return 'fair'
        elif pH < 5.0 or pH > 10.0:
            return 'critical'
        else:
            return 'poor'
    
    def _classify_turbidity(self, turbidity: float) -> str:
        """Classify turbidity level"""
        if turbidity is None:
            return 'unknown'
        
        thresholds = self.thresholds.get('turbidity', {})
        
        excellent = thresholds.get('excellent', [0, 5])
        good = thresholds.get('good', [5, 10])
        fair = thresholds.get('fair', [10, 25])
        poor = thresholds.get('poor', [25, 100])
        
        if excellent[0] <= turbidity < excellent[1]:
            return 'excellent'
        elif good[0] <= turbidity < good[1]:
            return 'good'
        elif fair[0] <= turbidity < fair[1]:
            return 'fair'
        elif poor[0] <= turbidity < poor[1]:
            return 'poor'
        else:
            return 'critical'
    
    def _classify_temperature(self, temperature: float) -> str:
        """Classify water temperature"""
        if temperature is None:
            return 'unknown'
        
        thresholds = self.thresholds.get('temperature', {})
        
        excellent = thresholds.get('excellent', [15, 25])
        good = thresholds.get('good', [10, 30])
        fair = thresholds.get('fair', [5, 35])
        
        if excellent[0] <= temperature <= excellent[1]:
            return 'excellent'
        elif good[0] <= temperature <= good[1]:
            return 'good'
        elif fair[0] <= temperature <= fair[1]:
            return 'fair'
        elif temperature < 0 or temperature > 40:
            return 'critical'
        else:
            return 'poor'
    
    def _get_worst_class(self, classes: list) -> str:
        """Get worst classification from a list"""
        priority = {
            'critical': 0,
            'poor': 1,
            'fair': 2,
            'good': 3,
            'excellent': 4,
            'unknown': 5
        }
        
        valid_classes = [c for c in classes if c != 'unknown']
        if not valid_classes:
            return 'unknown'
        
        worst = min(valid_classes, key=lambda x: priority.get(x, 5))
        return worst
    
    def _calculate_score(self, pH_class: str, turbidity_class: str, temp_class: str) -> int:
        """
        Calculate overall water quality score (0-100)
        
        Higher score = better quality
        """
        class_scores = {
            'excellent': 100,
            'good': 80,
            'fair': 60,
            'poor': 40,
            'critical': 20,
            'unknown': 0
        }
        
        # Weighted average (pH: 40%, turbidity: 40%, temperature: 20%)
        score = (
            class_scores.get(pH_class, 0) * 0.4 +
            class_scores.get(turbidity_class, 0) * 0.4 +
            class_scores.get(temp_class, 0) * 0.2
        )
        
        return int(score)
    
    def get_classification_description(self, classification: str) -> str:
        """Get human-readable description of classification"""
        descriptions = {
            'excellent': 'Water quality is excellent. Safe for all uses including drinking (after proper treatment).',
            'good': 'Water quality is good. Generally safe for most uses with minimal treatment.',
            'fair': 'Water quality is fair. Suitable for uses with appropriate treatment. Monitor closely.',
            'poor': 'Water quality is poor. Not recommended for sensitive uses. Investigation recommended.',
            'critical': 'Water quality is critical. Immediate pollution event detected. Urgent action required.'
        }
        
        return descriptions.get(classification, 'Unknown water quality status.')
    
    def get_recommendations(self, classification: str) -> list:
        """Get recommendations based on classification"""
        recommendations = {
            'excellent': [
                'Continue routine monitoring',
                'Maintain current conditions',
                'Regular maintenance of monitoring equipment'
            ],
            'good': [
                'Continue monitoring',
                'Review any recent changes in water source',
                'Ensure proper filtration if used for drinking'
            ],
            'fair': [
                'Increase monitoring frequency',
                'Investigate potential sources of degradation',
                'Consider additional treatment measures',
                'Review environmental factors'
            ],
            'poor': [
                'Immediately increase monitoring frequency',
                'Investigate pollution sources',
                'Restrict use for sensitive applications',
                'Consider implementing corrective measures',
                'Notify relevant authorities if required'
            ],
            'critical': [
                'IMMEDIATE ACTION REQUIRED',
                'Stop use for all sensitive applications',
                'Identify and isolate pollution source',
                'Notify environmental authorities',
                'Implement emergency treatment measures',
                'Consider evacuation of affected areas if necessary'
            ]
        }
        
        return recommendations.get(classification, ['Consult water quality expert'])


if __name__ == '__main__':
    # Test classifier
    thresholds = {
        'pH': {
            'excellent': [6.5, 8.5],
            'good': [6.0, 9.0],
            'fair': [5.5, 9.5]
        },
        'turbidity': {
            'excellent': [0, 5],
            'good': [5, 10],
            'fair': [10, 25],
            'poor': [25, 100]
        },
        'temperature': {
            'excellent': [15, 25],
            'good': [10, 30],
            'fair': [5, 35]
        }
    }
    
    classifier = WaterQualityClassifier(thresholds)
    
    # Test cases
    test_cases = [
        {'pH': 7.2, 'turbidity': 3.5, 'temperature': 20.0},  # Excellent
        {'pH': 8.0, 'turbidity': 8.0, 'temperature': 28.0},  # Good
        {'pH': 9.2, 'turbidity': 15.0, 'temperature': 33.0},  # Fair
        {'pH': 5.0, 'turbidity': 50.0, 'temperature': 38.0},  # Poor
        {'pH': 4.5, 'turbidity': 150.0, 'temperature': 42.0},  # Critical
    ]
    
    for i, readings in enumerate(test_cases, 1):
        result = classifier.classify(readings)
        print(f"\nTest Case {i}:")
        print(f"  Readings: pH={readings['pH']}, Turbidity={readings['turbidity']}NTU, Temp={readings['temperature']}°C")
        print(f"  Classification: {result['class'].upper()}")
        print(f"  Score: {result['score']}/100")
        print(f"  Description: {classifier.get_classification_description(result['class'])}")
