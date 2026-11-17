# Users/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Wallet, Ride, EmergencyAlert, Notification


@receiver(post_save, sender=CustomUser)
def create_user_wallet(sender, instance, created, **kwargs):
    """Automatically create wallet when user registers"""
    if created:
        Wallet.objects.get_or_create(user=instance)
        print(f"💰 Wallet created for user: {instance.username}")


@receiver(post_save, sender=Ride)
def update_user_stats_on_ride_completion(sender, instance, **kwargs):
    """Update user statistics when ride is completed"""
    if instance.status == 'completed':
        user = instance.user
        user.total_rides_count += 1
        user.total_distance_covered += float(instance.distance or 0)
        user.carbon_saved_total += float(instance.carbon_saved or 0)
        
        # Update loyalty points (1 point per km)
        user.loyalty_points += int(instance.distance or 0)
        
        # Update membership tier based on rides
        if user.total_rides_count >= 50:
            user.membership_tier = 'platinum'
        elif user.total_rides_count >= 20:
            user.membership_tier = 'gold' 
        elif user.total_rides_count >= 10:
            user.membership_tier = 'silver'
        
        user.save()
        print(f"📊 Updated stats for {user.username}: {user.total_rides_count} rides")


@receiver(post_save, sender=EmergencyAlert)
def notify_admin_emergency(sender, instance, created, **kwargs):
    """Notify admins when emergency alert is created"""
    if created:
        # Create notification for emergency
        Notification.objects.create(
            user=instance.user,
            notification_type='safety',
            title='Emergency Alert Activated',
            message=f'Your {instance.get_alert_type_display()} alert has been activated',
            data={'alert_id': instance.id, 'location': instance.location_name}
        )
        print(f"🚨 Emergency alert notification sent for {instance.user.username}")