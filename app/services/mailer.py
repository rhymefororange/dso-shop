"""Надсилання листів (SMTP). Без SMTP_HOST листи не надсилаються."""
import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

log = logging.getLogger(__name__)


def send_mail(to_addr, subject, body):
    host = current_app.config["SMTP_HOST"]
    if not host:
        log.info("SMTP_HOST is not set; mail with subject %r was not sent", subject)
        return False
    msg = EmailMessage()
    msg["From"] = current_app.config["MAIL_FROM"]
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(host, current_app.config["SMTP_PORT"], timeout=10) as smtp:
        smtp.starttls()
        smtp.send_message(msg)
    return True
