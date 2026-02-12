import smtplib
from email.mime.text import MIMEText

def send_notification_email(subject, body, email_config, log_callback=None):
    """
    Sends an email notification using the provided configuration.
    email_config must contain: SENDER_EMAIL, SENDER_PASSWORD, RECIPIENT_EMAILS
    """
    sender = email_config.get("SENDER_EMAIL")
    password = email_config.get("SENDER_PASSWORD")
    recipients = email_config.get("RECIPIENT_EMAILS")
    
    if not sender or not password or not recipients:
        if log_callback:
            log_callback("Email configuration missing. Skipping email.", "red")
        return

    # Join multiple recipients into a comma-separated string
    to_list = ", ".join(recipients)

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_list

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        if log_callback:
            log_callback(f"Email notification sent to {len(recipients)} recipient(s)!", "yellow")
    except Exception as e:
        if log_callback:
            log_callback(f"Failed to send email: {e}", "red")
            log_callback("HINT: Ensure 'Less secure app access' or 'App Password' is enabled.", "red")