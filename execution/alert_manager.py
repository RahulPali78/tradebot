"""Alert management for tradebot."""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger('tradebot')


class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 465
    ):
        """Initialize alert manager."""
        self.email = email
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def send_alert(
        self,
        subject: str,
        body: str,
        to_email: Optional[str] = None
    ) -> bool:
        """Send email alert."""
        if not self.email or not self.password:
            logger.warning("Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email or self.email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Alert sent: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def send_trade_alert(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        to_email: Optional[str] = None
    ) -> bool:
        """Send trade alert."""
        subject = f"Trade Alert: {signal} {symbol}"
        body = f"""
Trade Alert Generated

Symbol: {symbol}
Signal: {signal}
Confidence: {confidence}%
Time: {datetime.now().isoformat()}

This is an automated alert from your tradebot.
        """
        return self.send_alert(subject, body, to_email)
