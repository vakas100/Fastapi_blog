from email.message import EmailMessage

import aiosmtplib

from config import settings

# Function to send an email asynchronously
async def send_email(
    to_email: str,
    subject: str,
    plain_text: str,
    html_content: str | None = None,
) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain_text)
    
    if html_content:
        message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.mail_server,
        port=settings.mail_port,
        username=settings.mail_username if settings.mail_username else None,
        password=settings.mail_password.get_secret_value() or None,
        start_tls=settings.mail_use_tls,
    )

# Send Password reset email function
async def send_password_reset_email(to_email: str, username: str, token: str) -> None:
    reset_link = f"{settings.frontend_url}/reset-password?token={token}"

    plain_text = f"""Hi {username},

    You requested a password reset. Please click the link below to reset your password:
    {reset_link}

    This link will expire in {settings.reset_token_expire_minutes} minutes.

    If you did not request a password reset, please ignore this email.
    Best regards,  
    The FastAPI Blog Team
    """

    html_content = f"""<html>
    <body>
        <p>Hi {username},</p>
        <p>You requested a password reset. Please click the link below to reset your password:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <p>This link will expire in {settings.reset_token_expire_minutes} minutes.</p>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Best regards,<br>The FastAPI Blog Team</p>
    </body>
</html>""" 
    
    await send_email(to_email, "Password Reset Request", plain_text, html_content)
