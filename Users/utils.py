import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser

def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(user, otp):
    """Send verification email with OTP"""
    subject = 'Verify Your Email - SmartRide'
    message = f'''
    Hi {user.first_name or 'there'},

    Your email verification OTP is: {otp}

    This OTP will expire in 10 minutes.

    If you didn't create an account, please ignore this email.

    Happy Riding! 🛴
    SmartRide Team
    '''
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def calculate_ride_cost(duration_minutes, distance_km, price_per_minute, price_per_km=None):
    """Calculate ride cost"""
    cost = duration_minutes * float(price_per_minute)
    if price_per_km:
        cost += distance_km * float(price_per_km)
    return cost

def calculate_carbon_savings(distance_km):
    """Calculate carbon savings compared to car"""
    # Average car emits ~0.2kg CO2 per km
    return distance_km * 0.2