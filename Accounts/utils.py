# Accounts/utils.py
import random
from django.core.mail import EmailMessage
from django.core.cache import cache
from django.conf import settings

def send_otp_email(email):
    # 1. Generate a random 6-digit number
    otp_code = str(random.randint(100000, 999999))
    
    # 2. Store in Cache (Key: "otp_user@email.com", Value: "123456", Timeout: 300s)
    cache.set(f'otp_{email}', otp_code, timeout=300)
    
    # 3. Send the Email
    subject = "Reset Your Password - Horologie"
    message = f"""
    Hi there,
    
    Your verification code for resetting your password is:
    
    {otp_code}
    
    This code expires in 5 minutes.
    If you did not request this, please ignore this email.
    """
    
    email_msg = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    email_msg.send()