"""Email sending.

On Render's free tier outbound SMTP (ports 25/465/587) is blocked, so production
uses Brevo's HTTPS API. For local development you can fall back to Gmail SMTP by
setting MAIL_USERNAME and MAIL_PASSWORD (a Gmail App Password) in .env.
"""
import os
import smtplib
from email.message import EmailMessage

import requests

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class MailError(Exception):
    pass


def sendmail(to, subject, body):
    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("MAIL_SENDER") or os.getenv("MAIL_USERNAME")
    sender_name = os.getenv("MAIL_SENDER_NAME", "ShopSphere")

    if api_key:
        if not sender_email:
            raise MailError("MAIL_SENDER is not set")
        try:
            response = requests.post(
                BREVO_URL,
                headers={
                    "api-key": api_key,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                json={
                    "sender": {"name": sender_name, "email": sender_email},
                    "to": [{"email": to}],
                    "subject": subject,
                    "textContent": body,
                },
                timeout=15,
            )
        except requests.RequestException as exc:
            raise MailError(f"Could not reach Brevo: {exc}") from exc

        if response.status_code >= 300:
            raise MailError(f"Brevo error {response.status_code}: {response.text[:200]}")
        return

    # Local-development fallback (does NOT work on Render's free tier).
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    if username and password:
        msg = EmailMessage()
        msg["From"] = username
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(username, password)
                server.send_message(msg)
        except (smtplib.SMTPException, OSError) as exc:
            raise MailError(f"SMTP failed: {exc}") from exc
        return

    raise MailError("No email provider configured (set BREVO_API_KEY and MAIL_SENDER)")
