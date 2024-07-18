import datetime
import smtplib
from email.message import EmailMessage

from kani import ai_function

from ._base import ToolBase


class Email(ToolBase):
    """A toy tool to send emails via a given SMTP server."""

    def __init__(self, *args, email_from: str, smtp_host: str, smtp_pass: str, **kwargs):
        """
        :param email_from: the email address to send email from
        :param smtp_host: a string like mailserv.zhu.codes:465
        :param smtp_pass: the password for the email account on the SMTP server
        """
        super().__init__(*args, **kwargs)
        self.email_from = email_from
        self.smtp_host = smtp_host
        self.smtp_pass = smtp_pass

    @ai_function()
    def send_email(self, to: str, subject: str, body: str):
        """Send an email to the given address."""
        msg = EmailMessage()
        msg.set_content(body)

        # me == the sender's email address
        # you == the recipient's email address
        msg["Subject"] = subject
        msg["From"] = self.email_from
        msg["To"] = to.strip("<>")
        msg["Date"] = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        # Send the message via our own SMTP server.
        s = smtplib.SMTP_SSL(self.smtp_host)
        s.login(self.email_from, self.smtp_pass)
        s.send_message(msg)
        s.quit()
        return "Email sent!"
