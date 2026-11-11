"""Email dispatcher with Console and SMTP adapters for alert notifications."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Any, Protocol

from app.core.config import settings

logger = logging.getLogger("pyroscope.alerts")


class Mailer(Protocol):
    """Protocol for sending alert and confirmation emails."""

    def send_confirmation(self, to_email: str, area_id: str, token: str) -> bool:
        """Send a subscription confirmation email."""
        ...

    def send_alert(
        self,
        to_email: str,
        area_id: str,
        subject: str,
        body: str,
        unsubscribe_token: str,
    ) -> bool:
        """Send an advisory fire alert email."""
        ...


class ConsoleMailer:
    """Console/in-memory mailer used in test suites, CI, and local judge evaluation."""

    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []

    def clear(self) -> None:
        """Clear sent message log."""
        self.sent_messages.clear()

    def send_confirmation(self, to_email: str, area_id: str, token: str) -> bool:
        confirm_url = f"{settings.web_origin}/alerts/confirm?token={token}"
        msg = {
            "type": "confirmation",
            "to": to_email,
            "area_id": area_id,
            "token": token,
            "confirm_url": confirm_url,
            "subject": f"[PyroScope] Confirm your fire advisory subscription for {area_id}",
            "body": (
                f"Please confirm your fire advisory subscription for area {area_id}.\n"
                f"Confirmation link: {confirm_url}\n"
            ),
        }
        self.sent_messages.append(msg)
        logger.info("[ConsoleMailer] Confirmation sent to %s (area: %s)", to_email, area_id)
        return True

    def send_alert(
        self,
        to_email: str,
        area_id: str,
        subject: str,
        body: str,
        unsubscribe_token: str,
    ) -> bool:
        unsub_url = f"{settings.web_origin}/api/alerts/subscriptions?token={unsubscribe_token}"
        full_body = (
            f"{body}\n\n"
            "--------------------------------------------------\n"
            "ADVISORY NOTICE:\n"
            "This notification is based on satellite active fire detection from NASA FIRMS. "
            "Data is provisional and intended for environmental and agricultural awareness, "
            "not tactical emergency dispatch.\n"
            f"To unsubscribe: {unsub_url}\n"
        )
        msg = {
            "type": "alert",
            "to": to_email,
            "area_id": area_id,
            "subject": subject,
            "body": full_body,
            "unsubscribe_token": unsubscribe_token,
            "unsub_url": unsub_url,
        }
        self.sent_messages.append(msg)
        logger.info("[ConsoleMailer] Advisory alert sent to %s (area: %s)", to_email, area_id)
        return True


class SMTPMailer:
    """Production SMTP mailer."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 587,
        username: str = "",
        password: str = "",
        from_email: str = "alerts@pyroscope.org",
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email

    def _deliver(self, to_email: str, subject: str, body: str) -> bool:
        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10.0) as server:
                if self.username and self.password:
                    server.starttls()
                    server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send SMTP email to %s: %s", to_email, exc)
            return False

    def send_confirmation(self, to_email: str, area_id: str, token: str) -> bool:
        confirm_url = f"{settings.web_origin}/alerts/confirm?token={token}"
        subject = f"[PyroScope] Confirm your fire advisory subscription for {area_id}"
        body = (
            f"Please confirm your fire advisory subscription for area {area_id}.\n\n"
            f"Confirmation link: {confirm_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
        return self._deliver(to_email, subject, body)

    def send_alert(
        self,
        to_email: str,
        area_id: str,
        subject: str,
        body: str,
        unsubscribe_token: str,
    ) -> bool:
        unsub_url = f"{settings.web_origin}/api/alerts/subscriptions?token={unsubscribe_token}"
        full_body = (
            f"{body}\n\n"
            "--------------------------------------------------\n"
            "ADVISORY NOTICE:\n"
            "This notification is based on satellite active fire detection from NASA FIRMS. "
            "Data is provisional and intended for environmental and agricultural awareness, "
            "not tactical emergency dispatch.\n\n"
            f"To unsubscribe: {unsub_url}\n"
        )
        return self._deliver(to_email, subject, full_body)


_default_mailer: ConsoleMailer | SMTPMailer = ConsoleMailer()


def get_mailer() -> Mailer:
    """Return the configured mailer instance."""
    return _default_mailer


def set_mailer(mailer: ConsoleMailer | SMTPMailer) -> None:
    """Override the global mailer (useful in tests)."""
    global _default_mailer
    _default_mailer = mailer
