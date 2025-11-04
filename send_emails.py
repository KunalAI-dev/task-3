import smtplib
import ssl
import time
import csv
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path

# -------------------------------
# Setup Logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("email_log.txt"),
        logging.StreamHandler()
    ]
)

# -------------------------------
# Email Sending Function
# -------------------------------
def send_email(
    sender_email: str,
    password: str,
    recipient_email: str,
    subject: str,
    body: str,
    attachment_path: Path = None,
    retries: int = 3
):
    """Send an email with optional attachment and retry logic."""
    for attempt in range(1, retries + 1):
        try:
            # Create email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            # Add body text
            msg.attach(MIMEText(body, "plain"))

            # Add attachment if provided
            if attachment_path and attachment_path.exists():
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=attachment_path.name)
                part["Content-Disposition"] = f'attachment; filename="{attachment_path.name}"'
                msg.attach(part)

            # Secure connection with Gmail SMTP
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender_email, password)
                server.send_message(msg)

            logging.info(f"✅ Email sent to {recipient_email}")
            return True

        except Exception as e:
            logging.warning(f"Attempt {attempt} failed for {recipient_email}: {e}")
            time.sleep(2 * attempt)  # exponential backoff

    logging.error(f"❌ Failed to send email to {recipient_email} after {retries} attempts")
    return False


# -------------------------------
# Main Function
# -------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Automate sending emails with attachments using Gmail SMTP."
    )
    parser.add_argument("--sender", required=True, help="Sender Gmail address")
    parser.add_argument("--app-password", required=True, help="Gmail App Password (not your Gmail password)")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Path to text file containing email body")
    parser.add_argument("--recipients", required=True, help="CSV file with recipient details")
    parser.add_argument("--attachment", help="Path to attachment file (optional)")

    args = parser.parse_args()

    sender_email = args.sender
    password = args.app_password
    attachment_path = Path(args.attachment) if args.attachment else None

    # Load email body
    with open(args.body, "r", encoding="utf-8") as f:
        body_template = f.read()

    # Read recipients CSV
    with open(args.recipients, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            recipient_email = row.get("email")
            name = row.get("name", "there")

            # Personalize message
            body = body_template.replace("{name}", name)

            success = send_email(
                sender_email,
                password,
                recipient_email,
                args.subject,
                body,
                attachment_path
            )

            if not success:
                logging.error(f"Failed to send to {recipient_email}")


if __name__ == "__main__":
    main()
