import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """
    Synchronous helper to send an HTML email via SMTP.
    Returns True if sent successfully, False otherwise.
    """
    if not getattr(settings, "EMAILS_ENABLED", True):
        print("[Email Service] Email dispatch is disabled in settings.")
        return False

    smtp_user = getattr(settings, "SMTP_USER", "")
    smtp_password = getattr(settings, "SMTP_PASSWORD", "")
    smtp_host = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(getattr(settings, "SMTP_PORT", 587))
    from_email = getattr(settings, "SMTP_FROM_EMAIL", "") or smtp_user

    if not smtp_user or not smtp_password:
        print("[Email Service] SMTP credentials not configured.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        html_part = MIMEText(body_html, "html")
        msg.attach(html_part)

        # Connect to SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        print(f"[Email Service] Successfully sent email to {to_email}: '{subject}'")
        return True
    except Exception as e:
        print(f"[Email Service Error] Failed to send email to {to_email}: {e}")
        return False

def send_email_async(to_email: str, subject: str, body_html: str):
    """
    Dispatches email in a daemon thread so it never blocks or crashes the main request thread.
    """
    thread = threading.Thread(target=send_email, args=(to_email, subject, body_html), daemon=True)
    thread.start()
