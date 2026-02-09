"""
Alert Management Module
Multi-channel notifications for water quality events
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False


class EmailAlert:
    """Email notification handler"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        
        if self.enabled:
            self.smtp_server = config.get('smtp_server')
            self.smtp_port = config.get('smtp_port', 587)
            self.username = config.get('username')
            self.password = config.get('password')
            self.recipients = config.get('recipients', [])
            logger.info("Email alerts enabled")
    
    def send(self, alert: Dict) -> bool:
        if not self.enabled:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"AquaSentinel Alert: {alert['severity'].upper()}"
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            
            body = f"""
AquaSentinel-Pi5 Water Quality Alert

SEVERITY: {alert['severity'].upper()}
TYPE: {alert['type']}
TIME: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

MESSAGE:
{alert['message']}

WATER PARAMETERS:
- pH: {alert.get('pH', 'N/A')}
- Turbidity: {alert.get('turbidity', 'N/A')} NTU
- Temperature: {alert.get('temperature', 'N/A')}°C

---
AquaSentinel-Pi5 Monitoring System
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info("Email alert sent")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


class SMSAlert:
    """SMS notification via Twilio"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False) and HAS_TWILIO
        
        if self.enabled:
            self.client = TwilioClient(
                config.get('account_sid'),
                config.get('auth_token')
            )
            self.from_number = config.get('from_number')
            self.to_numbers = config.get('to_numbers', [])
            logger.info("SMS alerts enabled")
    
    def send(self, alert: Dict) -> bool:
        if not self.enabled:
            return False
        
        try:
            message = f"🌊 AquaSentinel Alert\n{alert['severity'].upper()}: {alert['message']}"
            
            for number in self.to_numbers:
                self.client.messages.create(
                    body=message[:160],
                    from_=self.from_number,
                    to=number
                )
            
            logger.info("SMS alert sent")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False


class LocalAlert:
    """Local buzzer and LED alerts"""
    
    def __init__(self, config: Dict, indicators=None):
        self.config = config
        self.buzzer_enabled = config.get('buzzer_enabled', True)
        self.led_enabled = config.get('led_enabled', True)
        self.indicators = indicators
    
    def send(self, alert: Dict) -> bool:
        if not self.indicators:
            return False
        
        try:
            severity = alert['severity']
            
            if self.led_enabled:
                colors = {
                    'critical': 'red',
                    'warning': 'yellow',
                    'info': 'blue'
                }
                self.indicators.set_led(colors.get(severity, 'white'))
            
            if self.buzzer_enabled:
                patterns = {
                    'critical': (0.5, 3),
                    'warning': (0.2, 2),
                    'info': (0.1, 1)
                }
                duration, count = patterns.get(severity, (0.1, 1))
                self.indicators.beep(duration=duration, count=count)
            
            return True
        except Exception as e:
            logger.error(f"Failed local alert: {e}")
            return False


class AlertManager:
    """Manages all alert channels"""
    
    def __init__(self, config: Dict, indicators=None):
        self.email_alert = EmailAlert(config.get('email', {}))
        self.sms_alert = SMSAlert(config.get('sms', {}))
        self.local_alert = LocalAlert(config.get('local', {}), indicators)
        logger.info("Alert manager initialized")
    
    def send_alert(self, alert: Dict):
        logger.info(f"Sending alert: {alert['type']} ({alert['severity']})")
        
        severity = alert['severity']
        
        if severity == 'critical':
            self.email_alert.send(alert)
            self.sms_alert.send(alert)
            self.local_alert.send(alert)
        elif severity == 'warning':
            self.email_alert.send(alert)
            self.local_alert.send(alert)
        else:
            self.local_alert.send(alert)
