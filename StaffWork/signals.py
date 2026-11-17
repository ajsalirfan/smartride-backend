from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Task, EmergencyAlert, StaffWorkAnalytics

@receiver(post_save, sender=Task)
def update_staff_analytics_on_task(sender, instance, created, **kwargs):
    """Update staff analytics when task status changes"""
    if instance.assigned_to and instance.status == 'completed':
        today = timezone.now().date()
        analytics, created_obj = StaffWorkAnalytics.objects.get_or_create(
            staff_member=instance.assigned_to,
            date=today,
            defaults={
                'tasks_completed': 1,
                'tasks_assigned': 1
            }
        )
        
        if not created_obj:
            analytics.tasks_completed = (analytics.tasks_completed or 0) + 1
            analytics.save()

@receiver(post_save, sender=EmergencyAlert)
def create_emergency_task(sender, instance, created, **kwargs):
    """Automatically create task when emergency is assigned"""
    if instance.assigned_staff and instance.status == 'assigned':
        task_id = f"EMG{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        Task.objects.get_or_create(
            task_id=task_id,
            defaults={
                'task_type': 'emergency',
                'title': f'Emergency: {instance.emergency_type}',
                'description': instance.description,
                'assigned_to': instance.assigned_staff,
                'assigned_by': instance.verified_by,
                'priority': 'urgent',
                'location_name': instance.location_name,
                'latitude': instance.latitude,
                'longitude': instance.longitude,
                'estimated_duration': 45,
                'task_data': {
                    'emergency_type': instance.emergency_type,
                    'severity': instance.severity,
                    'alert_id': instance.alert_id
                }
            }
        )