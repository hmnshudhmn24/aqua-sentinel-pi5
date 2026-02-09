"""
Water Quality Analyzer Module
Detects pollution events and analyzes trends
"""

import logging
from typing import Dict, List
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class WaterQualityAnalyzer:
    """Analyzes water quality trends and detects pollution events"""
    
    def __init__(self, thresholds: Dict):
        """
        Initialize analyzer
        
        Args:
            thresholds: Dictionary containing threshold values
        """
        self.thresholds = thresholds
        
        # Historical data for trend analysis (last 60 readings)
        self.pH_history = deque(maxlen=60)
        self.turbidity_history = deque(maxlen=60)
        self.temperature_history = deque(maxlen=60)
        
        # Event cooldown tracking
        self.last_event_time = {}
        self.event_cooldown = 300  # 5 minutes
        
        logger.info("Water quality analyzer initialized")
    
    def analyze(self, readings: Dict) -> List[Dict]:
        """
        Analyze readings for pollution events
        
        Args:
            readings: Dictionary with pH, turbidity, temperature
            
        Returns:
            List of pollution event dictionaries
        """
        events = []
        
        try:
            # Update history
            if 'pH' in readings:
                self.pH_history.append(readings['pH'])
            if 'turbidity' in readings:
                self.turbidity_history.append(readings['turbidity'])
            if 'temperature' in readings:
                self.temperature_history.append(readings['temperature'])
            
            # Check for various pollution events
            events.extend(self._check_pH_events(readings))
            events.extend(self._check_turbidity_events(readings))
            events.extend(self._check_temperature_events(readings))
            events.extend(self._check_combined_events(readings))
            events.extend(self._check_trend_events())
            
            # Apply cooldown filter
            events = self._apply_cooldown(events)
            
            return events
            
        except Exception as e:
            logger.error(f"Error analyzing water quality: {e}")
            return []
    
    def _check_pH_events(self, readings: Dict) -> List[Dict]:
        """Check for pH-related pollution events"""
        events = []
        
        if 'pH' not in readings:
            return events
        
        pH = readings['pH']
        
        # Critical pH levels
        if pH < 5.0:
            events.append({
                'event_type': 'pH_critical_low',
                'severity': 'critical',
                'description': f'Critical acidic pH detected: {pH:.2f} (Possible industrial discharge)',
                'pH': pH,
                'turbidity': readings.get('turbidity'),
                'temperature': readings.get('temperature'),
                'timestamp': datetime.now()
            })
        
        elif pH > 10.0:
            events.append({
                'event_type': 'pH_critical_high',
                'severity': 'critical',
                'description': f'Critical alkaline pH detected: {pH:.2f} (Possible chemical spill)',
                'pH': pH,
                'turbidity': readings.get('turbidity'),
                'temperature': readings.get('temperature'),
                'timestamp': datetime.now()
            })
        
        # Poor pH levels
        elif pH < 5.5:
            events.append({
                'event_type': 'pH_low',
                'severity': 'warning',
                'description': f'Acidic pH detected: {pH:.2f}',
                'pH': pH,
                'turbidity': readings.get('turbidity'),
                'temperature': readings.get('temperature'),
                'timestamp': datetime.now()
            })
        
        elif pH > 9.5:
            events.append({
                'event_type': 'pH_high',
                'severity': 'warning',
                'description': f'Alkaline pH detected: {pH:.2f}',
                'pH': pH,
                'turbidity': readings.get('turbidity'),
                'temperature': readings.get('temperature'),
                'timestamp': datetime.now()
            })
        
        # Rapid pH change
        if len(self.pH_history) >= 6:  # Last minute of data (10s intervals)
            recent_pH = list(self.pH_history)[-6:]
            pH_change = max(recent_pH) - min(recent_pH)
            
            if pH_change > 0.5:
                events.append({
                    'event_type': 'pH_rapid_change',
                    'severity': 'warning',
                    'description': f'Rapid pH change detected: {pH_change:.2f} units in 1 minute',
                    'pH': pH,
                    'turbidity': readings.get('turbidity'),
                    'temperature': readings.get('temperature'),
                    'timestamp': datetime.now()
                })
        
        return events
    
    def _check_turbidity_events(self, readings: Dict) -> List[Dict]:
        """Check for turbidity-related pollution events"""
        events = []
        
        if 'turbidity' not in readings:
            return events
        
        turbidity = readings['turbidity']
        
        # Critical turbidity
        if turbidity > 100:
            events.append({
                'event_type': 'turbidity_critical',
                'severity': 'critical',
                'description': f'Critical turbidity level: {turbidity:.1f} NTU (Possible sediment spill or algae bloom)',
                'pH': readings.get('pH'),
                'turbidity': turbidity,
                'temperature': readings.get('temperature'),
                'timestamp': datetime.now()
            })
        
        # High turbidity
        elif turbidity > 25:
            events.append({
                'event_type': 'turbidity_high',
                'severity': 'warning',
                'description': f'High turbidity detected: {turbidity:.1f} NTU',
                'pH': readings.get('pH'),
                'turbidity': turbidity,
                'temperature': readings.get('temperature'),
                'timestamp': datetime.now()
            })
        
        # Turbidity spike
        if len(self.turbidity_history) >= 6:
            recent_turbidity = list(self.turbidity_history)[-6:]
            previous_avg = sum(recent_turbidity[:-1]) / 5
            
            if previous_avg > 0:
                increase_percent = ((turbidity - previous_avg) / previous_avg) * 100
                
                if increase_percent > 50:
                    events.append({
                        'event_type': 'turbidity_spike',
                        'severity': 'warning',
                        'description': f'Turbidity spike detected: {increase_percent:.0f}% increase',
                        'pH': readings.get('pH'),
                        'turbidity': turbidity,
                        'temperature': readings.get('temperature'),
                        'timestamp': datetime.now()
                    })
        
        return events
    
    def _check_temperature_events(self, readings: Dict) -> List[Dict]:
        """Check for temperature-related pollution events"""
        events = []
        
        if 'temperature' not in readings:
            return events
        
        temperature = readings['temperature']
        
        # Extreme temperatures
        if temperature < 0 or temperature > 40:
            events.append({
                'event_type': 'temperature_extreme',
                'severity': 'critical',
                'description': f'Extreme water temperature: {temperature:.1f}°C',
                'pH': readings.get('pH'),
                'turbidity': readings.get('turbidity'),
                'temperature': temperature,
                'timestamp': datetime.now()
            })
        
        # Rapid temperature change
        if len(self.temperature_history) >= 6:
            recent_temp = list(self.temperature_history)[-6:]
            temp_change = abs(max(recent_temp) - min(recent_temp))
            
            if temp_change > 5:
                events.append({
                    'event_type': 'temperature_rapid_change',
                    'severity': 'warning',
                    'description': f'Rapid temperature change: {temp_change:.1f}°C in 1 minute (Possible thermal pollution)',
                    'pH': readings.get('pH'),
                    'turbidity': readings.get('turbidity'),
                    'temperature': temperature,
                    'timestamp': datetime.now()
                })
        
        return events
    
    def _check_combined_events(self, readings: Dict) -> List[Dict]:
        """Check for multi-parameter pollution events"""
        events = []
        
        pH = readings.get('pH')
        turbidity = readings.get('turbidity')
        temperature = readings.get('temperature')
        
        if pH is None or turbidity is None or temperature is None:
            return events
        
        # Combined poor conditions
        poor_conditions = 0
        
        if pH < 6.0 or pH > 9.0:
            poor_conditions += 1
        if turbidity > 25:
            poor_conditions += 1
        if temperature < 10 or temperature > 30:
            poor_conditions += 1
        
        if poor_conditions >= 2:
            events.append({
                'event_type': 'multi_parameter_degradation',
                'severity': 'critical',
                'description': f'Multiple parameters degraded: pH={pH:.2f}, Turbidity={turbidity:.1f}NTU, Temp={temperature:.1f}°C',
                'pH': pH,
                'turbidity': turbidity,
                'temperature': temperature,
                'timestamp': datetime.now()
            })
        
        return events
    
    def _check_trend_events(self) -> List[Dict]:
        """Check for concerning trends"""
        events = []
        
        # Check for sustained poor quality
        if len(self.pH_history) >= 30:  # 5 minutes of data
            recent_pH = list(self.pH_history)[-30:]
            
            # Count readings outside acceptable range
            poor_count = sum(1 for pH in recent_pH if pH < 6.5 or pH > 8.5)
            
            if poor_count > 20:  # >66% of readings
                events.append({
                    'event_type': 'sustained_poor_pH',
                    'severity': 'warning',
                    'description': 'pH outside acceptable range for extended period',
                    'timestamp': datetime.now()
                })
        
        # Check turbidity trend
        if len(self.turbidity_history) >= 30:
            recent_turbidity = list(self.turbidity_history)[-30:]
            
            # Check if turbidity is consistently increasing
            first_half = sum(recent_turbidity[:15]) / 15
            second_half = sum(recent_turbidity[15:]) / 15
            
            if second_half > first_half * 1.5:
                events.append({
                    'event_type': 'increasing_turbidity_trend',
                    'severity': 'info',
                    'description': 'Turbidity showing increasing trend',
                    'timestamp': datetime.now()
                })
        
        return events
    
    def _apply_cooldown(self, events: List[Dict]) -> List[Dict]:
        """Filter events based on cooldown period"""
        filtered_events = []
        current_time = datetime.now()
        
        for event in events:
            event_key = f"{event['event_type']}_{event['severity']}"
            
            if event_key in self.last_event_time:
                time_since_last = (current_time - self.last_event_time[event_key]).total_seconds()
                
                if time_since_last < self.event_cooldown:
                    logger.debug(f"Event cooldown active for {event_key}")
                    continue
            
            self.last_event_time[event_key] = current_time
            filtered_events.append(event)
        
        return filtered_events
    
    def get_statistics(self) -> Dict:
        """Get statistics from historical data"""
        stats = {}
        
        if self.pH_history:
            pH_list = list(self.pH_history)
            stats['pH'] = {
                'current': pH_list[-1],
                'average': sum(pH_list) / len(pH_list),
                'min': min(pH_list),
                'max': max(pH_list)
            }
        
        if self.turbidity_history:
            turb_list = list(self.turbidity_history)
            stats['turbidity'] = {
                'current': turb_list[-1],
                'average': sum(turb_list) / len(turb_list),
                'min': min(turb_list),
                'max': max(turb_list)
            }
        
        if self.temperature_history:
            temp_list = list(self.temperature_history)
            stats['temperature'] = {
                'current': temp_list[-1],
                'average': sum(temp_list) / len(temp_list),
                'min': min(temp_list),
                'max': max(temp_list)
            }
        
        return stats


if __name__ == '__main__':
    # Test analyzer
    thresholds = {
        'pH': {'excellent': [6.5, 8.5]},
        'turbidity': {'excellent': [0, 5]},
        'temperature': {'excellent': [15, 25]}
    }
    
    analyzer = WaterQualityAnalyzer(thresholds)
    
    # Test normal readings
    print("Test 1: Normal readings")
    normal = {'pH': 7.2, 'turbidity': 4.0, 'temperature': 20.0}
    events = analyzer.analyze(normal)
    print(f"Events: {len(events)}\n")
    
    # Test pollution event
    print("Test 2: Pollution event")
    polluted = {'pH': 4.5, 'turbidity': 150.0, 'temperature': 35.0}
    events = analyzer.analyze(polluted)
    for event in events:
        print(f"- {event['severity'].upper()}: {event['description']}")
