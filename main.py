#!/usr/bin/env python3
"""
AquaSentinel-Pi5 - Smart Water Quality Monitoring System
Main Application Entry Point
"""

import argparse
import sys
import signal
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
import yaml

from src.sensors import SensorManager
from src.analyzer import WaterQualityAnalyzer
from src.classifier import WaterQualityClassifier
from src.alerts import AlertManager
from src.data_handler import DataHandler
from src.web_dashboard import create_app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aquasentinel.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AquaSentinelMonitor:
    """Main water quality monitoring system"""
    
    def __init__(self, config_path='config.yaml'):
        """Initialize the monitoring system"""
        self.running = False
        self.config = self.load_config(config_path)
        
        logger.info("Initializing AquaSentinel-Pi5 monitoring system...")
        
        try:
            # Initialize components
            self.data_handler = DataHandler(self.config['database']['path'])
            self.sensor_manager = SensorManager(self.config['sensors'])
            self.analyzer = WaterQualityAnalyzer(self.config['thresholds'])
            self.classifier = WaterQualityClassifier(self.config['thresholds'])
            self.alert_manager = AlertManager(
                self.config['alerts'],
                self.sensor_manager.indicators
            )
            
            logger.info("System initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            raise
    
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML configuration: {e}")
            sys.exit(1)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received")
        self.stop()
    
    def start(self):
        """Start the monitoring system"""
        self.running = True
        logger.info("Starting water quality monitoring...")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        measurement_interval = self.config['system']['measurement_interval']
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while self.running:
                try:
                    # Read sensor data
                    readings = self.sensor_manager.read_all()
                    
                    if readings:
                        # Classify water quality
                        classification = self.classifier.classify(readings)
                        readings['quality_class'] = classification['class']
                        readings['quality_score'] = classification['score']
                        
                        # Log readings
                        logger.info(
                            f"Readings: pH={readings.get('pH'):.2f}, "
                            f"Turbidity={readings.get('turbidity'):.1f} NTU, "
                            f"Temp={readings.get('temperature'):.1f}°C, "
                            f"Quality={classification['class']}"
                        )
                        
                        # Store in database
                        self.data_handler.save_reading(readings)
                        
                        # Analyze for pollution events
                        events = self.analyzer.analyze(readings)
                        
                        # Handle any events
                        if events:
                            for event in events:
                                logger.warning(f"Pollution Event: {event['description']}")
                                
                                # Create alert
                                alert = {
                                    'type': event['event_type'],
                                    'severity': event['severity'],
                                    'message': event['description'],
                                    'timestamp': datetime.now(),
                                    'pH': readings.get('pH'),
                                    'turbidity': readings.get('turbidity'),
                                    'temperature': readings.get('temperature')
                                }
                                
                                self.alert_manager.send_alert(alert)
                                self.data_handler.save_event(event)
                        
                        # Reset error counter
                        consecutive_errors = 0
                    
                    else:
                        consecutive_errors += 1
                        logger.warning(
                            f"Failed to read sensors ({consecutive_errors}/{max_consecutive_errors})"
                        )
                        
                        if consecutive_errors >= max_consecutive_errors:
                            error_alert = {
                                'type': 'system_error',
                                'severity': 'critical',
                                'message': 'Sensor communication failure',
                                'timestamp': datetime.now()
                            }
                            self.alert_manager.send_alert(error_alert)
                            consecutive_errors = 0
                    
                    # Wait for next measurement
                    time.sleep(measurement_interval)
                
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                    consecutive_errors += 1
                    time.sleep(measurement_interval)
        
        finally:
            self.cleanup()
    
    def stop(self):
        """Stop the monitoring system"""
        logger.info("Stopping monitoring system...")
        self.running = False
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources...")
        try:
            self.sensor_manager.cleanup()
            self.data_handler.close()
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_status(self):
        """Get current system status"""
        try:
            readings = self.sensor_manager.read_all()
            if readings:
                classification = self.classifier.classify(readings)
                return {
                    'status': 'operational',
                    'current_readings': readings,
                    'quality_class': classification['class'],
                    'quality_score': classification['score'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'sensor_error',
                    'message': 'Unable to read sensors',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def export_data(self, start_date=None, end_date=None, format='csv', output_file=None):
        """Export data to file"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"data/export_{timestamp}.{format}"
            
            if format == 'csv':
                self.data_handler.export_to_csv(output_file, start_date, end_date)
            elif format == 'json':
                self.data_handler.export_to_json(output_file, start_date, end_date)
            else:
                logger.error(f"Unsupported format: {format}")
                return None
            
            logger.info(f"Data exported to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return None
    
    def generate_report(self, days=7, output_file=None):
        """Generate water quality report"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d')
                output_file = f"data/report_{timestamp}.txt"
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Get data
            readings = self.data_handler.get_readings(start_date=start_date, limit=10000)
            events = self.data_handler.get_events(start_date=start_date, limit=1000)
            stats = self.data_handler.get_statistics(start_date=start_date)
            
            # Generate report
            with open(output_file, 'w') as f:
                f.write("=" * 60 + "\n")
                f.write("AquaSentinel-Pi5 Water Quality Report\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Report Period: {days} days\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Statistics
                f.write("-" * 60 + "\n")
                f.write("STATISTICS\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total Readings: {stats.get('count', 0)}\n")
                f.write(f"Average pH: {stats.get('avg_pH', 0):.2f}\n")
                f.write(f"Average Turbidity: {stats.get('avg_turbidity', 0):.2f} NTU\n")
                f.write(f"Average Temperature: {stats.get('avg_temperature', 0):.2f}°C\n\n")
                
                # Quality distribution
                f.write("-" * 60 + "\n")
                f.write("WATER QUALITY DISTRIBUTION\n")
                f.write("-" * 60 + "\n")
                quality_counts = self.data_handler.get_quality_distribution(start_date)
                for quality, count in quality_counts.items():
                    percentage = (count / stats.get('count', 1)) * 100
                    f.write(f"{quality}: {count} ({percentage:.1f}%)\n")
                f.write("\n")
                
                # Pollution events
                f.write("-" * 60 + "\n")
                f.write("POLLUTION EVENTS\n")
                f.write("-" * 60 + "\n")
                f.write(f"Total Events: {len(events)}\n\n")
                for event in events[:10]:  # Show last 10 events
                    f.write(f"[{event['timestamp']}] {event['event_type'].upper()}\n")
                    f.write(f"  Severity: {event['severity']}\n")
                    f.write(f"  Description: {event['description']}\n\n")
                
                f.write("=" * 60 + "\n")
            
            logger.info(f"Report generated: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='AquaSentinel-Pi5 - Smart Water Quality Monitoring'
    )
    
    parser.add_argument('--config', default='config.yaml', help='Configuration file')
    parser.add_argument('--status', action='store_true', help='Display current status')
    parser.add_argument('--export', action='store_true', help='Export data')
    parser.add_argument('--format', default='csv', choices=['csv', 'json'], help='Export format')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--report', action='store_true', help='Generate report')
    parser.add_argument('--days', type=int, default=7, help='Days for report')
    parser.add_argument('--test-alerts', action='store_true', help='Test alerts')
    parser.add_argument('--cleanup', action='store_true', help='Clean old data')
    parser.add_argument('--test', action='store_true', help='Test system')
    parser.add_argument('--web', action='store_true', help='Start web dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Web port')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    parser.add_argument('--validate-config', action='store_true', help='Validate config')
    parser.add_argument('--show-calibration', action='store_true', help='Show calibration')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        monitor = AquaSentinelMonitor(args.config)
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)
    
    if args.validate_config:
        logger.info("Configuration is valid")
        sys.exit(0)
    
    elif args.status:
        status = monitor.get_status()
        print("\n=== AquaSentinel-Pi5 Status ===")
        print(f"Status: {status['status']}")
        if 'current_readings' in status:
            r = status['current_readings']
            print(f"pH: {r.get('pH', 'N/A'):.2f}")
            print(f"Turbidity: {r.get('turbidity', 'N/A'):.1f} NTU")
            print(f"Temperature: {r.get('temperature', 'N/A'):.1f}°C")
            print(f"Quality: {status['quality_class']} ({status['quality_score']}/100)")
        print(f"Timestamp: {status['timestamp']}")
        print("=" * 30 + "\n")
    
    elif args.export:
        start = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
        end = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None
        output = monitor.export_data(start, end, args.format, args.output)
        if output:
            print(f"Data exported to: {output}")
    
    elif args.report:
        output = monitor.generate_report(args.days, args.output)
        if output:
            print(f"Report generated: {output}")
    
    elif args.test_alerts:
        alert = {
            'type': 'test',
            'severity': 'info',
            'message': 'Test alert from AquaSentinel-Pi5',
            'timestamp': datetime.now()
        }
        monitor.alert_manager.send_alert(alert)
        print("Test alert sent")
    
    elif args.cleanup:
        cutoff = datetime.now() - timedelta(days=args.days)
        monitor.data_handler.cleanup_old_data(cutoff)
        print(f"Cleaned data older than {args.days} days")
    
    elif args.show_calibration:
        cal = monitor.sensor_manager.get_calibration()
        print("\n=== Sensor Calibration ===")
        for sensor, data in cal.items():
            print(f"{sensor}: {data}")
        print("=" * 30 + "\n")
    
    elif args.test:
        print("Testing AquaSentinel-Pi5 system...\n")
        status = monitor.get_status()
        print(f"System Status: {status['status']}")
        if status['status'] == 'operational':
            print("✓ All systems operational")
        else:
            print("✗ System errors detected")
            print(f"Error: {status.get('message')}")
    
    elif args.web:
        app = create_app(monitor)
        logger.info(f"Starting web dashboard on port {args.port}")
        app.run(host='0.0.0.0', port=args.port, debug=args.verbose)
    
    else:
        logger.info("=" * 60)
        logger.info("AquaSentinel-Pi5 - Smart Water Quality Monitoring")
        logger.info("=" * 60)
        monitor.start()


if __name__ == '__main__':
    main()
