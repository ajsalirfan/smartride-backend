from django.utils.timesince import timesince
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model

# Users app models (project-local)
from Users.models import CustomUser, Vehicle, Ride, Payment, Complaint, EmergencyAlert, Notification, VehicleLocationHistory, Wallet

# Local admin models
from .models import (
    AdminDepartment, AdminRole, AdminUser, SystemConfiguration, AuditTrail,
    APIKey, DataExport, SystemHealthCheck, AdminLog, Analytics, SystemAlert,
    TrendingArea, Report, DashboardWidget, DemandPrediction, SmartRebalancingRoute,
    DynamicPricingRule, PredictiveMaintenanceAlert, FleetMaintenance
)

User = get_user_model()

# ========================
# 🔐 AUTHENTICATION SERIALIZERS
# ========================

class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

# ========================
# 👥 USER MANAGEMENT SERIALIZERS
# ========================

class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id','username','email','phone_number','is_active','is_verified','verification_status','created_at']
        read_only_fields = ['id','created_at']

class StaffRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    employee_id = serializers.CharField(required=True)
    role = serializers.ChoiceField(
        choices=[
            ('field_agent', 'Field Agent'),
            ('supervisor', 'Supervisor'), 
            ('manager', 'Manager'),
            ('admin', 'Admin')
        ],
        required=True
    )
    work_zone = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name', 
            'phone_number', 'employee_id', 'role', 'work_zone'
        ]
    
    def create(self, validated_data):
        # Extract staff-specific data
        employee_id = validated_data.pop('employee_id')
        role = validated_data.pop('role')
        work_zone = validated_data.pop('work_zone', '')
        
        # Create the user
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            user_type='staff',
            is_staff=True
        )
        
        # Create staff member profile
        from StaffWork.models import StaffMember
        staff_member = StaffMember.objects.create(
            user=user,
            employee_id=employee_id,
            role=role,
            work_zone=work_zone,
            is_active=True
        )
        
        return user

    def to_representation(self, instance):
        # Return staff member data instead of user data
        from StaffWork.models import StaffMember
        try:
            staff_member = StaffMember.objects.get(user=instance)
            return {
                'id': staff_member.id,
                'employee_id': staff_member.employee_id,
                'username': instance.username,
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
                'phone_number': instance.phone_number,
                'role': staff_member.role,
                'work_zone': staff_member.work_zone,
                'is_active': staff_member.is_active
            }
        except StaffMember.DoesNotExist:
            return super().to_representation(instance)

class StaffMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        from StaffWork.models import StaffMember
        model = StaffMember
        fields = [
            'id', 'user', 'username', 'email', 'first_name', 'last_name',
            'employee_id', 'role', 'work_zone', 'is_active', 'is_on_duty',
            'current_status', 'created_at'
        ]

# ========================
# 📋 TASK MANAGEMENT SERIALIZERS
# ========================

class TaskAssignmentSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        from StaffWork.models import Task
        model = Task
        fields = [
            'task_id', 'title', 'description', 'task_type', 'priority', 'status',
            'assigned_to', 'assigned_to_name', 'assigned_by', 'assigned_by_name',
            'location_name', 'address', 'estimated_duration', 'due_date'
        ]

class TaskManagementSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        from StaffWork.models import Task
        model = Task
        fields = '__all__'

# ========================
# 🚗 VEHICLE & RIDE MANAGEMENT
# ========================

class VehicleManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id','vehicle_id','vehicle_type','status','battery_level','is_active','current_location_lat','current_location_lng']
        read_only_fields = ['id']

class RideManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = ['id','user','vehicle','start_time','end_time','status','distance','cost']
        read_only_fields = ['id','start_time','end_time']

class PaymentManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id','user','amount','status','payment_method','transaction_id','payment_initiated_at']
        read_only_fields = ['id','payment_initiated_at']

class ComplaintManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id','user','complaint_type','title','status','priority','created_at']
        read_only_fields = ['id','created_at']

# ========================
# 🔧 FLEET MAINTENANCE
# ========================

class FleetMaintenanceSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = FleetMaintenance
        fields = '__all__'

# ========================
# 🚨 ALERTS & NOTIFICATIONS
# ========================

class EmergencyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAlert
        fields = ['id','user','alert_type','message','location_lat','location_lng','priority','is_acknowledged','created_at']
        read_only_fields = ['id','created_at']

class SystemAlertSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    
    class Meta:
        model = SystemAlert
        fields = '__all__'

# ========================
# 📊 ANALYTICS & REPORTS
# ========================

class AnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analytics
        fields = '__all__'

class TrendingAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendingArea
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = '__all__'

class DashboardWidgetSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DashboardWidget
        fields = '__all__'

class DemandPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandPrediction
        fields = '__all__'

class SmartRebalancingRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartRebalancingRoute
        fields = '__all__'

class DynamicPricingRuleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DynamicPricingRule
        fields = '__all__'

class PredictiveMaintenanceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PredictiveMaintenanceAlert
        fields = '__all__'

# ========================
# 👑 ADMIN MANAGEMENT
# ========================

class AdminDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminDepartment
        fields = ['id', 'name', 'code', 'description', 'permissions', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class AdminRoleSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    class Meta:
        model = AdminRole
        fields = ['id', 'name', 'department', 'department_name', 'permissions', 'access_level', 'can_manage_users', 'can_manage_vehicles', 'is_active']
        read_only_fields = ['id']

class AdminUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ['id', 'user', 'department', 'role', 'employee_id', 'permissions', 'is_active']
        read_only_fields = ['id']

class AdminUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'user', 'username', 'email', 'first_name', 'last_name',
            'department', 'role', 'employee_id', 'is_active', 'last_active',
            'created_at'
        ]

class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = ['id', 'key', 'value', 'data_type', 'category', 'description', 'is_public', 'updated_by', 'updated_at']
        read_only_fields = ['id', 'updated_at']

class AuditTrailSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin_user.username', read_only=True)
    class Meta:
        model = AuditTrail
        fields = ['id', 'admin_user', 'admin_name', 'action', 'category', 'resource_type', 'resource_id', 'old_values', 'new_values', 'ip_address', 'user_agent', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class APIKeySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = APIKey
        fields = ['id', 'name', 'key', 'permissions', 'is_active', 'created_by', 'created_by_name', 'created_at', 'last_used', 'expires_at']
        read_only_fields = ['id', 'created_at', 'last_used']

class DataExportSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    class Meta:
        model = DataExport
        fields = ['id', 'requested_by', 'requested_by_name', 'export_name', 'data_model', 'filters', 'format', 'status', 'file', 'file_size', 'record_count', 'error_message', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']

class SystemHealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemHealthCheck
        fields = ['id', 'component', 'status', 'response_time', 'error_message', 'last_check', 'created_at']
        read_only_fields = ['id', 'last_check', 'created_at']

class AdminLogSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin_user.username', read_only=True)
    class Meta:
        model = AdminLog
        fields = ['id','admin_user','admin_name','action','action_type','details','timestamp']
        read_only_fields = ['id','timestamp']

# ========================
# 🔄 BULK OPERATIONS
# ========================

class BulkUserActionSerializer(serializers.Serializer):
    user_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    action = serializers.ChoiceField(choices=[('deactivate','deactivate'),('activate','activate'),('reset_password','reset_password')])

class BulkVehicleActionSerializer(serializers.Serializer):
    vehicle_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    action = serializers.ChoiceField(choices=[('set_maintenance','set_maintenance'),('set_active','set_active')])

# ========================
# ========================
# ⚙️ ADMIN SETTINGS SERIALIZER
# ========================

class AdminSettingsSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        from .models import AdminSettings
        model = AdminSettings
        fields = '__all__'

# ========================
# 📈 DEMAND ANALYTICS SERIALIZER
# ========================

class DemandAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import DemandAnalytics
        model = DemandAnalytics
        fields = '__all__'