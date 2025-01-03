from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
import json

class AlertHandler:
    def __init__(
        self,
        config: Config,
        logger: Optional[ContextLogger] = None
    ):
        self.config = config
        self.logger = logger or ContextLogger(__name__)
        self.alert_thresholds = {
            'error_rate': 0.1,  # Alert if >10% errors
            'processing_time': 60,  # Alert if batch takes >60s
            'api_errors': 5  # Alert after 5 API errors
        }

    def check_metrics(self, metrics: Dict[str, Any]) -> None:
        """Check metrics against thresholds and trigger alerts"""
        alerts = []
        
        # Check error rate
        if metrics['error_rate'] > self.alert_thresholds['error_rate']:
            alerts.append(
                f"High error rate: {metrics['error_rate']:.1%}"
            )
            
        # Check processing time
        if metrics['avg_processing_time'] > self.alert_thresholds['processing_time']:
            alerts.append(
                f"Slow processing: {metrics['avg_processing_time']:.1f}s"
            )
            
        # Check API errors
        if metrics['api_errors'] >= self.alert_thresholds['api_errors']:
            alerts.append(
                f"Multiple API errors: {metrics['api_errors']}"
            )
            
        if alerts:
            self._send_alert(alerts)

    # def _send_alert(self, alerts: List[str]) -> None:
    #     """Send alert via configured channels"""
    #     if self.config.alert_email:
    #         self._send_email_alert(alerts)
            
    #     if self.config.slack_webhook:
    #         self._send_slack_alert(alerts)
            
    #     self.logger.error(
    #         "Processing alerts triggered",
    #         alerts=alerts
    #     )

    # def _send_email_alert(self, alerts: List[str]) -> None:
    #     try:
    #         msg = MIMEText("\n".join(alerts))
    #         msg['Subject'] = "DevRev Processing Alert"
    #         msg['From'] = self.config.alert_email_from
    #         msg['To'] = self.config.alert_email_to
            
    #         with smtplib.SMTP(self.config.smtp_host) as smtp:
    #             smtp.send_message(msg)
                
    #     except Exception as e:
    #         self.logger.error(
    #             f"Failed to send email alert: {str(e)}"
    #         )