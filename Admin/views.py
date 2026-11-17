import logging
import random
import string
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.db.models import Count, Sum, Q, F
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta

from .permissions import IsAdminUser, IsSuperAdmin, IsFleetManager, IsSupportStaff
from .serializers import (
    AdminLoginSerializer, UserManagementSerializer, VehicleManagementSerializer,
    RideManagementSerializer, PaymentManagementSerializer, ComplaintManagementSerializer,
    FleetMaintenanceSerializer, SystemAlertSerializer, AdminLogSerializer,
    StaffRegistrationSerializer, TaskAssignmentSerializer, BulkUserActionSerializer,
    BulkVehicleActionSerializer, TaskManagementSerializer, StaffMemberSerializer,
    AdminUserSerializer
)

# ADD THESE MISSING IMPORTS:
from .models import (
    APIKey, AuditTrail, DashboardWidget, DemandPrediction, DynamicPricingRule, 
    FleetMaintenance, PredictiveMaintenanceAlert, Report, SmartRebalancingRoute, 
    SystemAlert, SystemConfiguration, TrendingArea, AdminSettings, DemandAnalytics
)

from .serializers import (
    EmergencyAlertSerializer, SystemConfigurationSerializer, AuditTrailSerializer,
    APIKeySerializer, TrendingAreaSerializer, DemandPredictionSerializer,
    SmartRebalancingRouteSerializer, DynamicPricingRuleSerializer,
    PredictiveMaintenanceAlertSerializer, ReportSerializer, DashboardWidgetSerializer,
    AdminSettingsSerializer, DemandAnalyticsSerializer
)
# NO OTHER IMPORTS NEEDED HERE
# Remove the problematic import line entirely
# from smartride_backend.Admin.models import APIKey, AuditTrail, DashboardWidget, DemandPrediction, DynamicPricingRule, FleetMaintenance, PredictiveMaintenanceAlert, Report, SmartRebalancingRoute, SystemAlert, SystemConfiguration, TrendingArea
# ========================
# 🔐 AUTHENTICATION CLASSES
# ========================

class AdminAuthenticationView(APIView):
    """Admin login with JWT tokens"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)
        
        if not user or not (user.is_staff or user.is_superuser):
            return Response({'error': 'Invalid admin credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        
        # Log admin login
        try:
            from .models import AdminLog
            AdminLog.objects.create(
                admin_user=user, 
                action='Admin login', 
                action_type='login'
            )
        except Exception as e:
            logging.error(f"Admin login logging failed: {e}")

        return Response({
            'user': {
                'id': user.id, 
                'username': user.username, 
                'email': getattr(user, 'email', ''),
                'is_superuser': user.is_superuser
            },
            'tokens': {
                'refresh': str(refresh), 
                'access': str(refresh.access_token)
            }
        })

class AdminProfileView(APIView):
    """Get current admin profile"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            from .models import AdminUser
            profile = AdminUser.objects.get(user=request.user)
            from .serializers import AdminUserSerializer
            serializer = AdminUserSerializer(profile)
            return Response(serializer.data)
        except Exception:
            return Response({
                'id': request.user.id,
                'username': request.user.username,
                'email': getattr(request.user, 'email', ''),
                'is_superuser': request.user.is_superuser
            })

# ========================
# 📊 DASHBOARD CLASSES
# ========================

class AdminDashboardView(APIView):
    """Comprehensive admin dashboard"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            # Import models inside method to avoid circular imports
            from Users.models import CustomUser, Vehicle, Ride, Payment
            from StaffWork.models import StaffMember, Task, EmergencyAlert
            
            # User statistics
            total_users = CustomUser.objects.count()
            total_admins = CustomUser.objects.filter(is_staff=True).count()
            total_staff = StaffMember.objects.filter(is_active=True).count()
            
            # Vehicle statistics
            total_vehicles = Vehicle.objects.count()
            available_vehicles = Vehicle.objects.filter(status='available').count()
            maintenance_vehicles = Vehicle.objects.filter(status='maintenance').count()
            
            # Ride statistics
            active_rides = Ride.objects.filter(status='active').count()
            completed_rides_today = Ride.objects.filter(
                status='completed',
                start_time__date=timezone.now().date()
            ).count()
            
            # Revenue statistics
            today_revenue = Payment.objects.filter(
                payment_completed_at__date=timezone.now().date(), 
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Task statistics
            pending_tasks = Task.objects.filter(status='assigned').count()
            active_emergencies = EmergencyAlert.objects.filter(
                status__in=['reported', 'assigned']
            ).count()

            dashboard_data = {
                'user_metrics': {
                    'total_users': total_users,
                    'total_admins': total_admins,
                    'total_staff': total_staff,
                    'active_rides': active_rides,
                },
                'vehicle_metrics': {
                    'total_vehicles': total_vehicles,
                    'available_vehicles': available_vehicles,
                    'maintenance_vehicles': maintenance_vehicles,
                },
                'financial_metrics': {
                    'today_revenue': float(today_revenue),
                    'completed_rides_today': completed_rides_today,
                },
                'operational_metrics': {
                    'pending_tasks': pending_tasks,
                    'active_emergencies': active_emergencies,
                },
                'timestamp': timezone.now().isoformat()
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            logging.error(f"Admin dashboard error: {e}")
            return Response(
                {'error': 'Failed to load dashboard data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class QuickStatsView(APIView):
    """Quick statistics for admin dashboard"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            from Users.models import CustomUser, Vehicle, Ride, Payment
            
            today = timezone.now().date()
            data = {
                'total_users': CustomUser.objects.count(),
                'total_vehicles': Vehicle.objects.count(),
                'active_rides': Ride.objects.filter(status='active').count(),
                'today_revenue': Payment.objects.filter(
                    payment_completed_at__date=today, 
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0,
            }
            return Response(data)
        except Exception as e:
            logging.error(f"Quick stats error: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 👥 USER MANAGEMENT CLASSES
# ========================

class UserManagementViewSet(viewsets.ModelViewSet):
    """Complete user management for admins"""
    serializer_class = UserManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import CustomUser
        qs = CustomUser.objects.all().order_by('-date_joined')
        
        # Filter by status
        status_q = self.request.GET.get('status')
        if status_q:
            qs = qs.filter(verification_status=status_q)
            
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            
        return qs

    @action(detail=True, methods=['post'])
    def verify_user(self, request, pk=None):
        """Verify user account"""
        user = self.get_object()
        user.is_verified = True
        user.verification_status = 'approved'
        user.verification_approved_at = timezone.now()
        user.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user, 
            action=f"Approved verification for {user.username}", 
            action_type='user_verified', 
            target_user=user
        )
        
        # Send notification
        from Users.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='system',
            title='Account Verified',
            message='Your account has been verified by admin'
        )
        
        return Response({'message': f'User {user.username} verified successfully'})

    @action(detail=True, methods=['post'])
    def reject_user(self, request, pk=None):
        """Reject user verification"""
        user = self.get_object()
        reason = request.data.get('reason', 'Documents not clear')
        
        user.is_verified = False
        user.verification_status = 'rejected'
        user.verification_rejected_at = timezone.now()
        user.verification_rejection_reason = reason
        user.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user, 
            action=f"Rejected verification for {user.username}", 
            action_type='user_rejected', 
            target_user=user
        )
        
        # Send notification
        from Users.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='system',
            title='Verification Rejected',
            message=f'Your verification was rejected: {reason}'
        )
        
        return Response({'message': f'User {user.username} verification rejected'})

    @action(detail=True, methods=['post'])
    def warn_user(self, request, pk=None):
        """Send warning to user"""
        user = self.get_object()
        reason = request.data.get('reason', 'Violation of terms')
        
        # Send notification
        from Users.models import Notification
        Notification.objects.create(
            user=user,
            notification_type='system',
            title='Account Warning',
            message=f'Admin warning: {reason}'
        )
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user, 
            action=f"Warned user {user.username}: {reason}", 
            action_type='user_warned', 
            target_user=user
        )
        
        return Response({'message': f'Warning sent to {user.username}'})

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Bulk user actions"""
        serializer = BulkUserActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        user_ids = serializer.validated_data['user_ids']
        action = serializer.validated_data['action']
        users = self.get_queryset().filter(id__in=user_ids)
        
        for user in users:
            if action == 'deactivate':
                user.is_active = False
                user.save()
            elif action == 'activate':
                user.is_active = True
                user.save()
            elif action == 'verify':
                user.is_verified = True
                user.verification_status = 'approved'
                user.save()
                
        # Log bulk action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user, 
            action=f"Bulk user action: {action}", 
            action_type='system_update', 
            details={'count': users.count()}
        )
        
        return Response({
            'message': 'Bulk action completed', 
            'affected_users': users.count()
        })

# ========================
# 👨‍💼 STAFF MANAGEMENT CLASSES
# ========================

class StaffRegistrationView(APIView):
    """Register new staff members with email credentials"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = StaffRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            with transaction.atomic():
                staff_data = serializer.validated_data
                
                # Generate temporary password
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                
                # Create staff user account
                from Users.models import CustomUser
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
                
                # Create staff profile
                from StaffWork.models import StaffMember
                staff_profile = StaffMember.objects.create(
                    user=staff_user,
                    employee_id=staff_data.get('employee_id', f"STAFF{staff_user.id:04d}"),
                    role=staff_data['role'],
                    phone=staff_data.get('phone_number', ''),
                    work_zone=staff_data.get('work_zone', ''),
                    is_active=True
                )
                
                # Send welcome email with credentials
                email_sent = self._send_welcome_email(staff_data, temp_password, staff_profile)
                
                # Log staff registration
                from .models import AdminLog
                AdminLog.objects.create(
                    admin_user=request.user,
                    action=f"Registered new staff member: {staff_profile.employee_id}",
                    action_type='staff_registered'
                )
                
                return Response({
                    'success': True,
                    'message': 'Staff member registered successfully',
                    'staff_id': staff_profile.employee_id,
                    'email_sent': email_sent,
                    'credentials': {
                        'username': staff_data['username'],
                        'email': staff_data['email'],
                        'temp_password': temp_password
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logging.error(f"Staff registration failed: {e}")
            return Response({
                'error': f'Registration failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    def _send_welcome_email(self, staff_data, temp_password, staff_profile):
        """Send welcome email to new staff member"""
        try:
            subject = '🎉 Welcome to SmartRide Staff Team!'
            message = f"""
Dear {staff_data.get('first_name', 'Team Member')},

Welcome to the SmartRide Staff Team! Your staff account has been created.

🔐 YOUR LOGIN CREDENTIALS:
• Username: {staff_data['username']}
• Email: {staff_data['email']}  
• Temporary Password: {temp_password}
• Staff ID: {staff_profile.employee_id}
• Role: {staff_data['role']}

🚀 GETTING STARTED:
1. Login at: {getattr(settings, 'STAFF_LOGIN_URL', 'http://localhost:8000/api/staffwork/auth/login/')}
2. Change your password after first login
3. Check your assigned tasks and schedule

📱 STAFF FEATURES:
• Task Management & Assignment
• Emergency Response System  
• Vehicle Status Updates
• Real-time Notifications
• Performance Analytics

🔒 SECURITY:
• Please change your password immediately after first login
• Keep your credentials confidential

Need help? Contact staff support.

Welcome aboard!
SmartRide Operations Team
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_data['email']],
                fail_silently=False,
            )
            return True
        except Exception as e:
            logging.error(f"Failed to send welcome email: {e}")
            return False

class StaffManagementViewSet(viewsets.ModelViewSet):
    """Staff member management for admins"""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from StaffWork.models import StaffMember
        return StaffMember.objects.select_related('user').all().order_by('-created_at')
    
    def get_serializer_class(self):
        from .serializers import StaffMemberSerializer
        return StaffMemberSerializer

    @action(detail=True, methods=['post'])
    def deactivate_staff(self, request, pk=None):
        """Deactivate staff member"""
        staff = self.get_object()
        staff.is_active = False
        staff.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Deactivated staff member: {staff.employee_id}",
            action_type='staff_deactivated'
        )
        
        return Response({'message': f'Staff member {staff.employee_id} deactivated'})

    @action(detail=True, methods=['post'])
    def activate_staff(self, request, pk=None):
        """Activate staff member"""
        staff = self.get_object()
        staff.is_active = True
        staff.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Activated staff member: {staff.employee_id}",
            action_type='staff_activated'
        )
        
        return Response({'message': f'Staff member {staff.employee_id} activated'})

# ========================
# 📋 TASK ASSIGNMENT CLASSES
# ========================

class TaskAssignmentView(APIView):
    """Assign tasks to staff members"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = TaskAssignmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            with transaction.atomic():
                task_data = serializer.validated_data
                
                # Get staff member
                from StaffWork.models import StaffMember
                staff_member = StaffMember.objects.get(
                    id=task_data['assigned_to_id'], 
                    is_active=True
                )
                
                # Create task
                from StaffWork.models import Task
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
                        from StaffWork.models import TaskAttachment
                        TaskAttachment.objects.create(
                            task=task,
                            file=file,
                            filename=file.name,
                            uploaded_by=request.user
                        )
                
                # Send notification to staff
                self._notify_staff_task_assignment(task, staff_member)
                
                # Log task assignment
                from .models import AdminLog
                AdminLog.objects.create(
                    admin_user=request.user,
                    action=f"Assigned task {task_id} to {staff_member.employee_id}",
                    action_type='task_assigned',
                    details={'task_id': task_id, 'staff_id': staff_member.employee_id}
                )
                
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
                
        except StaffMember.DoesNotExist:
            return Response(
                {'error': 'Staff member not found or inactive'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logging.error(f"Task assignment error: {e}")
            return Response(
                {'error': f'Failed to assign task: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _notify_staff_task_assignment(self, task, staff_member):
        """Notify staff about task assignment"""
        try:
            from Users.models import Notification
            Notification.objects.create(
                user=staff_member.user,
                notification_type='task_assigned',
                title='New Task Assigned',
                message=f'You have been assigned a new task: {task.title}'
            )
            
            # Send email notification
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
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[staff_member.user.email],
                fail_silently=True,
            )
            
        except Exception as e:
            logging.error(f"Task assignment notification error: {e}")

class TaskManagementViewSet(viewsets.ModelViewSet):
    """Admin task management"""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from StaffWork.models import Task
        return Task.objects.select_related('assigned_to__user', 'assigned_by').all().order_by('-created_at')
    
    def get_serializer_class(self):
        from .serializers import TaskManagementSerializer
        return TaskManagementSerializer

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['completed', 'cancelled', 'in_progress']:
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.status = new_status
        if new_status == 'completed':
            task.completed_at = timezone.now()
        task.save()
        
        # Log status update
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Updated task {task.task_id} status to {new_status}",
            action_type='task_updated'
        )
        
        return Response({'message': f'Task status updated to {new_status}'})

# ========================
# 🚗 VEHICLE MANAGEMENT CLASSES
# ========================

class VehicleManagementViewSet(viewsets.ModelViewSet):
    """Vehicle management for fleet managers"""
    serializer_class = VehicleManagementSerializer
    permission_classes = [IsFleetManager]
    
    def get_queryset(self):
        from Users.models import Vehicle
        return Vehicle.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        vehicle = serializer.save()
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=self.request.user, 
            action=f"Added vehicle {vehicle.vehicle_id}", 
            action_type='vehicle_added', 
            target_vehicle=vehicle
        )

    def perform_update(self, serializer):
        vehicle = serializer.save()
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=self.request.user, 
            action=f"Updated vehicle {vehicle.vehicle_id}", 
            action_type='vehicle_updated', 
            target_vehicle=vehicle
        )

    def perform_destroy(self, instance):
        vid = instance.vehicle_id
        instance.delete()
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=self.request.user, 
            action=f"Removed vehicle {vid}", 
            action_type='vehicle_removed'
        )

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Bulk vehicle actions"""
        serializer = BulkVehicleActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        vehicle_ids = serializer.validated_data['vehicle_ids']
        action = serializer.validated_data['action']
        vehicles = self.get_queryset().filter(id__in=vehicle_ids)
        
        for vehicle in vehicles:
            if action == 'set_maintenance':
                vehicle.status = 'maintenance'
            elif action == 'set_active':
                vehicle.status = 'available'
            elif action == 'deactivate':
                vehicle.is_active = False
            vehicle.save()
            
        # Log bulk action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user, 
            action=f"Bulk vehicle action: {action}", 
            action_type='system_update', 
            details={'count': vehicles.count()}
        )
        
        return Response({
            'message': 'Bulk vehicle action completed', 
            'affected': vehicles.count()
        })

    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """Get vehicle maintenance history"""
        vehicle = self.get_object()
        from .models import FleetMaintenance
        records = FleetMaintenance.objects.filter(vehicle=vehicle).order_by('-scheduled_date')
        serializer = FleetMaintenanceSerializer(records, many=True)
        return Response(serializer.data)

class GPSMonitoringView(APIView):
    """Real-time GPS monitoring of vehicles"""
    permission_classes = [IsFleetManager]
    
    def get(self, request):
        from Users.models import Vehicle, VehicleLocationHistory
        vehicles = Vehicle.objects.prefetch_related('location_history').all()
        data = []
        
        for vehicle in vehicles:
            latest = vehicle.location_history.first()
            if latest:
                data.append({
                    'vehicle_id': vehicle.vehicle_id,
                    'lat': float(latest.latitude),
                    'lng': float(latest.longitude),
                    'battery': vehicle.battery_level,
                    'status': vehicle.status,
                    'last_updated': latest.timestamp
                })
                
        return Response(data)

# ========================
# 📊 ANALYTICS & REPORTS CLASSES
# ========================

class AnalyticsView(APIView):
    """Comprehensive analytics for admin"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        analytics_type = request.GET.get('type', 'overview')
        
        if analytics_type == 'user_growth':
            return self._get_user_growth_analytics()
        elif analytics_type == 'revenue':
            return self._get_revenue_analytics()
        elif analytics_type == 'ride_patterns':
            return self._get_ride_patterns()
        else:
            return self._get_overview_analytics()
    
    def _get_overview_analytics(self):
        """Get overview analytics"""
        from Users.models import CustomUser, Ride, Payment
        from StaffWork.models import Task
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        data = {
            'user_metrics': {
                'total_users': CustomUser.objects.count(),
                'new_users_week': CustomUser.objects.filter(date_joined__gte=week_ago).count(),
                'active_users_week': CustomUser.objects.filter(last_login__gte=week_ago).count(),
            },
            'ride_metrics': {
                'total_rides': Ride.objects.count(),
                'rides_this_week': Ride.objects.filter(start_time__gte=week_ago).count(),
                'completion_rate': self._calculate_ride_completion_rate(),
            },
            'financial_metrics': {
                'total_revenue': Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0,
                'revenue_this_week': Payment.objects.filter(
                    payment_completed_at__gte=week_ago, 
                    status='completed'
                ).aggregate(total=Sum('amount'))['total'] or 0,
            },
            'operational_metrics': {
                'pending_tasks': Task.objects.filter(status='assigned').count(),
                'completed_tasks_week': Task.objects.filter(
                    status='completed',
                    completed_at__gte=week_ago
                ).count(),
            }
        }
        
        return Response(data)
    
    def _calculate_ride_completion_rate(self):
        """Calculate ride completion rate"""
        from Users.models import Ride
        total_rides = Ride.objects.count()
        completed_rides = Ride.objects.filter(status='completed').count()
        
        if total_rides > 0:
            return round((completed_rides / total_rides) * 100, 2)
        return 0

# ========================
# 🔔 NOTIFICATION CLASSES
# ========================

class BroadcastNotificationView(APIView):
    """Broadcast notifications to all users"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        title = request.data.get('title', 'System Notification')
        message = request.data.get('message', '')
        notification_type = request.data.get('type', 'system')
        
        if not message:
            return Response(
                {'error': 'Message is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from Users.models import CustomUser, Notification
            users = CustomUser.objects.all()
            count = 0
            
            for user in users:
                Notification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    title=title,
                    message=message
                )
                count += 1
                
            # Log broadcast
            from .models import AdminLog
            AdminLog.objects.create(
                admin_user=request.user,
                action=f"Broadcast notification to {count} users: {title}",
                action_type='broadcast_notification'
            )
            
            return Response({
                'message': f'Notification broadcasted to {count} users',
                'count': count
            })
            
        except Exception as e:
            logging.error(f"Broadcast notification error: {e}")
            return Response(
                {'error': 'Failed to broadcast notification'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# ========================
# 🚨 LEGACY FUNCTIONAL VIEWS (Keep only essential)
# ========================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_logout(request):
    """Admin logout - keep as functional for simplicity"""
    try:
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user, 
            action='Admin logout', 
            action_type='logout'
        )
    except Exception as e:
        logging.error(f"Admin logout logging failed: {e}")
    
    return Response({'message': 'Logged out successfully'})

@api_view(['GET'])
@permission_classes([IsAdminUser])
def recent_activity(request):
    """Recent admin activity - keep as functional"""
    from .models import AdminLog
    logs = AdminLog.objects.select_related('admin_user').order_by('-timestamp')[:50]
    serializer = AdminLogSerializer(logs, many=True)
    return Response(serializer.data)


# ========================
# 🚗 RIDE MANAGEMENT CLASSES
# ========================

class RideViewSet(viewsets.ModelViewSet):
    """Ride management for admins"""
    serializer_class = RideManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import Ride
        return Ride.objects.select_related('user', 'vehicle').all().order_by('-start_time')

    @action(detail=True, methods=['post'])
    def cancel_ride(self, request, pk=None):
        """Cancel a ride"""
        ride = self.get_object()
        ride.status = 'cancelled'
        ride.end_time = timezone.now()
        ride.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Cancelled ride {ride.id}",
            action_type='ride_cancelled'
        )
        
        return Response({'message': 'Ride cancelled successfully'})

# ========================
# 💰 PAYMENT MANAGEMENT CLASSES
# ========================

class PaymentViewSet(viewsets.ModelViewSet):
    """Payment management for admins"""
    serializer_class = PaymentManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import Payment
        return Payment.objects.select_related('user').all().order_by('-payment_initiated_at')

    @action(detail=True, methods=['post'])
    def refund_payment(self, request, pk=None):
        """Refund a payment"""
        payment = self.get_object()
        payment.status = 'refunded'
        payment.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Refunded payment {payment.transaction_id}",
            action_type='payment_refunded'
        )
        
        return Response({'message': 'Payment refunded successfully'})

# ========================
# 🎯 COMPLAINT MANAGEMENT CLASSES
# ========================

class ComplaintViewSet(viewsets.ModelViewSet):
    """Complaint management for admins"""
    serializer_class = ComplaintManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import Complaint
        return Complaint.objects.select_related('user').all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve_complaint(self, request, pk=None):
        """Resolve a complaint"""
        complaint = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        complaint.status = 'resolved'
        complaint.resolution_notes = resolution_notes
        complaint.resolved_at = timezone.now()
        complaint.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Resolved complaint {complaint.id}",
            action_type='complaint_resolved'
        )
        
        return Response({'message': 'Complaint resolved successfully'})

    @action(detail=True, methods=['post'])
    def escalate_complaint(self, request, pk=None):
        """Escalate a complaint"""
        complaint = self.get_object()
        complaint.priority = 'high'
        complaint.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Escalated complaint {complaint.id}",
            action_type='complaint_escalated'
        )
        
        return Response({'message': 'Complaint escalated successfully'})

# ========================
# 🚨 EMERGENCY ALERT MANAGEMENT
# ========================

class EmergencyAlertViewSet(viewsets.ModelViewSet):
    """Emergency alert management for admins"""
    serializer_class = EmergencyAlertSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import EmergencyAlert
        return EmergencyAlert.objects.select_related('user').all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def acknowledge_alert(self, request, pk=None):
        """Acknowledge an emergency alert"""
        alert = self.get_object()
        alert.is_acknowledged = True
        alert.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Acknowledged emergency alert {alert.id}",
            action_type='alert_acknowledged'
        )
        
        return Response({'message': 'Emergency alert acknowledged'})

# ========================
# 📊 SYSTEM ANALYTICS VIEWS
# ========================

class SystemAnalyticsView(APIView):
    """System-wide analytics and reporting"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        analytics_type = request.GET.get('type', 'overview')
        
        if analytics_type == 'revenue':
            return self._get_revenue_analytics()
        elif analytics_type == 'user_growth':
            return self._get_user_growth_analytics()
        elif analytics_type == 'vehicle_utilization':
            return self._get_vehicle_utilization_analytics()
        else:
            return self._get_system_overview_analytics()
    
    def _get_system_overview_analytics(self):
        """Get system overview analytics"""
        from Users.models import CustomUser, Vehicle, Ride, Payment
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        data = {
            'period': {
                'today': today.isoformat(),
                'week_ago': week_ago.isoformat(),
                'month_ago': month_ago.isoformat(),
            },
            'users': {
                'total': CustomUser.objects.count(),
                'new_today': CustomUser.objects.filter(date_joined__date=today).count(),
                'new_week': CustomUser.objects.filter(date_joined__date__gte=week_ago).count(),
                'new_month': CustomUser.objects.filter(date_joined__date__gte=month_ago).count(),
                'active_today': CustomUser.objects.filter(last_login__date=today).count(),
            },
            'vehicles': {
                'total': Vehicle.objects.count(),
                'available': Vehicle.objects.filter(status='available').count(),
                'in_use': Vehicle.objects.filter(status='in_use').count(),
                'maintenance': Vehicle.objects.filter(status='maintenance').count(),
            },
            'rides': {
                'total': Ride.objects.count(),
                'completed_today': Ride.objects.filter(status='completed', start_time__date=today).count(),
                'active_now': Ride.objects.filter(status='active').count(),
                'cancelled_today': Ride.objects.filter(status='cancelled', start_time__date=today).count(),
            },
            'revenue': {
                'total': float(Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0),
                'today': float(Payment.objects.filter(status='completed', payment_completed_at__date=today).aggregate(total=Sum('amount'))['total'] or 0),
                'this_week': float(Payment.objects.filter(status='completed', payment_completed_at__date__gte=week_ago).aggregate(total=Sum('amount'))['total'] or 0),
            }
        }
        
        return Response(data)
    
    def _get_revenue_analytics(self):
        """Get detailed revenue analytics"""
        from Users.models import Payment
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        dates = [today - timedelta(days=i) for i in range(7, -1, -1)]
        
        revenue_data = []
        for date in dates:
            daily_revenue = Payment.objects.filter(
                status='completed',
                payment_completed_at__date=date
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            revenue_data.append({
                'date': date.isoformat(),
                'revenue': float(daily_revenue),
                'transactions': Payment.objects.filter(
                    status='completed',
                    payment_completed_at__date=date
                ).count()
            })
        
        return Response({
            'revenue_trend': revenue_data,
            'total_week_revenue': sum(item['revenue'] for item in revenue_data),
            'average_daily_revenue': sum(item['revenue'] for item in revenue_data) / len(revenue_data) if revenue_data else 0
        })
    
    def _get_user_growth_analytics(self):
        """Get user growth analytics"""
        from Users.models import CustomUser
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        dates = [today - timedelta(days=i) for i in range(30, -1, -1)]
        
        growth_data = []
        cumulative_users = 0
        
        for date in dates:
            daily_signups = CustomUser.objects.filter(date_joined__date=date).count()
            cumulative_users += daily_signups
            
            growth_data.append({
                'date': date.isoformat(),
                'daily_signups': daily_signups,
                'cumulative_users': cumulative_users
            })
        
        return Response({
            'user_growth': growth_data,
            'total_signups': cumulative_users,
            'average_daily_signups': sum(item['daily_signups'] for item in growth_data) / len(growth_data) if growth_data else 0
        })
    
    def _get_vehicle_utilization_analytics(self):
        """Get vehicle utilization analytics"""
        from Users.models import Vehicle, Ride
        from datetime import timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        vehicles = Vehicle.objects.all()
        utilization_data = []
        
        for vehicle in vehicles:
            rides_count = Ride.objects.filter(
                vehicle=vehicle,
                start_time__date__gte=week_ago
            ).count()
            
            total_hours_used = Ride.objects.filter(
                vehicle=vehicle,
                start_time__date__gte=week_ago,
                status='completed'
            ).aggregate(
                total_hours=Sum(F('end_time') - F('start_time'))
            )['total_hours']
            
            if total_hours_used:
                hours_used = total_hours_used.total_seconds() / 3600
            else:
                hours_used = 0
            
            utilization_data.append({
                'vehicle_id': vehicle.vehicle_id,
                'vehicle_type': vehicle.vehicle_type,
                'rides_count': rides_count,
                'hours_used': round(hours_used, 2),
                'status': vehicle.status,
                'battery_level': vehicle.battery_level
            })
        
        return Response({
            'vehicle_utilization': utilization_data,
            'summary': {
                'total_vehicles': len(utilization_data),
                'active_vehicles': len([v for v in utilization_data if v['rides_count'] > 0]),
                'average_rides_per_vehicle': sum(v['rides_count'] for v in utilization_data) / len(utilization_data) if utilization_data else 0,
                'total_rides_week': sum(v['rides_count'] for v in utilization_data)
            }
        })

# ========================
# 🔧 SYSTEM CONFIGURATION VIEWS
# ========================

class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """System configuration management"""
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return SystemConfiguration.objects.all().order_by('category', 'key')

# ========================
# 📝 AUDIT TRAIL VIEWS
# ========================

class AuditTrailViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit trail viewing"""
    serializer_class = AuditTrailSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return AuditTrail.objects.select_related('admin_user').all().order_by('-timestamp')

# ========================
# 🔑 API KEY MANAGEMENT
# ========================

class APIKeyViewSet(viewsets.ModelViewSet):
    """API Key management"""
    serializer_class = APIKeySerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return APIKey.objects.select_related('created_by').all().order_by('-created_at')

    def perform_create(self, serializer):
        api_key = serializer.save(created_by=self.request.user)
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=self.request.user,
            action=f"Created API key: {api_key.name}",
            action_type='api_key_created'
        )



# ========================
# 🚗 RIDE MANAGEMENT CLASSES
# ========================

class RideViewSet(viewsets.ModelViewSet):
    """Ride management for admins"""
    serializer_class = RideManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import Ride
        return Ride.objects.select_related('user', 'vehicle').all().order_by('-start_time')

    @action(detail=True, methods=['post'])
    def cancel_ride(self, request, pk=None):
        """Cancel a ride"""
        ride = self.get_object()
        ride.status = 'cancelled'
        ride.end_time = timezone.now()
        ride.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Cancelled ride {ride.id}",
            action_type='ride_cancelled'
        )
        
        return Response({'message': 'Ride cancelled successfully'})

# ========================
# 💰 PAYMENT MANAGEMENT CLASSES
# ========================

class PaymentViewSet(viewsets.ModelViewSet):
    """Payment management for admins"""
    serializer_class = PaymentManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import Payment
        return Payment.objects.select_related('user').all().order_by('-payment_initiated_at')

    @action(detail=True, methods=['post'])
    def refund_payment(self, request, pk=None):
        """Refund a payment"""
        payment = self.get_object()
        payment.status = 'refunded'
        payment.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Refunded payment {payment.transaction_id}",
            action_type='payment_refunded'
        )
        
        return Response({'message': 'Payment refunded successfully'})

# ========================
# 🎯 COMPLAINT MANAGEMENT CLASSES
# ========================

class ComplaintViewSet(viewsets.ModelViewSet):
    """Complaint management for admins"""
    serializer_class = ComplaintManagementSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from Users.models import Complaint
        return Complaint.objects.select_related('user').all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve_complaint(self, request, pk=None):
        """Resolve a complaint"""
        complaint = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        complaint.status = 'resolved'
        complaint.resolution_notes = resolution_notes
        complaint.resolved_at = timezone.now()
        complaint.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Resolved complaint {complaint.id}",
            action_type='complaint_resolved'
        )
        
        return Response({'message': 'Complaint resolved successfully'})

# ========================
# 🔧 MAINTENANCE MANAGEMENT
# ========================

class MaintenanceViewSet(viewsets.ModelViewSet):
    """Maintenance management for admins"""
    serializer_class = FleetMaintenanceSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return FleetMaintenance.objects.all().order_by('-scheduled_date')

    @action(detail=True, methods=['post'])
    def complete_maintenance(self, request, pk=None):
        """Complete maintenance task"""
        maintenance = self.get_object()
        maintenance.status = 'completed'
        maintenance.completed_date = timezone.now()
        maintenance.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Completed maintenance {maintenance.id}",
            action_type='maintenance_completed'
        )
        
        return Response({'message': 'Maintenance completed successfully'})

# ========================
# 🚨 SYSTEM ALERTS
# ========================

class SystemAlertViewSet(viewsets.ModelViewSet):
    """System alert management"""
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return SystemAlert.objects.select_related('created_by', 'resolved_by').all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve_alert(self, request, pk=None):
        """Resolve system alert"""
        alert = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        alert.is_resolved = True
        alert.resolved_by = request.user
        alert.resolved_at = timezone.now()
        alert.resolution_notes = resolution_notes
        alert.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Resolved system alert {alert.id}",
            action_type='alert_resolved'
        )
        
        return Response({'message': 'Alert resolved successfully'})

# ========================
# 📈 TRENDING AREAS
# ========================

class TrendingAreaViewSet(viewsets.ModelViewSet):
    """Trending areas management"""
    serializer_class = TrendingAreaSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return TrendingArea.objects.all().order_by('-popularity_score')

# ========================
# 🔮 DEMAND PREDICTIONS
# ========================

class DemandPredictionViewSet(viewsets.ModelViewSet):
    """Demand prediction management"""
    serializer_class = DemandPredictionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return DemandPrediction.objects.all().order_by('-prediction_time')

# ========================
# 🔄 SMART REBALANCING
# ========================

class SmartRebalancingViewSet(viewsets.ModelViewSet):
    """Smart rebalancing management"""
    serializer_class = SmartRebalancingRouteSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return SmartRebalancingRoute.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def execute_route(self, request, pk=None):
        """Execute rebalancing route"""
        route = self.get_object()
        route.status = 'in_progress'
        route.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Executed rebalancing route {route.route_name}",
            action_type='rebalancing_executed'
        )
        
        return Response({'message': 'Rebalancing route execution started'})

# ========================
# 💰 DYNAMIC PRICING
# ========================

class DynamicPricingRuleViewSet(viewsets.ModelViewSet):
    """Dynamic pricing rule management"""
    serializer_class = DynamicPricingRuleSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return DynamicPricingRule.objects.all().order_by('name')

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle pricing rule active status"""
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"{'Activated' if rule.is_active else 'Deactivated'} pricing rule {rule.name}",
            action_type='pricing_rule_updated'
        )
        
        return Response({
            'message': f'Pricing rule {"activated" if rule.is_active else "deactivated"}',
            'is_active': rule.is_active
        })

# ========================
# ⚠️ PREDICTIVE MAINTENANCE
# ========================

class PredictiveMaintenanceViewSet(viewsets.ModelViewSet):
    """Predictive maintenance alert management"""
    serializer_class = PredictiveMaintenanceAlertSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return PredictiveMaintenanceAlert.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve_alert(self, request, pk=None):
        """Resolve predictive maintenance alert"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user.username
        alert.save()
        
        # Log action
        from .models import AdminLog
        AdminLog.objects.create(
            admin_user=request.user,
            action=f"Resolved predictive maintenance alert {alert.id}",
            action_type='predictive_alert_resolved'
        )
        
        return Response({'message': 'Predictive maintenance alert resolved'})

# ========================
# 📄 REPORTS
# ========================

class ReportViewSet(viewsets.ModelViewSet):
    """Report management"""
    serializer_class = ReportSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return Report.objects.select_related('generated_by').all().order_by('-generated_at')

    @action(detail=True, methods=['post'])
    def generate_report(self, request, pk=None):
        """Generate report"""
        report = self.get_object()
        # Add report generation logic here
        return Response({'message': 'Report generation started'})

# ========================
# 📊 DASHBOARD WIDGETS
# ========================

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """Dashboard widget management"""
    serializer_class = DashboardWidgetSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return DashboardWidget.objects.all().order_by('position')

# ========================
# ⚙️ ADMIN SETTINGS
# ========================

class AdminSettingsViewSet(viewsets.ModelViewSet):
    """Admin settings management"""
    serializer_class = AdminSettingsSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        from .models import AdminSettings
        return AdminSettings.objects.all().order_by('category', 'key')

# ========================
# 📊 ADDITIONAL ANALYTICS VIEWS
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def ride_analytics_detailed(request):
    """Detailed ride analytics"""
    from Users.models import Ride
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    data = {
        'total_rides': Ride.objects.count(),
        'completed_rides': Ride.objects.filter(status='completed').count(),
        'active_rides': Ride.objects.filter(status='active').count(),
        'cancelled_rides': Ride.objects.filter(status='cancelled').count(),
        'rides_today': Ride.objects.filter(start_time__date=today).count(),
        'rides_this_week': Ride.objects.filter(start_time__date__gte=week_ago).count(),
        'average_ride_duration': 0,  # Calculate based on your data
        'revenue_today': 0,  # Calculate based on your data
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def ride_detail_view(request, ride_id):
    """Get ride details"""
    from Users.models import Ride
    try:
        ride = Ride.objects.get(id=ride_id)
        serializer = RideManagementSerializer(ride)
        return Response(serializer.data)
    except Ride.DoesNotExist:
        return Response({'error': 'Ride not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def revenue_analytics(request):
    """Revenue analytics"""
    from Users.models import Payment
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    data = {
        'total_revenue': float(Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0),
        'revenue_today': float(Payment.objects.filter(status='completed', payment_completed_at__date=today).aggregate(total=Sum('amount'))['total'] or 0),
        'revenue_this_week': float(Payment.objects.filter(status='completed', payment_completed_at__date__gte=week_ago).aggregate(total=Sum('amount'))['total'] or 0),
        'revenue_this_month': float(Payment.objects.filter(status='completed', payment_completed_at__date__gte=month_ago).aggregate(total=Sum('amount'))['total'] or 0),
        'transactions_today': Payment.objects.filter(payment_completed_at__date=today).count(),
        'average_transaction_value': 0,  # Calculate based on your data
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def demand_analytics(request):
    """Demand analytics"""
    from .models import DemandAnalytics
    data = DemandAnalytics.objects.all().order_by('-timestamp')[:100]
    serializer = DemandAnalyticsSerializer(data, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_analytics(request):
    """User analytics"""
    from Users.models import CustomUser
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    data = {
        'total_users': CustomUser.objects.count(),
        'new_users_today': CustomUser.objects.filter(date_joined__date=today).count(),
        'new_users_week': CustomUser.objects.filter(date_joined__date__gte=week_ago).count(),
        'new_users_month': CustomUser.objects.filter(date_joined__date__gte=month_ago).count(),
        'active_users_today': CustomUser.objects.filter(last_login__date=today).count(),
        'active_users_week': CustomUser.objects.filter(last_login__date__gte=week_ago).count(),
        'verified_users': CustomUser.objects.filter(is_verified=True).count(),
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def advanced_analytics(request):
    """Advanced analytics dashboard"""
    # Combine multiple analytics
    return Response({
        'user_analytics': user_analytics(request._request).data,
        'ride_analytics': ride_analytics_detailed(request._request).data,
        'revenue_analytics': revenue_analytics(request._request).data,
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def real_time_metrics(request):
    """Real-time system metrics"""
    from Users.models import CustomUser, Vehicle, Ride
    from StaffWork.models import Task, EmergencyAlert
    
    data = {
        'online_users': CustomUser.objects.filter(last_login__gte=timezone.now() - timedelta(minutes=30)).count(),
        'active_rides': Ride.objects.filter(status='active').count(),
        'available_vehicles': Vehicle.objects.filter(status='available').count(),
        'pending_tasks': Task.objects.filter(status='assigned').count(),
        'active_emergencies': EmergencyAlert.objects.filter(status__in=['reported', 'assigned']).count(),
        'system_health': 'healthy',  # Add your system health logic
        'timestamp': timezone.now().isoformat(),
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def smart_StaffWork_dashboard(request):
    """Smart StaffWork dashboard"""
    from StaffWork.models import StaffMember, Task
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    
    data = {
        'total_staff': StaffMember.objects.filter(is_active=True).count(),
        'on_duty_staff': StaffMember.objects.filter(is_on_duty=True).count(),
        'total_tasks': Task.objects.count(),
        'completed_tasks_today': Task.objects.filter(status='completed', completed_at__date=today).count(),
        'pending_tasks': Task.objects.filter(status__in=['assigned', 'in_progress']).count(),
        'staff_performance': [],  # Add staff performance metrics
    }
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_activity_logs(request):
    """Admin activity logs"""
    from .models import AdminLog
    logs = AdminLog.objects.select_related('admin_user').order_by('-timestamp')[:100]
    serializer = AdminLogSerializer(logs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_user_action(request):
    """Bulk user actions"""
    serializer = BulkUserActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    # Implement bulk user actions
    return Response({'message': 'Bulk action completed'})

@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_vehicle_action(request):
    """Bulk vehicle actions"""
    serializer = BulkVehicleActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    # Implement bulk vehicle actions
    return Response({'message': 'Bulk action completed'})

@api_view(['GET'])
@permission_classes([IsAdminUser])
def api_documentation(request):
    """API documentation"""
    return Response({
        'message': 'Admin API Documentation',
        'endpoints': [
            {'path': '/api/admin/auth/login/', 'method': 'POST', 'description': 'Admin login'},
            {'path': '/api/admin/dashboard/', 'method': 'GET', 'description': 'Admin dashboard'},
            # Add more endpoints as needed
        ]
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def maintenance_schedule(request):
    """Maintenance schedule"""
    from .models import FleetMaintenance
    maintenance = FleetMaintenance.objects.filter(status='scheduled').order_by('scheduled_date')
    serializer = FleetMaintenanceSerializer(maintenance, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_emergency_alert(request):
    """Send emergency alert"""
    # Implement emergency alert logic
    return Response({'message': 'Emergency alert sent'})



from django.shortcuts import render
from Users.models import CustomUser, Vehicle, EmergencyAlert
from StaffWork.models import StaffMember

def dashboard(request):
    total_users = CustomUser.objects.count()
    total_staff = StaffMember.objects.count()
    total_vehicles = Vehicle.objects.count()
    total_alerts = EmergencyAlert.objects.count()

    context = {
        'total_users': total_users,
        'total_staff': total_staff,
        'total_vehicles': total_vehicles,
        'total_alerts': total_alerts,
    }
    return render(request, 'admin/dashboard.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
from django.urls import reverse

from Users.models import CustomUser
from StaffWork.models import StaffMember


def register_staff(request):
    """
    Admin-only form to register new staff.
    Creates CustomUser (staff type) + StaffMember entry.
    Sends credentials to staff email.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        role = request.POST.get("role") or "Field Agent"

        # Check if email already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "⚠️ A user with this email already exists.")
            return redirect("Admin:register_staff")

        # Create safe unique username
        base_username = name.lower().replace(" ", "")
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        try:
            # ✅ Create CustomUser (staff account)
            user = CustomUser.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                user_type="staff",
                is_active=True,
                is_verified=True
            )

            # ✅ Create StaffMember record
            StaffMember.objects.create(
                user=user,
                employee_id=f"STF{user.id:04d}",
                role=role,
                is_on_duty=False,
                current_status="Available"
            )

            # ✅ Send credentials via email
            try:
                send_mail(
                    subject="Welcome to SmartRide Staff Portal",
                    message=(
                        f"Hello {name},\n\n"
                        f"Welcome to SmartRide Team!\n\n"
                        f"Your login credentials:\n"
                        f"Email: {email}\nPassword: {password}\n\n"
                        f"Login at: https://yourdomain.com/staff-login/\n"
                        f"Please change your password after first login.\n\n"
                        f"— SmartRide Admin Team"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER),
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception as e:
                messages.warning(request, f"⚠️ Staff created, but email not sent ({e})")

            # ✅ Success message
            messages.success(request, f"✅ Staff '{name}' registered successfully and credentials sent via email.")

            # ✅ Redirect to Admin Dashboard
            return redirect("/admin-site/")

        except IntegrityError:
            messages.error(request, "⚠️ Duplicate username or database error. Try again.")
            return redirect("Admin:register_staff")

        except Exception as e:
            messages.error(request, f"⚠️ Unexpected error: {e}")
            return redirect("Admin:register_staff")

    # Default GET (Render the form)
    return render(request, "admin/admin_register_staff.html")

