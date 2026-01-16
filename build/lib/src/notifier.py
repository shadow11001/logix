import smtplib
import requests
from email.mime.text import MIMEText
from src.config import Config

class Notifier:
    def __init__(self):
        self.config = Config

    def send_discord(self, finding):
        if not self.config.DISCORD_WEBHOOK_URL:
            return False

        message = {
            "embeds": [
                {
                    "title": f"Logix Alert: {finding.get('severity', 'Unknown').upper()}",
                    "description": finding.get('findings', 'No details provided.'),
                    "color": 15158332 if finding.get('severity') == 'critical' else 15105570,
                    "fields": [
                        {
                            "name": "Log Entry",
                            "value": f"```\n{finding.get('log_entry', '')[:1000]}\n```"
                        },
                        {
                            "name": "Suggested Fix",
                            "value": finding.get('suggested_fix', 'None')
                        }
                    ],
                    "footer": {
                        "text": "Logix Automated Agent"
                    }
                }
            ]
        }

        try:
            response = requests.post(self.config.DISCORD_WEBHOOK_URL, json=message)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Discord webhook: {e}")
            return False

    def send_email(self, finding):
        if not all([self.config.SMTP_SERVER, self.config.SMTP_USER, self.config.SMTP_PASSWORD, self.config.SMTP_TO]):
            return False

        subject = f"[Logix] {finding.get('severity', 'Alert').title()}: Issue Detected"
        body = f"""
        Logix has detected an issue.
        
        Severity: {finding.get('severity')}
        Findings: {finding.get('findings')}
        
        Log Entry:
        {finding.get('log_entry')}
        
        Suggested Fix:
        {finding.get('suggested_fix')}
        """

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.config.SMTP_FROM or self.config.SMTP_USER
        msg['To'] = self.config.SMTP_TO

        try:
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def notify_all(self, finding):
        """Attempts to send notifications via all configured channels."""
        results = {}
        if self.config.DISCORD_WEBHOOK_URL:
            results['discord'] = self.send_discord(finding)
        
        if self.config.SMTP_SERVER:
            results['email'] = self.send_email(finding)
            
        return results
