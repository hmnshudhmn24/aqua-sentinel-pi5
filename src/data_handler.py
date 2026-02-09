"""
Data Handler Module
Database operations for water quality data
"""

import sqlite3
import csv
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataHandler:
    """Handles data storage and retrieval"""
    
    def __init__(self, db_path='data/aquasentinel.db'):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pH REAL,
                turbidity REAL,
                temperature REAL,
                quality_class TEXT,
                quality_score INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                severity TEXT,
                description TEXT,
                pH REAL,
                turbidity REAL,
                temperature REAL,
                resolved INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                calibration_data TEXT
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
        
        self.conn.commit()
    
    def save_reading(self, readings: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO readings (pH, turbidity, temperature, quality_class, quality_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                readings.get('pH'),
                readings.get('turbidity'),
                readings.get('temperature'),
                readings.get('quality_class'),
                readings.get('quality_score')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save reading: {e}")
            return False
    
    def save_event(self, event: Dict) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO events (timestamp, event_type, severity, description, pH, turbidity, temperature)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get('timestamp', datetime.now()),
                event.get('event_type'),
                event.get('severity'),
                event.get('description'),
                event.get('pH'),
                event.get('turbidity'),
                event.get('temperature')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save event: {e}")
            return False
    
    def get_readings(self, start_date=None, end_date=None, limit=100):
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM readings WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get readings: {e}")
            return []
    
    def get_events(self, start_date=None, end_date=None, severity=None, limit=100):
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM events WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    def get_statistics(self, start_date=None, end_date=None):
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    COUNT(*) as count,
                    AVG(pH) as avg_pH,
                    MIN(pH) as min_pH,
                    MAX(pH) as max_pH,
                    AVG(turbidity) as avg_turbidity,
                    MIN(turbidity) as min_turbidity,
                    MAX(turbidity) as max_turbidity,
                    AVG(temperature) as avg_temperature,
                    MIN(temperature) as min_temperature,
                    MAX(temperature) as max_temperature
                FROM readings WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            cursor.execute(query, params)
            return dict(cursor.fetchone()) if cursor.fetchone() else {}
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def get_quality_distribution(self, start_date=None):
        try:
            cursor = self.conn.cursor()
            query = "SELECT quality_class, COUNT(*) as count FROM readings WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            query += " GROUP BY quality_class"
            cursor.execute(query, params)
            
            return {row['quality_class']: row['count'] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get distribution: {e}")
            return {}
    
    def export_to_csv(self, output_file, start_date=None, end_date=None):
        try:
            readings = self.get_readings(start_date, end_date, limit=100000)
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'pH', 'Turbidity (NTU)', 'Temperature (°C)', 'Quality Class', 'Quality Score'])
                
                for r in readings:
                    writer.writerow([
                        r['timestamp'], r['pH'], r['turbidity'], 
                        r['temperature'], r['quality_class'], r['quality_score']
                    ])
            
            logger.info(f"Exported {len(readings)} readings to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def export_to_json(self, output_file, start_date=None, end_date=None):
        try:
            readings = self.get_readings(start_date, end_date, limit=100000)
            
            with open(output_file, 'w') as f:
                json.dump(readings, f, indent=2, default=str)
            
            logger.info(f"Exported {len(readings)} readings to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def cleanup_old_data(self, cutoff_date):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM readings WHERE timestamp < ?", (cutoff_date,))
            readings_deleted = cursor.rowcount
            cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_date,))
            events_deleted = cursor.rowcount
            self.conn.commit()
            logger.info(f"Deleted {readings_deleted + events_deleted} old records")
            return readings_deleted + events_deleted
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database closed")
