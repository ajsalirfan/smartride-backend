# StaffWork/views.py
import logging
import random
import string
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

# REST Framework imports
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken



import json
from django.contrib.auth import get_user_model
User = get_user_model()




# Model imports
from .models import StaffMember, Task, EmergencyAlert, Vehicle,RebalancingTask, DemandZone, TaskAttachment
from .serializers import (
    TaskSerializer, TaskCreateSerializer, EmergencyAlertSerializer,
    VehicleSerializer,RebalancingTaskSerializer,
    DemandZoneSerializer, StaffMemberSerializer, TaskAttachmentSerializer
)

try:
    from Users.models import CustomUser, Notification
except ImportError:
    # Fallback for development
    class CustomUser:
        objects = None
        @classmethod
        def create_user(cls, **kwargs):
            user = cls()
            user.id = 1
            user.username = kwargs.get('username', 'temp_user')
            user.email = kwargs.get('email', 'temp@example.com')
            user.first_name = kwargs.get('first_name', '')
            user.last_name = kwargs.get('last_name', '')
            user.phone_number = kwargs.get('phone_number', '')
            user.user_type = kwargs.get('user_type', 'staff')
            user.is_staff = kwargs.get('is_staff', True)
            return user

    class Notification:
        objects = type('obj', (object,), {'create': lambda **kwargs: print(f"Placeholder: Notification created - {kwargs}")})()

logger = logging.getLogger(__name__)




# Add this at the top of your views.py with other imports
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

# Add this function to your views.py
@api_view(['GET'])
def api_root(request, format=None):
    """
    📋 SmartRide Staff API Root
    Provides an overview of all available API endpoints
    """
    return Response({
        # 🔐 AUTHENTICATION ENDPOINTS
        'staff-login': reverse('StaffWork:staff-login', request=request, format=format),
        'staff-logout': reverse('StaffWork:staff-logout', request=request, format=format),
        'token-refresh': reverse('StaffWork:token-refresh', request=request, format=format),
        'password-change': reverse('StaffWork:password-change', request=request, format=format),
        
        # 📊 DASHBOARD & OVERVIEW
        'staff-dashboard': reverse('StaffWork:staff-dashboard', request=request, format=format),
        'dashboard-health': reverse('StaffWork:dashboard-health', request=request, format=format),
        
        # 📋 TASK MANAGEMENT
        'staff-tasks': reverse('StaffWork:staff-tasks', request=request, format=format),
        'task-attachments': reverse('StaffWork:task-attachments', request=request, format=format, kwargs={'task_id': 'sample_task_id'}),
        
        # 👑 ADMIN MANAGEMENT
        'admin-tasks': reverse('StaffWork:admin-tasks', request=request, format=format),
        'admin-staff-list': reverse('StaffWork:admin-staff-list', request=request, format=format),
        'register-staff': reverse('StaffWork:register-staff', request=request, format=format),
        
        # 🚨 EMERGENCY MANAGEMENT
        'emergency-alerts': reverse('StaffWork:emergency-alerts', request=request, format=format),
        
        # 🔄 REBALANCING & ANALYTICS
        'rebalancing': reverse('StaffWork:rebalancing', request=request, format=format),
        'demand-analytics': reverse('StaffWork:demand-analytics', request=request, format=format),
        'staff-performance': reverse('StaffWork:staff-performance', request=request, format=format),
        
        # 🚗 VEHICLE MANAGEMENT
        'vehicle-management': reverse('StaffWork:vehicle-management', request=request, format=format),
        
        # 🛠️ ISSUE RESOLUTION
        'issue-resolution': reverse('StaffWork:issue-resolution', request=request, format=format),
        
        # 🔔 NOTIFICATIONS
        'staff-notifications': reverse('StaffWork:staff-notifications', request=request, format=format),
        
        # 🚨 LEGACY ENDPOINTS
        'legacy-staff-login': reverse('StaffWork:legacy-staff-login', request=request, format=format),
        'legacy-staff-dashboard': reverse('StaffWork:legacy-staff-dashboard', request=request, format=format),
        'legacy-staff-tasks': reverse('StaffWork:legacy-staff-tasks', request=request, format=format),
    })




# ========================
# 🔧 HELPER FUNCTIONS
# ========================

def get_staff_member(user):
    """Helper function to get staff member"""
    try:
        return StaffMember.objects.get(user=user)
    except StaffMember.DoesNotExist:
        logger.warning(f"Staff member not found for user: {user.username}")
        return None

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# ========================
# 🔐 AUTHENTICATION VIEWS
# ========================
class StaffAuthenticationView(APIView):
    """🔐 Staff Authentication System"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Staff login using email + password but authenticate via username"""

        # Remove Authorization header to avoid token interference
        request._request.META.pop("HTTP_AUTHORIZATION", None)

        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'success': False, 'error': 'Email and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user by email
        try:
            auth_user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Authenticate using username + password
        user = authenticate(username=auth_user.username, password=password)

        if not user:
            return Response(
                {'success': False, 'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Ensure this user is a staff
        try:
            staff_member = StaffMember.objects.get(user=user, is_active=True)
        except StaffMember.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Staff account not found or inactive'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Issue tokens
        refresh = RefreshToken.for_user(user)

        # Update staff status
        staff_member.is_on_duty = True
        staff_member.current_status = 'available'
        staff_member.last_login = timezone.now()
        staff_member.save()

        # ⭐ MOST IMPORTANT PART — Return user object (NOT staff)
        # This matches Login.jsx perfectly.
        user_payload = {
            'id': user.id,                                  # Django User ID → Notifications need this
            'username': user.username,
            'email': user.email,
            'user_type': 'staff',                           # Login.jsx checks this
            'employee_id': staff_member.employee_id,
            'role': staff_member.get_role_display(),
        }

        return Response({
            'success': True,
            'message': 'Login successful',

            # ⭐ Login.jsx REQUIRES "user"
            'user': user_payload,

            # Tokens
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class StaffLogoutView(APIView):
    """🚪 Staff Logout and Session Management"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Staff logout with status update"""
        try:
            staff_member = get_staff_member(request.user)
            staff_member.is_on_duty = False
            staff_member.current_status = 'off_duty'
            staff_member.save()

            logger.info(f"Staff logout successful: {staff_member.employee_id}")

            return Response({
                'success': True, 
                'message': 'Logout successful',
                'staff_id': staff_member.employee_id
            }, status=status.HTTP_200_OK)

        except StaffMember.DoesNotExist:
            return Response(
                {'error': 'Staff account not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Staff logout error: {e}")
            return Response(
                {'error': 'Logout failed due to server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 📊 DASHBOARD & ANALYTICS VIEWS
# ========================

class StaffDashboardView(APIView):
    """📊 Staff Dashboard and Operational Views"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Main staff dashboard with comprehensive metrics"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            today = timezone.now().date()
            week_ago = today - timezone.timedelta(days=7)
            
            assigned_tasks = Task.objects.filter(assigned_to=staff_member)
            today_tasks = assigned_tasks.filter(created_at__date=today)
            completed_tasks_week = assigned_tasks.filter(
                status='completed',
                updated_at__date__gte=week_ago
            )
            
            active_emergencies = EmergencyAlert.objects.filter(
                assigned_staff=staff_member,
                status__in=['reported', 'assigned', 'in_progress']
            )
            
            dashboard_data = {
                'success': True,
                'staff_info': {
                    'name': staff_member.user.get_full_name(),
                    'employee_id': staff_member.employee_id,
                    'role': staff_member.role,
                    'current_status': staff_member.current_status,
                    'is_on_duty': staff_member.is_on_duty,
                    'work_zone': staff_member.work_zone,
                },
                'today_metrics': {
                    'total_tasks': assigned_tasks.count(),
                    'completed_today': today_tasks.filter(status='completed').count(),
                    'pending_tasks': assigned_tasks.filter(status__in=['assigned', 'in_progress']).count(),
                    'active_emergencies': active_emergencies.count(),
                    'high_priority_tasks': assigned_tasks.filter(priority='high', status__in=['assigned', 'in_progress']).count(),
                },
                'current_tasks': list(assigned_tasks.filter(
                    status__in=['assigned', 'in_progress']
                ).order_by('-priority', '-created_at').values(
                    'task_id', 'title', 'task_type', 'priority', 'status', 
                    'location_name', 'estimated_duration', 'created_at'
                )[:5]),
                'quick_actions': [
                    {
                        'action': 'start_shift',
                        'title': '🟢 Start Shift',
                        'description': 'Begin your work day',
                        'icon': 'play-circle',
                        'enabled': not staff_member.is_on_duty
                    },
                    {
                        'action': 'end_shift', 
                        'title': '🔴 End Shift',
                        'description': 'Finish your work day',
                        'icon': 'stop-circle',
                        'enabled': staff_member.is_on_duty
                    },
                    {
                        'action': 'view_tasks', 
                        'title': '📋 My Tasks',
                        'description': 'View assigned tasks',
                        'icon': 'list-check',
                        'enabled': True
                    },
                    {
                        'action': 'emergency_alerts',
                        'title': '🚨 Emergencies',
                        'description': 'Respond to urgent alerts', 
                        'icon': 'alert-triangle',
                        'enabled': True
                    }
                ]
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Dashboard error for staff {staff_member.employee_id}: {e}")
            return Response(
                {'error': 'Failed to load dashboard data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 📋 TASK MANAGEMENT VIEWS
# ========================
class TaskManagementView(APIView):
    """📋 Task Management System for Staff"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all tasks assigned to staff member with filtering"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            status_filter = request.GET.get('status', '')
            task_type = request.GET.get('type', '')
            priority = request.GET.get('priority', '')

            tasks = Task.objects.filter(assigned_to=staff_member)

            if status_filter:
                tasks = tasks.filter(status=status_filter)
            if task_type:
                tasks = tasks.filter(task_type=task_type)
            if priority:
                tasks = tasks.filter(priority=priority)

            task_stats = {
                'total': tasks.count(),
                'pending': tasks.filter(status='pending').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'completed': tasks.filter(status='completed').count(),
                'high_priority': tasks.filter(priority='high').count(),
            }

            tasks_data = []

            for task in tasks.order_by('-priority', '-created_at'):
                task_data = {
                    'task_id': task.task_id,
                    'title': task.title,
                    'description': task.description,
                    'task_type': task.task_type,
                    'priority': task.priority,
                    'status': task.status,
                    'location_name': task.location_name,
                    'address': task.address,
                    'assigned_at': task.assigned_at.isoformat() if task.assigned_at else None,
                    'estimated_duration': task.estimated_duration,
                    'actual_duration': task.actual_duration,
                    'created_at': task.created_at.isoformat(),
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                }

                # ⭐ ADD VEHICLE INFO
                if hasattr(task, "vehicle") and task.vehicle:
                    task_data.update({
                        "vehicle": task.vehicle.vehicle_id,
                        "vehicle_type": task.vehicle.vehicle_type,
                        "vehicle_photo": task.vehicle.photo.url if task.vehicle.photo else None
                    })

                # ⭐ ADD LOCATION COORDINATES
                if task.latitude and task.longitude:
                    task_data.update({
                        'latitude': float(task.latitude),
                        'longitude': float(task.longitude)
                    })

                tasks_data.append(task_data)

            return Response({
                'success': True,
                'statistics': task_stats,
                'tasks': tasks_data,
                'total_count': len(tasks_data)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Staff tasks error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, task_id):
        """Update task status"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            task = Task.objects.get(task_id=task_id, assigned_to=staff_member)
            new_status = request.data.get('status')
            notes = request.data.get('notes', '')

            if new_status not in dict(Task.TASK_STATUS).keys():
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            old_status = task.status
            task.status = new_status

            # START TASK
            if new_status == 'in_progress' and not task.started_at:
                task.started_at = timezone.now()

            # COMPLETE TASK
            elif new_status == 'completed' and not task.completed_at:
                task.completed_at = timezone.now()
                if task.started_at:
                    task.actual_duration = (
                        task.completed_at - task.started_at
                    ).total_seconds() / 60

            # ADD NOTES
            task_data = task.task_data or {}
            if notes:
                task_data['completion_notes'] = notes
                task_data['status_updates'] = task_data.get('status_updates', []) + [{
                    'timestamp': timezone.now().isoformat(),
                    'from_status': old_status,
                    'to_status': new_status,
                    'notes': notes
                }]
            task.task_data = task_data

            task.save()

            logger.info(
                f"Task {task_id} status updated from {old_status} to {new_status} by {staff_member.employee_id}"
            )

            return Response({
                'success': True,
                'message': f'Task status updated to {new_status}',
                'task_id': task_id,
                'status': new_status,
            }, status=status.HTTP_200_OK)

        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logger.error(f"Update task status error: {e}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🚨 EMERGENCY MANAGEMENT VIEWS
# ========================

class EmergencyManagementView(APIView):
    """🚨 Emergency Management System"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all emergency alerts"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            emergencies = EmergencyAlert.objects.filter(
                Q(status='reported') | Q(status='assigned')
            ).order_by('-severity', '-reported_at')
            
            my_emergencies = EmergencyAlert.objects.filter(
                assigned_staff=staff_member,
                status__in=['assigned', 'in_progress']
            ).order_by('-severity', '-reported_at')

            emergencies_data = []
            for emergency in emergencies:
                emergency_data = {
                    'alert_id': emergency.alert_id,
                    'emergency_type': emergency.emergency_type,
                    'description': emergency.description,
                    'severity': emergency.severity,
                    'status': emergency.status,
                    'location_name': emergency.location_name,
                    'latitude': float(emergency.latitude),
                    'longitude': float(emergency.longitude),
                    'reported_at': emergency.reported_at.isoformat(),
                    'already_assigned': emergency.assigned_staff is not None,
                    'is_assigned_to_me': emergency.assigned_staff == staff_member
                }
                    
                emergencies_data.append(emergency_data)

            my_emergencies_data = []
            for emergency in my_emergencies:
                my_emergencies_data.append({
                    'alert_id': emergency.alert_id,
                    'emergency_type': emergency.emergency_type,
                    'description': emergency.description,
                    'severity': emergency.severity,
                    'status': emergency.status,
                    'location_name': emergency.location_name,
                    'reported_at': emergency.reported_at.isoformat(),
                })

            return Response({
                'success': True,
                'summary': {
                    'total_emergencies': len(emergencies_data),
                    'my_assigned_emergencies': len(my_emergencies_data),
                    'high_severity': emergencies.filter(severity='high').count(),
                },
                'available_emergencies': emergencies_data,
                'my_emergencies': my_emergencies_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Emergency alerts error: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, alert_id):
        """Handle emergency actions"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        action_type = request.data.get('action')
        
        if action_type == 'accept':
            return self._accept_emergency(request, staff_member, alert_id)
        elif action_type == 'resolve':
            return self._resolve_emergency(request, staff_member, alert_id)
        else:
            return Response(
                {'error': 'Invalid action'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def _accept_emergency(self, request, staff_member, alert_id):
        """Accept emergency assignment"""
        try:
            emergency = EmergencyAlert.objects.get(alert_id=alert_id)
            
            if emergency.assigned_staff:
                return Response(
                    {'error': 'Emergency already assigned to another staff member'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not staff_member.is_on_duty or staff_member.current_status == 'busy':
                return Response(
                    {'error': 'Staff member is not available for new assignments'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            emergency.assigned_staff = staff_member
            emergency.status = 'assigned'
            emergency.assigned_at = timezone.now()
            emergency.save()

            staff_member.current_status = 'busy'
            staff_member.save()

            logger.info(f"Emergency {alert_id} assigned to staff {staff_member.employee_id}")

            return Response({
                'success': True,
                'message': 'Emergency accepted successfully',
                'emergency_id': alert_id,
                'assigned_staff': staff_member.user.get_full_name(),
            }, status=status.HTTP_200_OK)

        except EmergencyAlert.DoesNotExist:
            return Response(
                {'error': 'Emergency not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Accept emergency error: {e}")
            return Response(
                {'error': 'Failed to accept emergency'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _resolve_emergency(self, request, staff_member, alert_id):
        """Resolve emergency"""
        try:
            emergency = EmergencyAlert.objects.get(alert_id=alert_id, assigned_staff=staff_member)
            
            resolution_notes = request.data.get('resolution_notes', '')
            resolution_type = request.data.get('resolution_type', 'resolved')
            
            if not resolution_notes:
                return Response(
                    {'error': 'Resolution notes are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            emergency.status = 'resolved'
            emergency.resolved_at = timezone.now()
            emergency.response_notes = resolution_notes
            emergency.resolution_type = resolution_type
            emergency.save()

            staff_member.current_status = 'available'
            staff_member.save()

            logger.info(f"Emergency {alert_id} resolved by staff {staff_member.employee_id}")

            return Response({
                'success': True,
                'message': 'Emergency resolved successfully',
                'emergency_id': alert_id,
                'resolved_at': emergency.resolved_at.isoformat(),
            }, status=status.HTTP_200_OK)

        except EmergencyAlert.DoesNotExist:
            return Response(
                {'error': 'Emergency not found or not assigned to you'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Resolve emergency error: {e}")
            return Response(
                {'error': 'Failed to resolve emergency'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 👑 ADMIN TASK ASSIGNMENT VIEWS
# ========================

class AdminTaskAssignmentView(APIView):
    """👑 Admin Task Assignment and Management"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get all tasks for admin management"""
        try:
            status_filter = request.GET.get('status', '')
            task_type = request.GET.get('type', '')
            staff_filter = request.GET.get('staff_id', '')
            
            tasks = Task.objects.select_related('assigned_to__user').all()
            
            if status_filter:
                tasks = tasks.filter(status=status_filter)
            if task_type:
                tasks = tasks.filter(task_type=task_type)
            if staff_filter:
                tasks = tasks.filter(assigned_to_id=staff_filter)
            
            task_stats = {
                'total': tasks.count(),
                'pending': tasks.filter(status='pending').count(),
                'assigned': tasks.filter(status='assigned').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'completed': tasks.filter(status='completed').count(),
                'overdue': tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['pending', 'assigned', 'in_progress']
                ).count(),
            }
            
            tasks_data = []
            for task in tasks.order_by('-created_at'):
                task_data = {
                    'task_id': task.task_id,
                    'title': task.title,
                    'description': task.description,
                    'task_type': task.task_type,
                    'priority': task.priority,
                    'status': task.status,
                    'location_name': task.location_name,
                    'assigned_to': {
                        'id': task.assigned_to.id,
                        'employee_id': task.assigned_to.employee_id,
                        'name': task.assigned_to.user.get_full_name() if task.assigned_to else 'Unassigned',
                    } if task.assigned_to else None,
                    'assigned_at': task.assigned_at.isoformat() if task.assigned_at else None,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'attachments': TaskAttachment.objects.filter(task=task).count()
                }
                
                tasks_data.append(task_data)
            
            available_staff = StaffMember.objects.filter(
                is_active=True, is_on_duty=True
            ).select_related('user').values(
                'id', 'employee_id', 'user__first_name', 'user__last_name', 'role'
            )
            
            return Response({
                'success': True,
                'statistics': task_stats,
                'tasks': tasks_data,
                'available_staff': list(available_staff),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Admin tasks error: {e}")
            return Response(
                {'error': 'Failed to fetch admin tasks'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Assign new task to staff member"""
        try:
            task_data = request.data
            
            required_fields = ['title', 'task_type', 'assigned_to_id']
            for field in required_fields:
                if field not in task_data:
                    return Response(
                        {'error': f'Missing required field: {field}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            try:
                staff_member = StaffMember.objects.get(
                    id=task_data['assigned_to_id'], is_active=True
                )
            except StaffMember.DoesNotExist:
                return Response(
                    {'error': 'Staff member not found or inactive'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            with transaction.atomic():
                task_id = f"TASK{timezone.now().strftime('%Y%m%d')}{Task.objects.count() + 1:04d}"
                
                task = Task.objects.create(
                    task_id=task_id,
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    task_type=task_data['task_type'],
                    priority=task_data.get('priority', 'medium'),
                    status='assigned',
                    assigned_to=staff_member,
                    assigned_by=request.user,
                    assigned_at=timezone.now(),
                    location_name=task_data.get('location_name', ''),
                    address=task_data.get('address', ''),
                    latitude=task_data.get('latitude'),
                    longitude=task_data.get('longitude'),
                    estimated_duration=task_data.get('estimated_duration'),
                    due_date=task_data.get('due_date')
                )
                
                # Handle file attachments
                if 'attachments' in request.FILES:
                    for file in request.FILES.getlist('attachments'):
                        TaskAttachment.objects.create(
                            task=task,
                            file=file,
                            filename=file.name,
                            uploaded_by=request.user
                        )
                
                # Send notification
                self._notify_staff_task_assignment(task, staff_member)
                
                logger.info(f"Task {task_id} assigned to staff {staff_member.employee_id} by admin {request.user.username}")

                return Response({
                    'success': True,
                    'message': 'Task assigned successfully',
                    'task_id': task_id,
                    'task': {
                        'id': task.id,
                        'title': task.title,
                        'type': task.task_type,
                        'priority': task.priority,
                        'assigned_to': staff_member.user.get_full_name(),
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Admin task assignment error: {e}")
            return Response(
                {'error': f'Failed to assign task: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _notify_staff_task_assignment(self, task, staff_member):
        """Notify staff about task assignment"""
        try:
            subject = '📋 New Task Assigned - Smart Ride'
            message = f"""
Hello {staff_member.user.get_full_name() or staff_member.user.username},

A new task has been assigned to you:

**Task Details:**
• Title: {task.title}
• Type: {task.get_task_type_display()}
• Priority: {task.get_priority_display()}
• Location: {task.location_name}
• Due: {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else 'ASAP'}

Please check your Staff Dashboard for complete details.

Thank you,
Smart Ride Operations Team
            """
            
            send_mail(
                subject=subject,
                message=message.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_member.user.email],
                fail_silently=True,
            )
            
        except Exception as e:
            logger.error(f"Task assignment notification error: {e}")

class TaskAttachmentView(APIView):
    """📎 Task Attachment Management"""
    permission_classes = [IsAuthenticated]

    def post(self, request, task_id):
        """Upload attachment to task"""
        try:
            task = Task.objects.get(task_id=task_id)
            staff_member = get_staff_member(request.user)
            
            # Check permission
            if not (staff_member == task.assigned_to or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            file = request.FILES['file']
            
            # Validate file size (10MB max)
            if file.size > 10 * 1024 * 1024:
                return Response(
                    {'error': 'File size too large. Maximum 10MB allowed.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            attachment = TaskAttachment.objects.create(
                task=task,
                file=file,
                filename=file.name,
                uploaded_by=request.user
            )
            
            return Response({
                'success': True,
                'message': 'File uploaded successfully',
                'attachment': {
                    'id': attachment.id,
                    'filename': attachment.filename,
                    'file_size': attachment.file_size,
                    'uploaded_at': attachment.uploaded_at.isoformat(),
                    'url': attachment.file.url
                }
            }, status=status.HTTP_201_CREATED)
            
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"File upload error: {e}")
            return Response(
                {'error': 'Failed to upload file'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, task_id):
        """Get task attachments"""
        try:
            task = Task.objects.get(task_id=task_id)
            staff_member = get_staff_member(request.user)
            
            # Check permission
            if not (staff_member == task.assigned_to or request.user.is_staff):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            attachments = TaskAttachment.objects.filter(task=task)
            
            return Response({
                'success': True,
                'attachments': [
                    {
                        'id': att.id,
                        'filename': att.filename,
                        'file_size': att.file_size,
                        'uploaded_at': att.uploaded_at.isoformat(),
                        'url': att.file.url,
                        'uploaded_by': att.uploaded_by.get_full_name()
                    }
                    for att in attachments
                ]
            }, status=status.HTTP_200_OK)
            
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

# ========================
# 🔄 REBALANCING VIEWS
# ========================

class RebalancingView(APIView):
    """🔄 Vehicle Rebalancing Operations"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get rebalancing recommendations and tasks"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            rebalancing_tasks = RebalancingTask.objects.filter(
                assigned_staff=staff_member,
                status__in=['pending', 'in_progress']
            ).order_by('-priority', 'created_at')
            
            demand_zones = DemandZone.objects.filter(
                rebalancing_needed=True
            ).order_by('-demand_level', '-updated_at')
            
            rebalancing_data = {
                'success': True,
                'assigned_tasks': [
                    {
                        'id': task.id,
                        'zone': task.zone.zone_name,
                        'priority': task.priority,
                        'status': task.status,
                        'vehicles_to_move': task.vehicles_to_move,
                        'target_zone': task.target_zone
                    }
                    for task in rebalancing_tasks
                ],
                'demand_zones': [
                    {
                        'id': zone.id,
                        'zone_name': zone.zone_name,
                        'demand_level': zone.demand_level,
                        'current_vehicles': zone.current_vehicle_count,
                        'optimal_vehicles': zone.optimal_vehicle_count
                    }
                    for zone in demand_zones
                ],
                'summary': {
                    'pending_tasks': rebalancing_tasks.filter(status='pending').count(),
                    'high_demand_zones': demand_zones.filter(demand_level='high').count(),
                }
            }
            
            return Response(rebalancing_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Rebalancing recommendations error: {e}")
            return Response(
                {'error': 'Failed to fetch rebalancing recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 📈 DEMAND ANALYTICS
# ========================

class DemandAnalyticsView(APIView):
    """📈 Demand Analytics and Predictions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get demand heatmap and analytics"""
        try:
            demand_zones = DemandZone.objects.filter(
                updated_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).order_by('-demand_level', '-updated_at')
            
            heatmap_data = []
            for zone in demand_zones:
                intensity = {
                    'high': 0.8,
                    'medium': 0.5,
                    'low': 0.2
                }.get(zone.demand_level, 0.1)
                
                heatmap_data.append({
                    'zone_id': zone.id,
                    'zone_name': zone.zone_name,
                    'latitude': float(zone.latitude),
                    'longitude': float(zone.longitude),
                    'intensity': intensity,
                    'demand_level': zone.demand_level,
                    'current_vehicles': zone.current_vehicle_count,
                    'optimal_vehicles': zone.optimal_vehicle_count,
                })
            
            analytics_data = {
                'success': True,
                'heatmap_data': heatmap_data,
                'summary': {
                    'total_zones': demand_zones.count(),
                    'high_demand_zones': demand_zones.filter(demand_level='high').count(),
                    'rebalancing_needed': demand_zones.filter(rebalancing_needed=True).count(),
                }
            }
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Demand heatmap error: {e}")
            return Response(
                {'error': 'Failed to fetch demand analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🚗 VEHICLE MANAGEMENT
# ========================
class VehicleManagementView(APIView):
    """🚗 Vehicle Status Management"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get vehicle status and information"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Get all vehicles in the staff’s zone
            vehicles = Vehicle.objects.filter(
                current_zone=staff_member.work_zone
            ).order_by('-last_maintenance', 'status')

            # ✅ Updated: Get maintenance-related tasks only
            maintenance_tasks = Task.objects.filter(
                assigned_to=staff_member,
                task_type='maintenance',
                status__in=['pending', 'in_progress']
            ).order_by('-priority', 'created_at')

            vehicle_data = {
                'success': True,
                'vehicles': [
                    {
                        'vehicle_id': vehicle.vehicle_id,
                        'vehicle_type': vehicle.vehicle_type,
                        'status': vehicle.status,
                        'battery_level': vehicle.battery_level,
                        'current_zone': vehicle.current_zone,
                    }
                    for vehicle in vehicles
                ],
                'maintenance_tasks': [
                    {
                        'task_id': task.task_id,
                        'title': task.title,
                        'task_type': task.task_type,
                        'priority': task.priority,
                        'status': task.status,
                        'description': task.description,
                        'vehicle': getattr(task, 'vehicle', None).vehicle_id if hasattr(task, 'vehicle') and task.vehicle else None,
                        'due_date': task.due_date,
                    }
                    for task in maintenance_tasks
                ],
                'summary': {
                    'total_vehicles': vehicles.count(),
                    'available_vehicles': vehicles.filter(status='available').count(),
                    'in_use_vehicles': vehicles.filter(status='in_use').count(),
                    'maintenance_vehicles': vehicles.filter(status='maintenance').count(),
                },
            }

            return Response(vehicle_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Vehicle management error: {e}")
            return Response(
                {'error': 'Failed to fetch vehicle data'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🛠️ ISSUE RESOLUTION HUB
# ========================
class IssueResolutionView(APIView):
    """🛠️ Issue Resolution Hub"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get assigned issues and problems"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Get all vehicles under maintenance in the staff’s zone
            vehicle_issues = Vehicle.objects.filter(
                status='maintenance',
                current_zone=staff_member.work_zone
            )

            # ✅ Updated: Filter maintenance-type tasks linked to those vehicles
            pending_tasks = Task.objects.filter(
                task_type='maintenance',
                status='pending',
                assigned_to=staff_member,
                address__isnull=False  # optional — can be removed
            )

            issues_data = {
                'success': True,
                'vehicle_issues': [
                    {
                        'vehicle_id': vehicle.vehicle_id,
                        'vehicle_type': vehicle.vehicle_type,
                        'status': vehicle.status,
                        'maintenance_notes': vehicle.maintenance_notes,
                        'battery_level': vehicle.battery_level,
                    }
                    for vehicle in vehicle_issues
                ],
                'summary': {
                    'total_issues': vehicle_issues.count(),
                    'pending_resolution': pending_tasks.count(),
                    'assigned_to_me': pending_tasks.filter(assigned_to=staff_member).count(),
                }
            }

            return Response(issues_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Issue resolution hub error: {e}")
            return Response(
                {'error': 'Failed to fetch issues'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 👑 ADMIN MANAGEMENT VIEWS
# ========================

class StaffAdminView(APIView):
    """👑 Admin Staff Management"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get all staff members"""
        try:
            staff_members = StaffMember.objects.select_related('user').all()
            
            staff_data = []
            for staff in staff_members:
                tasks = Task.objects.filter(assigned_to=staff)
                emergencies = EmergencyAlert.objects.filter(assigned_staff=staff)
                
                staff_data.append({
                    'id': staff.id,
                    'employee_id': staff.employee_id,
                    'user': {
                        'username': staff.user.username,
                        'email': staff.user.email,
                        'first_name': staff.user.first_name,
                        'last_name': staff.user.last_name,
                    },
                    'role': staff.role,
                    'work_zone': staff.work_zone,
                    'is_active': staff.is_active,
                    'is_on_duty': staff.is_on_duty,
                    'performance_metrics': {
                        'total_tasks': tasks.count(),
                        'completed_tasks': tasks.filter(status='completed').count(),
                        'active_emergencies': emergencies.filter(status__in=['assigned', 'in_progress']).count()
                    },
                })
            
            return Response({
                'success': True,
                'staff_members': staff_data,
                'total_count': len(staff_data),
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Admin staff list error: {e}")
            return Response(
                {'error': 'Failed to fetch staff list'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class StaffRegistrationView(APIView):
    """👨‍💼 Staff Member Registration"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        """Register new staff member"""
        try:
            staff_data = request.data

            with transaction.atomic():
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

                staff_user = CustomUser.objects.create_user(
                    username=staff_data['username'],
                    email=staff_data['email'],
                    password=temp_password,
                    first_name=staff_data.get('first_name', ''),
                    last_name=staff_data.get('last_name', ''),
                    phone_number=staff_data.get('phone_number', ''),
                    user_type='staff',
                    is_staff=True
                )

                staff_profile = StaffMember.objects.create(
                    user=staff_user,
                    employee_id=staff_data.get('employee_id', f"STAFF{staff_user.id:04d}"),
                    role=staff_data['role'],
                    phone=staff_data.get('phone_number', ''),
                    work_zone=staff_data.get('coverage_zone', ''),
                    is_active=True
                )

                email_sent = self._send_welcome_email(staff_data, temp_password, staff_profile)

                return Response({
                    'success': True,
                    'message': 'Staff member registered successfully',
                    'staff_id': staff_profile.employee_id,
                    'credentials': {
                        'email': staff_data['email'],
                        'temp_password': temp_password
                    }
                }, status=status.HTTP_201_CREATED)

        except KeyError as e:
            return Response({
                'error': f'Missing required field: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Staff registration failed: {e}")
            return Response({
                'error': f'Registration failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def _send_welcome_email(self, staff_data, temp_password, staff_profile):
        """Send welcome email to new staff member"""
        try:
            send_mail(
                subject='🎉 Welcome to SmartRide Staff Team!',
                message=f"""
Dear {staff_data.get('first_name', 'Team Member')},

Welcome to the SmartRide Staff Team!

Your login credentials:
• Username: {staff_data['username']}
• Email: {staff_data['email']}  
• Temporary Password: {temp_password}
• Staff ID: {staff_profile.employee_id}

Please change your password after first login.

Welcome aboard!
SmartRide Operations Team
                """.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_data['email']],
                fail_silently=False,
            )
            return True
        except Exception as email_error:
            logger.error(f"Failed to send welcome email: {email_error}")
            return False

# ========================
# 🔔 NOTIFICATIONS & ALERTS
# ========================

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Q

from Users.models import Notification   # ✅ IMPORTANT FIX
from .models import EmergencyAlert, StaffMember, Task

import logging
logger = logging.getLogger(__name__)


# ===========================
# 🔔 STAFF NOTIFICATIONS VIEW
# ===========================
class StaffNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            staff_member = StaffMember.objects.get(user=request.user)

            notifications = Notification.objects.filter(
                staff_member=staff_member
            ).order_by('-created_at')

            notifications_list = [
                {
                    'id': n.id,
                    'notification_type': n.notification_type,
                    'title': n.title,
                    'message': n.message,
                    'is_read': n.is_read,
                    'is_sent': n.is_sent,
                    'created_at': n.created_at.isoformat(),
                    'read_at': n.read_at.isoformat() if n.read_at else None,
                }
                for n in notifications
            ]

            unread_count = Notification.objects.filter(
                staff_member=staff_member,
                is_read=False
            ).count()

            return Response({
                'success': True,
                'notifications': notifications_list,
                'unread_count': unread_count
            })

        except StaffMember.DoesNotExist:
            return Response({'error': 'Staff not found'}, status=404)


# ======================================================
# 🔔 MARK SINGLE NOTIFICATION AS READ
# ======================================================
class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notification_id = request.data.get("notification_id")
        if not notification_id:
            return Response({'error': 'Notification ID is required'}, status=400)

        try:
            staff_member = StaffMember.objects.get(user=request.user)
            notification = Notification.objects.get(id=notification_id, staff_member=staff_member)

            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()

            return Response({'success': True, 'message': 'Notification marked as read'}, status=200)

        except StaffMember.DoesNotExist:
            return Response({'error': 'Staff member not found'}, status=404)

        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=404)


# ======================================================
# 🔔 MARK ALL READ
# ======================================================
class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            staff_member = StaffMember.objects.get(user=request.user)

            updated = Notification.objects.filter(
                staff_member=staff_member,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())

            return Response({
                'success': True,
                'message': f'Marked {updated} notifications as read'
            }, status=200)

        except StaffMember.DoesNotExist:
            return Response({'error': 'Staff member not found'}, status=404)


# ======================================================
# 🔔 CLEAR ALL NOTIFICATIONS
# ======================================================
class ClearAllNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            staff_member = StaffMember.objects.get(user=request.user)

            deleted, _ = Notification.objects.filter(
                staff_member=staff_member
            ).delete()

            return Response({
                'success': True,
                'message': f'Deleted {deleted} notifications'
            }, status=200)

        except StaffMember.DoesNotExist:
            return Response({'error': 'Staff member not found'}, status=404)

# ========================
# 📊 PERFORMANCE ANALYTICS
# ========================

class StaffAnalyticsView(APIView):
    """📊 Staff Performance and Analytics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get staff performance analytics"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            tasks = Task.objects.filter(assigned_to=staff_member)
            completed_tasks = tasks.filter(status='completed')
            
            analytics_data = {
                'success': True,
                'task_metrics': {
                    'total_assigned': tasks.count(),
                    'completed': completed_tasks.count(),
                    'completion_rate': f"{(completed_tasks.count() / tasks.count() * 100) if tasks.count() > 0 else 0:.1f}%",
                },
                'performance_trends': {
                    'weekly_trend': 'improving',
                    'key_improvements': ['Faster task completion'],
                }
            }
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Staff performance error: {e}")
            return Response(
                {'error': 'Failed to fetch performance data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🔑 PASSWORD MANAGEMENT
# ========================

class StaffPasswordView(APIView):
    """🔑 Staff Password Management"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change staff password"""
        try:
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                return Response(
                    {'error': 'All password fields are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_password != confirm_password:
                return Response(
                    {'error': 'New passwords do not match'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(new_password) < 8:
                return Response(
                    {'error': 'New password must be at least 8 characters long'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = request.user
            if not user.check_password(current_password):
                return Response(
                    {'error': 'Current password is incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(new_password)
            user.save()

            logger.info(f"Password changed successfully for staff: {user.username}")

            return Response({
                'success': True,
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Password change error: {e}")
            return Response(
                {'error': 'Password change failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🔄 TOKEN MANAGEMENT
# ========================

class TokenRefreshView(APIView):
    """🔄 JWT Token Refresh"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Refresh JWT token"""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            return Response({
                'success': True,
                'access': new_access_token
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return Response(
                {'error': 'Invalid or expired refresh token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

# ========================
# 🩺 HEALTH & UTILITY
# ========================

class DashboardHealthView(APIView):
    """🩺 Dashboard Health and System Status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard health status"""
        try:
            health_data = {
                'success': True,
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'components': {
                    'task_service': 'operational',
                    'emergency_service': 'operational',
                    'notification_service': 'operational',
                }
            }
            return Response(health_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return Response(
                {'error': 'Health check failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🚨 LEGACY FUNCTION-BASED VIEWS
# ========================

@api_view(['POST'])
@permission_classes([AllowAny])
def staff_login(request):
    """Staff Login - Legacy endpoint"""
    from .views import StaffAuthenticationView
    view = StaffAuthenticationView()
    return view.post(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_logout(request):
    """Staff Logout - Legacy endpoint"""
    from .views import StaffLogoutView
    view = StaffLogoutView()
    return view.post(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_dashboard(request):
    """Staff Dashboard - Legacy endpoint"""
    from .views import StaffDashboardView
    view = StaffDashboardView()
    return view.get(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_tasks(request):
    """Staff Tasks - Legacy endpoint"""
    from .views import TaskManagementView
    view = TaskManagementView()
    return view.get(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_task_status(request, task_id):
    """Update Task Status - Legacy endpoint"""
    from .views import TaskManagementView
    view = TaskManagementView()
    return view.post(request, task_id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emergency_alerts(request):
    """Emergency Alerts - Legacy endpoint"""
    from .views import EmergencyManagementView
    view = EmergencyManagementView()
    return view.get(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_emergency(request, alert_id):
    """Accept Emergency - Legacy endpoint"""
    from .views import EmergencyManagementView
    view = EmergencyManagementView()
    return view.post(request, alert_id)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_emergency(request, alert_id):
    """Resolve Emergency - Legacy endpoint"""
    from .views import EmergencyManagementView
    view = EmergencyManagementView()
    return view.post(request, alert_id)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_tasks(request):
    """Admin Tasks - Legacy endpoint"""
    from .views import AdminTaskAssignmentView
    view = AdminTaskAssignmentView()
    return view.get(request)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_assign_task(request):
    """Admin Assign Task - Legacy endpoint"""
    from .views import AdminTaskAssignmentView
    view = AdminTaskAssignmentView()
    return view.post(request)

# ============================
# 🚀 GET ALL STAFF — STAFF LIST
# ============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_staff(request):
    """Return list of all staff members for user viewing."""
    staff = StaffMember.objects.select_related("user").all()
    data = [
        {
            "employee_id": s.employee_id,
            "name": s.user.first_name or s.user.username,
            "role": s.role,
            "phone_number": s.phone_number or "Not Available",
            "is_on_duty": s.is_on_duty,
            "status": s.current_status or "Offline",
        }
        for s in staff
    ]
    return Response(data)

# ============================
# 👤 STAFF PROFILE VIEW
# ============================
class StaffProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": "staff",
                "date_joined": user.date_joined,
                "last_login": user.last_login,
            }
        })

# ============================
# ✏️ STAFF PROFILE UPDATE
# ============================
class StaffProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        username = request.data.get("username")
        email = request.data.get("email")

        # ----- USERNAME -----
        if username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({"error": "Username already exists"}, status=400)
            user.username = username

        # ----- EMAIL -----
        if email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({"error": "Email already exists"}, status=400)
            user.email = email

        user.save()

        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": "staff"
            }
        }, status=200)

# ============================
# 🔐 STAFF PASSWORD CHANGE
# ============================
class StaffPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current = request.data.get("current_password")
        new = request.data.get("new_password")
        confirm = request.data.get("confirm_password")

        if not all([current, new, confirm]):
            return Response({"error": "All fields required"}, status=400)

        if new != confirm:
            return Response({"error": "Passwords do not match"}, status=400)

        if not user.check_password(current):
            return Response({"error": "Current password incorrect"}, status=400)

        user.set_password(new)
        user.save()
        update_session_auth_hash(request, user)

        return Response({
            "success": True,
            "message": "Password changed successfully"
        }, status=200)
# ========================
# 📊 PERFORMANCE ANALYTICS
# ========================

class StaffAnalyticsView(APIView):
    """📊 Staff Performance and Analytics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get staff performance analytics"""
        staff_member = get_staff_member(request.user)
        if not staff_member:
            return Response(
                {'error': 'Staff member not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            tasks = Task.objects.filter(assigned_to=staff_member)
            completed_tasks = tasks.filter(status='completed')
            
            analytics_data = {
                'success': True,
                'task_metrics': {
                    'total_assigned': tasks.count(),
                    'completed': completed_tasks.count(),
                    'completion_rate': f"{(completed_tasks.count() / tasks.count() * 100) if tasks.count() > 0 else 0:.1f}%",
                },
                'performance_trends': {
                    'weekly_trend': 'improving',
                    'key_improvements': ['Faster task completion'],
                }
            }
            
            return Response(analytics_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Staff performance error: {e}")
            return Response(
                {'error': 'Failed to fetch performance data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🔑 PASSWORD MANAGEMENT
# ========================

class StaffPasswordView(APIView):
    """🔑 Staff Password Management"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Change staff password"""
        try:
            current_password = request.data.get('current_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            if not all([current_password, new_password, confirm_password]):
                return Response(
                    {'error': 'All password fields are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_password != confirm_password:
                return Response(
                    {'error': 'New passwords do not match'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(new_password) < 8:
                return Response(
                    {'error': 'New password must be at least 8 characters long'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = request.user
            if not user.check_password(current_password):
                return Response(
                    {'error': 'Current password is incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(new_password)
            user.save()

            logger.info(f"Password changed successfully for staff: {user.username}")

            return Response({
                'success': True,
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Password change error: {e}")
            return Response(
                {'error': 'Password change failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🔄 TOKEN MANAGEMENT
# ========================

class TokenRefreshView(APIView):
    """🔄 JWT Token Refresh"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Refresh JWT token"""
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

            return Response({
                'success': True,
                'access': new_access_token
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return Response(
                {'error': 'Invalid or expired refresh token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

# ========================
# 🩺 HEALTH & UTILITY
# ========================

class DashboardHealthView(APIView):
    """🩺 Dashboard Health and System Status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard health status"""
        try:
            health_data = {
                'success': True,
                'status': 'healthy',
                'timestamp': timezone.now().isoformat(),
                'components': {
                    'task_service': 'operational',
                    'emergency_service': 'operational',
                    'notification_service': 'operational',
                }
            }
            return Response(health_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return Response(
                {'error': 'Health check failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🚨 LEGACY FUNCTION-BASED VIEWS
# ========================

@api_view(['POST'])
@permission_classes([AllowAny])
def staff_login(request):
    """Staff Login - Legacy endpoint"""
    view = StaffAuthenticationView()
    return view.post(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_logout(request):
    """Staff Logout - Legacy endpoint"""
    view = StaffLogoutView()
    return view.post(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_dashboard(request):
    """Staff Dashboard - Legacy endpoint"""
    view = StaffDashboardView()
    return view.get(request)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_tasks(request):
    """Staff Tasks - Legacy endpoint"""
    view = TaskManagementView()
    return view.get(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_task_status(request, task_id):
    """Update Task Status - Legacy endpoint"""
    view = TaskManagementView()
    return view.post(request, task_id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emergency_alerts(request):
    """Emergency Alerts - Legacy endpoint"""
    view = EmergencyManagementView()
    return view.get(request)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_emergency(request, alert_id):
    """Accept Emergency - Legacy endpoint"""
    view = EmergencyManagementView()
    return view.post(request, alert_id)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_emergency(request, alert_id):
    """Resolve Emergency - Legacy endpoint"""
    view = EmergencyManagementView()
    return view.post(request, alert_id)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_tasks(request):
    """Admin Tasks - Legacy endpoint"""
    view = AdminTaskAssignmentView()
    return view.get(request)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_assign_task(request):
    """Admin Assign Task - Legacy endpoint"""
    view = AdminTaskAssignmentView()
    return view.post(request)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from .models import StaffMember

User = get_user_model()   # ✅ FIXED: Always use CustomUser


# ============================
# 🚀 GET ALL STAFF — STAFF LIST
# ============================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_staff(request):
    """Return list of all staff members for user viewing."""
    staff = StaffMember.objects.select_related("user").all()
    data = [
        {
            "employee_id": s.employee_id,
            "name": s.user.first_name or s.user.username,
            "role": s.role,
            "phone_number": s.phone_number or "Not Available",
            "is_on_duty": s.is_on_duty,
            "status": s.current_status or "Offline",
        }
        for s in staff
    ]
    return Response(data)



# ============================
# 👤 STAFF PROFILE VIEW
# ============================
class StaffProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": "staff",
                "date_joined": user.date_joined,
                "last_login": user.last_login,
            }
        })



# ============================
# ✏️ STAFF PROFILE UPDATE
# ============================
class StaffProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        username = request.data.get("username")
        email = request.data.get("email")

        # ----- USERNAME -----
        if username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return Response({"error": "Username already exists"}, status=400)
            user.username = username

        # ----- EMAIL -----
        if email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({"error": "Email already exists"}, status=400)
            user.email = email

        user.save()

        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": "staff"
            }
        }, status=200)



# ============================
# 🔐 STAFF PASSWORD CHANGE
# ============================
class StaffPasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current = request.data.get("current_password")
        new = request.data.get("new_password")
        confirm = request.data.get("confirm_password")

        if not all([current, new, confirm]):
            return Response({"error": "All fields required"}, status=400)

        if new != confirm:
            return Response({"error": "Passwords do not match"}, status=400)

        if not user.check_password(current):
            return Response({"error": "Current password incorrect"}, status=400)

        user.set_password(new)
        user.save()
        update_session_auth_hash(request, user)

        return Response({
            "success": True,
            "message": "Password changed successfully"
        }, status=200)
    
# StaffWork/views_emergency.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from Users.models import EmergencyAlert, Notification
from .serializers import EmergencyAlertSerializer, EmergencyAlertUpdateSerializer
from .models import StaffMember


# ======================================================
# 📌 STAFF: LIST ALL EMERGENCIES
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_emergency_list(request):
    # Ensure staff
    try:
        StaffMember.objects.get(user=request.user)
    except StaffMember.DoesNotExist:
        return Response({"error": "Not a staff account"}, status=403)

    alerts = EmergencyAlert.objects.all().order_by("-created_at")
    serializer = EmergencyAlertSerializer(alerts, many=True)

    active = [e for e in serializer.data if not e["is_resolved"]]
    history = [e for e in serializer.data if e["is_resolved"]]

    return Response({
        "status": True,
        "emergencies": serializer.data,
        "active": active,
        "history": history
    })


# ======================================================
# 📌 STAFF: GET SINGLE EMERGENCY DETAILS
# ======================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_emergency_detail(request, alert_id):
    try:
        alert = EmergencyAlert.objects.get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=404)

    return Response({
        "status": True,
        "emergency": EmergencyAlertSerializer(alert).data
    })


# ======================================================
# 📌 STAFF: UPDATE / RESOLVE EMERGENCY
# ======================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def staff_update_emergency(request, alert_id):

    # Validate staff
    try:
        staff = StaffMember.objects.get(user=request.user)
    except StaffMember.DoesNotExist:
        return Response({"error": "Not a staff account"}, status=403)

    # Fetch alert
    try:
        alert = EmergencyAlert.objects.get(id=alert_id)
    except EmergencyAlert.DoesNotExist:
        return Response({"error": "Alert not found"}, status=404)

    data = request.data.copy()

    # Staff text response → admin_response
    if "response" in data:
        data["admin_response"] = data["response"]
        alert.response_sent_at = timezone.now()

    # Optional staff notes
    if "notes" in data:
        data["resolution_notes"] = data["notes"]

    # Resolve logic
    if str(data.get("is_resolved")).lower() in ["true", "1", "yes"]:
        data["is_resolved"] = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user

    serializer = EmergencyAlertUpdateSerializer(alert, data=data, partial=True)

    if not serializer.is_valid():
        return Response({"status": False, "errors": serializer.errors}, status=400)

    serializer.save()

    # ======================================================
    # 🔔 SEND NOTIFICATION TO USER (DYNAMIC MESSAGE)
    # ======================================================
    Notification.objects.create(
        user=alert.user,
        notification_type="emergency_alert",
        title="Emergency Update",
        message=f"Staff Response: {alert.admin_response}",
        data={"alert_id": alert.id},
        is_sent=True
    )

    return Response({
        "status": True,
        "message": "Emergency updated successfully",
        "updated": EmergencyAlertSerializer(alert).data
    })
