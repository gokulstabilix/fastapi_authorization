import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional

from authorization_service.core.config import settings


def send_email(
    to_email: str,
    subject: str,
    body: str,
    *,
    from_name: Optional[str] = None,
    from_email: Optional[str] = None,
) -> None:
    """
    Send an email using SMTP settings from configuration.
    Uses SSL on port 465 by default if SMTP_USE_SSL is True.
    """
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    use_ssl = settings.SMTP_USE_SSL
    use_tls = settings.SMTP_USE_TLS

    if not host or not port or not username or not password:
        raise RuntimeError("SMTP is not configured. Please set SMTP_* settings in .env")

    sender_email = from_email or settings.MAIL_FROM or username
    sender_name = from_name or settings.PROJECT_NAME or "No-Reply"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((sender_name, sender_email))
    msg["To"] = to_email

    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(username, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            server.login(username, password)
            server.sendmail(sender_email, [to_email], msg.as_string())


def send_verification_otp_email(to_email: str, otp: str) -> None:
    subject = "🔒 Verify Your Email Address"

    body = f"""
    Hello,

     Please use the One-Time Password (OTP) below to complete your verification process:

    👉 **Your Verification Code:** {otp}

    This code will expire in {settings.EMAIL_OTP_EXPIRE_MINUTES} minutes for your security.

    If you did not initiate this request, please ignore this email — no further action is required.

    Thank you,  
     {settings.PROJECT_NAME} Team  
    """

    send_email(to_email=to_email, subject=subject, body=body)

