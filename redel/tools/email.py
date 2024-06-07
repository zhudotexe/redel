import datetime
import smtplib
from email.message import EmailMessage

from kani import ai_function

from redel.config import EMAIL_FROM, EMAIL_HOST, EMAIL_PASS


class EmailMixin:
    @ai_function()
    def send_email(self, to: str, subject: str, body: str):
        """Send an email to the given address."""
        msg = EmailMessage()
        msg.set_content(body)

        # me == the sender's email address
        # you == the recipient's email address
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM
        msg["To"] = to.strip("<>")
        msg["Date"] = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        # Send the message via our own SMTP server.
        s = smtplib.SMTP_SSL(EMAIL_HOST)
        s.login(EMAIL_FROM, EMAIL_PASS)
        s.send_message(msg)
        s.quit()
        return "Email sent!"
