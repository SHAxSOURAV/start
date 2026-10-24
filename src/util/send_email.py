from datetime import datetime
from email.message import EmailMessage

import aiosmtplib

from src.config import config

current_date = datetime.now()
formatted_date = current_date.strftime("%m/%d/%Y")


async def send_email(options: dict) -> None:
    message = EmailMessage()
    message["From"] = f"{config.smtp.NAME} <{config.smtp.smtp_mail}>"
    message["To"] = options["email"]
    message["Subject"] = options["subject"]
    message["Date"] = formatted_date
    message.set_content(options["html"], subtype="html")

    await aiosmtplib.send(
        message,
        hostname=config.smtp.smtp_host,
        port=config.smtp.smtp_port or 587,
        username=config.smtp.smtp_mail,
        password=config.smtp.smtp_password,
        start_tls=True,  # secure: false + STARTTLS, as in the nodemailer config
    )
