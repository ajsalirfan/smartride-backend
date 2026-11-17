# StaffWork/utils.py
import logging
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class StaffWorkUtils:
    
    @staticmethod
    def get_staff_member(user):
        """
        Get StaffMember instance from User
        Returns None if not found
        """
        try:
            from .models import StaffMember
            return StaffMember.objects.get(user=user)
        except StaffMember.DoesNotExist:
            # Try to create staff member if user is staff
            if hasattr(user, 'user_type') and user.user_type == 'staff':
                try:
                    return StaffMember.objects.create(
                        user=user,
                        staff_id=f"STAFF{user.id:04d}",
                        department="Operations",
                        designation="Staff Member",
                        is_active=True
                    )
                except Exception as e:
                    logger.error(f"Failed to create staff member: {e}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error getting staff member: {e}")
            return None
    
    @staticmethod
    def get_client_ip(request):
        """
        Get client IP address from request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def calculate_efficiency_score(staff_member, date):
        """Calculate staff efficiency score for the day"""
        try:
            from .models import StaffWorkAnalytics
            
            analytics = StaffWorkAnalytics.objects.filter(
                staff_member=staff_member,
                date=date
            ).first()
            
            if not analytics:
                return 0.0
                
            # Safe numeric values
            tasks_assigned = analytics.tasks_assigned or 0
            tasks_completed = analytics.tasks_completed or 0
            avg_completion_time = analytics.avg_completion_time or 0.0  # minutes
            
            completion_rate = (tasks_completed / tasks_assigned * 100.0) if tasks_assigned > 0 else 0.0
            # time_efficiency: lower avg completion time -> higher efficiency (clamped 0-100)
            # Example: avg_completion_time = 30 -> time_efficiency = max(0, 100 - 30) = 70
            time_efficiency = max(0.0, 100.0 - float(avg_completion_time))
            
            efficiency_score = (completion_rate * 0.6) + (time_efficiency * 0.4)
            return round(min(100.0, efficiency_score), 2)
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {e}")
            return 0.0
    
    @staticmethod
    def get_staff_current_location(staff_member):
        """Get staff's current location based on active tasks"""
        try:
            from .models import Task
            
            active_task = Task.objects.filter(
                assigned_to=staff_member,
                status__in=['assigned', 'in_progress']
            ).first()
            
            if active_task and active_task.latitude is not None and active_task.longitude is not None:
                return {
                    'latitude': float(active_task.latitude),
                    'longitude': float(active_task.longitude),
                    'task_id': getattr(active_task, 'task_id', None),
                    'location_name': getattr(active_task, 'location_name', None)
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting staff location: {e}")
            return None
    
    @staticmethod
    def generate_rebalancing_plan(zone_name, vehicles_needed):
        """Generate optimized rebalancing plan"""
        try:
            from .models import DemandHeatmap
            
            source_zones = DemandHeatmap.objects.filter(
                vehicle_count__gt=vehicles_needed,
                demand_score__lt=0.3  # Low demand areas with excess vehicles
            ).order_by('demand_score')[:3]
            
            plan = {
                'target_zone': zone_name,
                'vehicles_needed': vehicles_needed,
                'recommended_sources': []
            }
            
            for zone in source_zones:
                available = zone.vehicle_count or 0
                plan['recommended_sources'].append({
                    'zone_name': zone.zone_name,
                    'available_vehicles': available,
                    'distance_km': 5.0,  # This would be calculated with actual distance API
                    'priority': 'high' if available > vehicles_needed * 2 else 'medium'
                })
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating rebalancing plan: {e}")
            return None
    
    @staticmethod
    def create_staff_notification(staff_member, title, message, notification_type='system', 
                                related_task=None, related_emergency=None, related_vehicle=None, 
                                is_urgent=False):
        """Create a notification for staff member"""
        try:
            from .models import Notification
            
            notification = Notification.objects.create(
                staff_member=staff_member,
                notification_type=notification_type,
                title=title,
                message=message,
                related_task=related_task,
                related_emergency=related_emergency,
                related_vehicle=related_vehicle,
                is_urgent=is_urgent,
                is_read=False
            )
            return notification
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    @staticmethod
    def notify_all_staff(title, message, notification_type='announcement'):
        """Send notification to all active staff members"""
        try:
            from .models import StaffMember, Notification
            
            staff_members = StaffMember.objects.filter(is_active=True)
            notifications = []
            
            for staff in staff_members:
                notification = Notification.objects.create(
                    staff_member=staff,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    is_read=False
                )
                notifications.append(notification)
            
            return notifications
        except Exception as e:
            logger.error(f"Failed to notify all staff: {e}")
            return []
    
    @staticmethod
    def format_time_ago(dt):
        """Format datetime as time ago string"""
        if not dt:
            return ""
        
        now = timezone.now()
        diff = now - dt
        
        if diff < timedelta(minutes=1):
            return "just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=30):
            days = int(diff.total_seconds() / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif diff < timedelta(days=365):
            months = int(diff.days / 30)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(diff.days / 365)
            return f"{years} year{'s' if years != 1 else ''} ago"
    
    @staticmethod
    def get_staff_performance_stats(staff_member, days=30):
        """Get staff performance statistics for last N days"""
        try:
            from .models import StaffWorkAnalytics
            from django.db.models import Avg, Sum, Count
            
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            stats = StaffWorkAnalytics.objects.filter(
                staff_member=staff_member,
                date__range=[start_date, end_date]
            ).aggregate(
                total_tasks_assigned=Sum('tasks_assigned'),
                total_tasks_completed=Sum('tasks_completed'),
                avg_completion_time=Avg('avg_completion_time'),
                avg_efficiency=Avg('efficiency_score'),
                total_working_days=Count('id')
            )
            
            # Calculate completion rate
            total_assigned = stats['total_tasks_assigned'] or 0
            total_completed = stats['total_tasks_completed'] or 0
            completion_rate = (total_completed / total_assigned * 100) if total_assigned > 0 else 0
            
            return {
                'period': f'Last {days} days',
                'total_tasks_assigned': total_assigned,
                'total_tasks_completed': total_completed,
                'completion_rate': round(completion_rate, 2),
                'avg_completion_time': round(stats['avg_completion_time'] or 0, 2),
                'avg_efficiency_score': round(stats['avg_efficiency'] or 0, 2),
                'total_working_days': stats['total_working_days']
            }
        except Exception as e:
            logger.error(f"Error getting staff performance stats: {e}")
            return None

# Create aliases for backward compatibility
get_staff_member = StaffWorkUtils.get_staff_member
get_client_ip = StaffWorkUtils.get_client_ip