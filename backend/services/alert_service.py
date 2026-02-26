"""
Alert Service - Sends email and Slack notifications

Features:
- Email alerts via SendGrid
- Slack webhooks for notifications
- Filtering by quality score and domain age
- Batch notifications with top opportunities
"""

import logging
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from sqlalchemy.orm import Session

import models

logger = logging.getLogger(__name__)


class AlertService:
    """Manages notifications for top domain opportunities"""

    def __init__(self):
        """Initialize alert service with API credentials"""
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK")
        self.sendgrid_from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@domainfinder.pro")

    def send_daily_alerts(self, db_session: Session, top_domains: List[Dict]) -> Dict:
        """
        Send daily digest to all subscribers

        Args:
            db_session: Database session
            top_domains: List of top opportunity dicts

        Returns:
            {"email_sent": 0, "slack_sent": 0, "errors": []}
        """
        results = {
            "email_sent": 0,
            "slack_sent": 0,
            "errors": [],
        }

        try:
            # Get all enabled alerts
            alerts = db_session.query(models.Alert).filter(
                models.Alert.enabled == True
            ).all()

            logger.info(f"Sending alerts to {len(alerts)} subscribers...")

            # Filter top domains by alert criteria
            for alert in alerts:
                filtered_domains = self._filter_domains(top_domains, alert)

                if not filtered_domains:
                    logger.debug(f"No qualifying domains for {alert.email}")
                    continue

                # Send email
                if alert.email:
                    try:
                        self.send_email_alert(alert.email, filtered_domains)
                        results["email_sent"] += 1
                    except Exception as e:
                        logger.error(f"Email error for {alert.email}: {e}")
                        results["errors"].append(f"Email {alert.email}: {str(e)}")

                # Send Slack
                if alert.slack_webhook:
                    try:
                        self.send_slack_alert(alert.slack_webhook, filtered_domains)
                        results["slack_sent"] += 1
                    except Exception as e:
                        logger.error(f"Slack error: {e}")
                        results["errors"].append(f"Slack: {str(e)}")

            logger.info(f"Alert results: {results}")
            return results

        except Exception as e:
            logger.error(f"Alert service error: {e}")
            results["errors"].append(str(e))
            return results

    @staticmethod
    def _filter_domains(domains: List[Dict], alert: models.Alert) -> List[Dict]:
        """Filter domains by alert criteria"""
        filtered = []

        for domain in domains:
            # Check quality score threshold
            if domain.get("score", {}).get("total_score", 0) < alert.min_quality_score:
                continue

            # Check domain age filters
            age_days = domain.get("analysis", {}).get("domain_age_days", 0)
            if age_days < alert.min_domain_age or age_days > alert.max_domain_age:
                continue

            # Check backlink minimum
            backlinks = domain.get("analysis", {}).get("backlink_count", 0)
            if backlinks < alert.min_backlinks:
                continue

            filtered.append(domain)

        return filtered[:20]  # Limit to 20 per alert

    def send_email_alert(self, email: str, domains: List[Dict]) -> bool:
        """Send email alert with top opportunities"""
        try:
            subject = f"🎯 Domain Finder Pro - Top {len(domains)} Opportunities"
            html_content = self._build_email_html(domains)

            # SendGrid API call
            if self.sendgrid_api_key:
                return self._send_via_sendgrid(email, subject, html_content)

            # Fallback to direct SMTP (requires mail server)
            return False

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email via SendGrid API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}],
                        "subject": subject,
                    }
                ],
                "from": {"email": self.sendgrid_from_email},
                "content": [
                    {
                        "type": "text/html",
                        "value": html_content,
                    }
                ],
            }

            response = httpx.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers,
                timeout=10.0,
            )

            if response.status_code in [200, 202]:
                logger.info(f"Email sent to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.text}")
                return False

        except Exception as e:
            logger.error(f"SendGrid API error: {e}")
            return False

    @staticmethod
    def _build_email_html(domains: List[Dict]) -> str:
        """Build HTML email content"""
        rows = ""
        for i, domain in enumerate(domains, 1):
            score = domain.get("score", {}).get("total_score", 0)
            grade = domain.get("grade", "N/A")
            price_high = domain.get("estimates", {}).get("price_high", 0)
            roi = domain.get("estimates", {}).get("roi_percent", 0)
            backlinks = domain.get("analysis", {}).get("backlink_count", 0)

            rows += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 12px;">{i}</td>
                <td style="padding: 12px;"><strong>{domain['domain']}</strong></td>
                <td style="padding: 12px; background: #f0f0f0; font-weight: bold;">{score:.1f} ({grade})</td>
                <td style="padding: 12px;">${price_high:,}</td>
                <td style="padding: 12px;">{roi:.0f}%</td>
                <td style="padding: 12px;">{backlinks}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2196F3; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #2196F3; color: white; padding: 12px; text-align: left; }}
                .grade-a {{ color: #4CAF50; font-weight: bold; }}
                .grade-b {{ color: #2196F3; font-weight: bold; }}
                .grade-c {{ color: #FF9800; font-weight: bold; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Domain Finder Pro - Daily Opportunities</h1>
                <p>Hello,</p>
                <p>Here are today's top {len(domains)} domain opportunities matching your criteria:</p>

                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Domain</th>
                            <th>Score</th>
                            <th>Est. Value</th>
                            <th>ROI</th>
                            <th>Backlinks</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>

                <div class="footer">
                    <p>💡 Scores are based on domain age, backlinks, authority, brandability, keywords, and traffic.</p>
                    <p>© Domain Finder Pro - Your automated domain investment assistant</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def send_slack_alert(self, webhook_url: str, domains: List[Dict]) -> bool:
        """Send Slack notification with top opportunities"""
        try:
            # Build blocks for top 5 domains
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🎯 Top {len(domains)} Domain Opportunities",
                    },
                }
            ]

            for domain in domains[:5]:
                score = domain.get("score", {}).get("total_score", 0)
                grade = domain.get("grade", "N/A")
                price_high = domain.get("estimates", {}).get("price_high", 0)
                roi = domain.get("estimates", {}).get("roi_percent", 0)

                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{domain['domain']}*\nScore: {score:.1f} (Grade {grade}) | Value: ${price_high:,} | ROI: {roi:.0f}%",
                    },
                })

            payload = {"blocks": blocks}

            response = httpx.post(webhook_url, json=payload, timeout=10.0)

            if response.status_code == 200:
                logger.info("Slack alert sent successfully")
                return True
            else:
                logger.error(f"Slack error: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Slack send error: {e}")
            return False
