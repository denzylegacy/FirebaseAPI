import os
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List
import aiofiles

from app.settings import (
    log, GMAIL_SENDER_EMAIL, 
    GMAIL_SENDER_SECRET
)


class AsyncGmailClient:
    def __init__(
        self, 
        sender_email: str, 
        sender_secret: str, 
        smtp_server: str = 'smtp.gmail.com', 
        port: int = 465
    ):
        """
        Initialize the AsyncGmailClient with the sender's credentials and SMTP server settings.
        
        Parameters:
            sender_email (str): The sender's email address.
            sender_secret (str): The passphrase for the sender's email account.
            smtp_server (str): The SMTP server address (default: smtp.gmail.com).
            port (int): The port to use (default: 465 for SSL connection).
        """
        self.sender_email = sender_email
        self.sender_secret = sender_secret
        self.smtp_server = smtp_server
        self.port = port
        
        if not self.sender_email or self.sender_email is None:
            raise ValueError("Sender email cannot be empty or None")
        if not self.sender_secret or self.sender_secret is None:
            raise ValueError("Sender secret/password cannot be empty or None")

    async def _connect(self):
        """
        Private async method to create a secure connection with the SMTP server.
        
        Returns:
            An instance of the SMTP_SSL connection.
        """
        try:
            log.debug(
                f"Connecting to SMTP server {self.smtp_server}:{self.port} " + 
                f"with account {self.sender_email}"
            )
            
            server = aiosmtplib.SMTP(hostname=self.smtp_server, port=self.port, use_tls=True)
            await server.connect()
            await server.login(self.sender_email, self.sender_secret)
            return server
        except Exception as e:
            log.error(f"Error connecting to SMTP server: {e}")
            
            if self.sender_secret is None:
                log.error("Authentication failed - sender_secret is None. Check your environment variables or settings.")
            raise

    async def send_text_email(self, subject: str, body: str, recipients: List[str]):
        """
        Send a plain text email asynchronously.
        
        Parameters:
            subject (str): The subject of the email.
            body (str): The body of the email.
            recipients (list): A list of recipient email addresses.
        """
        msg = MIMEText(body, 'plain')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients)
        
        try:
            server = await self._connect()
            await server.send_message(msg)
            await server.quit()
            log.info("Plain text email sent successfully!")
        except Exception as e:
            log.error(f"Error sending plain text email: {e}")
            raise

    async def send_html_email(self, subject: str, html_body: str, recipients: List[str]):
        """
        Send an HTML email asynchronously.
        
        Parameters:
            subject (str): The subject of the email.
            html_body (str): The HTML content of the email.
            recipients (list): A list of recipient email addresses.
        """
        msg = MIMEText(html_body, 'html')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients)
        
        try:
            server = await self._connect()
            await server.send_message(msg)
            await server.quit()
            log.info("HTML email sent successfully!")
        except Exception as e:
            log.error(f"Error sending HTML email: {e}")
            raise

    async def send_email_with_attachment(
        self, 
        subject: str, 
        body: str, 
        recipients: List[str], 
        attachment_path: str
    ):
        """
        Send an email with an attachment asynchronously. 
        The body may contain either plain text or HTML.
        
        Parameters:
            subject (str): The subject of the email.
            body (str): The body of the email (plain text or HTML).
            recipients (list): A list of recipient email addresses.
            attachment_path (str): The path to the file to be attached.
        """
        message = MIMEMultipart()
        message['Subject'] = subject
        message['From'] = self.sender_email
        message['To'] = ', '.join(recipients)

        if '<html>' in body.lower():
            body_part = MIMEText(body, 'html')
        else:
            body_part = MIMEText(body, 'plain')
        message.attach(body_part)

        if not os.path.exists(attachment_path):
            log.warn(f"Attachment file not found: {attachment_path}")
            return

        try:
            async with aiofiles.open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(await attachment.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header("Content-Disposition", f"attachment; filename=\"{filename}\"")
            message.attach(part)
        except Exception as e:
            log.error(f"Error preparing the attachment: {e}")
            return

        try:
            server = await self._connect()
            await server.send_message(message)
            await server.quit()
            log.info("Email with attachment sent successfully!")
        except Exception as e:
            log.error(f"Error sending email with attachment: {e}")
            raise


# global async Gmail client instance
async_gmail_client = AsyncGmailClient(
    sender_email=GMAIL_SENDER_EMAIL, sender_secret=GMAIL_SENDER_SECRET
)


# Example usage with async/await
async def main():
    # Send a plain text email
    # subject_text = "Plain Text Email"
    # body_text = "This is the body of a plain text email."
    # await async_gmail_client.send_text_email(subject_text, body_text, "example@gmail.com")

    # Send an HTML email
    subject_html = "HTML Email"
    html_body = """
    <html>
      <body>
        <p>This is an <b>HTML</b> email sent from Python using Gmail SMTP.</p>
      </body>
    </html>
    """
    await async_gmail_client.send_html_email(subject_html, html_body, "example@gmail.com")

    # # Send an email with an attachment
    # subject_attachment = "Email with Attachment"
    # body_attachment = "Please find the attached file."
    # attachment = "attachment.txt"
    # await async_gmail_client.send_email_with_attachment(
    #     subject_attachment, 
    #     body_attachment, 
    #     ["recipient@gmail.com"], 
    #     attachment
    # )


if __name__ == "__main__":
    asyncio.run(main())
    