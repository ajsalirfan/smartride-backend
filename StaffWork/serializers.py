# StaffWork/serializers.py - FINAL VERSION ✅
from rest_framework import serializers
from .models import (
    Staff, StaffMember, StaffTask, Task, Vehicle,
    RebalancingTask, DemandZone, TaskAttachment, DemandHeatmap,
    StaffWorkAnalytics, StaffPerformance, Notification,
    DemandPrediction, DynamicPricingRule, PredictiveMaintenanceAlert
)
from Users.models import EmergencyAlert

# ========== STAFF MANAGEMENT SERIALIZERS ==========

class StaffSerializer(serializers.ModelSerializer):
    """Serializer for Staff model (alias of StaffMember)"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'user_name', 'user_email', 'employee_id', 'role',
            'phone', 'work_zone', 'is_active', 'is_on_duty', 'current_status',
            'current_latitude', 'current_longitude', 'last_location_update',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaffMemberSerializer(serializers.ModelSerializer):
    """Serializer for StaffMember model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = StaffMember
        fields = [
            'id', 'user', 'user_name', 'user_email', 'employee_id', 'role',
            'phone', 'work_zone', 'is_active', 'is_on_duty', 'current_status',
            'current_latitude', 'current_longitude', 'last_location_update',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaffTaskSerializer(serializers.ModelSerializer):
    """Serializer for legacy StaffTask or related task view"""
    staff_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    
    class Meta:
        model = StaffTask
        fields = [
            'task_id', 'staff_name', 'title', 'description', 'assigned_at',
            'due_date', 'status', 'created_at'
        ]
        read_only_fields = ['task_id', 'assigned_at', 'created_at']


# ========== TASK MANAGEMENT SERIALIZERS ==========

class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.user.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'task_id', 'title', 'description', 'task_type', 'priority', 'status',
            'assigned_to', 'assigned_to_name', 'assigned_by', 'assigned_by_name',
            'assigned_at', 'location_name', 'address', 'latitude', 'longitude',
            'estimated_duration', 'actual_duration', 'due_date', 'started_at',
            'completed_at', 'task_data', 'is_active', 'created_at', 'updated_at',
            'deleted_at', 'deleted_by'
        ]
        read_only_fields = ['task_id', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    """For admin/staff task creation"""
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'task_type', 'priority', 'assigned_to',
            'location_name', 'address', 'latitude', 'longitude',
            'estimated_duration', 'due_date'
        ]


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """For updating only task progress/status"""
    class Meta:
        model = Task
        fields = ['status', 'task_data']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = TaskAttachment
        fields = [
            'id', 'task', 'file', 'filename', 'file_size', 'uploaded_by',
            'uploaded_by_name', 'uploaded_at', 'description'
        ]
        read_only_fields = ['id', 'file_size', 'uploaded_at']

# StaffWork/serializers.py
from rest_framework import serializers
from Users.models import EmergencyAlert, CustomUser


# ======================================================
# 🔹 EMERGENCY ALERT SERIALIZER (STAFF VIEW)
# ======================================================
class EmergencyAlertSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = EmergencyAlert
        fields = [
            "id",
            "alert_type",
            "message",
            "location_lat",
            "location_lng",
            "location_name",

            # User Info
            "user",
            "username",
            "user_email",

            # Admin/Staff responses
            "admin_response",
            "response_sent_at",
            "resolution_notes",

            # Status
            "is_resolved",
            "resolved_at",
            "resolved_by",

            # Timestamps
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "username",
            "user_email",
            "created_at",
            "resolved_at",
            "resolved_by",
            "response_sent_at"
        ]


# ======================================================
# 🔹 EMERGENCY ALERT UPDATE SERIALIZER (STAFF ACTION)
# ======================================================
class EmergencyAlertUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmergencyAlert
        fields = [
            "admin_response",
            "resolution_notes",
            "is_resolved",
            "resolved_by",
        ]
        read_only_fields = ["resolved_by"]

# ========== VEHICLE SERIALIZER ==========

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_id', 'vehicle_type', 'status', 'current_zone',
            'latitude', 'longitude', 'last_location_update', 'battery_level',
            'last_maintenance', 'maintenance_notes', 'total_distance',
            'photo', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['vehicle_id', 'created_at', 'updated_at']


# ========== REBALANCING & DEMAND SERIALIZERS ==========

class RebalancingTaskSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.zone_name', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.user.get_full_name', read_only=True)
    
    class Meta:
        model = RebalancingTask
        fields = [
            'id', 'zone', 'zone_name', 'assigned_staff', 'assigned_staff_name',
            'priority', 'status', 'vehicles_to_move', 'vehicles_moved',
            'source_zone', 'target_zone', 'estimated_duration', 'started_at',
            'completed_at', 'completion_notes', 'optimized_route',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DemandZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandZone
        fields = [
            'id', 'zone_name', 'demand_level', 'latitude', 'longitude', 'radius',
            'current_vehicle_count', 'optimal_vehicle_count', 'predicted_demand',
            'rebalancing_needed', 'last_updated', 'created_at'
        ]
        read_only_fields = ['id', 'last_updated', 'created_at']


class DemandHeatmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandHeatmap
        fields = [
            'id', 'zone_name', 'demand_score', 'vehicle_count',
            'recommended_vehicles', 'last_updated', 'is_active'
        ]
        read_only_fields = ['id', 'last_updated']


# ========== PREDICTION & ANALYTICS SERIALIZERS ==========

class DemandPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemandPrediction
        fields = [
            'prediction_id', 'zone_name', 'prediction_type', 'prediction_time',
            'demand_score', 'confidence_level', 'latitude', 'longitude', 'radius_km',
            'predicted_vehicles_needed', 'weather_impact', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['prediction_id', 'created_at', 'updated_at']


class DynamicPricingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DynamicPricingRule
        fields = [
            'rule_id', 'rule_name', 'rule_type', 'zone_name',
            'base_price_multiplier', 'min_price', 'max_price', 'activation_threshold',
            'is_active', 'start_time', 'end_time', 'days_of_week',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['rule_id', 'created_at', 'updated_at']


class PredictiveMaintenanceAlertSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.CharField(source='vehicle.vehicle_id', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.user.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = PredictiveMaintenanceAlert
        fields = [
            'alert_id', 'vehicle', 'vehicle_id', 'alert_type', 'severity',
            'description', 'predicted_failure_date', 'confidence_score',
            'is_resolved', 'resolved_at', 'resolved_by', 'resolved_by_name',
            'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['alert_id', 'created_at', 'updated_at']


# ========== ANALYTICS & PERFORMANCE SERIALIZERS ==========

class StaffWorkAnalyticsSerializer(serializers.ModelSerializer):
    staff_member_name = serializers.CharField(source='staff_member.user.get_full_name', read_only=True)
    staff_employee_id = serializers.CharField(source='staff_member.employee_id', read_only=True)
    
    class Meta:
        model = StaffWorkAnalytics
        fields = [
            'id', 'staff_member', 'staff_member_name', 'staff_employee_id',
            'date', 'tasks_completed', 'emergencies_handled',
            'avg_completion_time', 'on_time_completion_rate', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StaffPerformanceSerializer(serializers.ModelSerializer):
    staff_member_name = serializers.CharField(source='staff_member.user.get_full_name', read_only=True)
    staff_employee_id = serializers.CharField(source='staff_member.employee_id', read_only=True)
    
    class Meta:
        model = StaffPerformance
        fields = [
            'id', 'staff_member', 'staff_member_name', 'staff_employee_id',
            'total_tasks_assigned', 'tasks_completed', 'completion_rate',
            'average_response_time', 'average_task_duration', 'quality_score',
            'customer_rating', 'emergencies_handled', 'emergency_response_rate',
            'period_start', 'period_end', 'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']

class NotificationSerializer(serializers.ModelSerializer):
    staff_member_name = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    read_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'staff_member',
            'staff_member_name',
            'notification_type',
            'title',
            'message',
            'related_task',
            'related_emergency',
            'related_vehicle',
            'is_read',
            'is_urgent',
            'is_sent',
            'created_at',
            'read_at',
        ]
        read_only_fields = ['id', 'created_at', 'read_at']

    def get_staff_member_name(self, obj):
        """Return full name or username."""
        try:
            name = obj.staff_member.user.get_full_name()
            return name if name else obj.staff_member.user.username
        except:
            return None

# ========== DASHBOARD & UTILITY SERIALIZERS ==========

class StaffDashboardSerializer(serializers.Serializer):
    staff_info = serializers.DictField()
    today_stats = serializers.DictField()
    current_tasks = serializers.ListField()
    active_emergencies = serializers.ListField()
    quick_actions = serializers.ListField()


class TaskSummarySerializer(serializers.Serializer):
    total_tasks = serializers.IntegerField()
    completed_today = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    active_emergencies = serializers.IntegerField()


class PerformanceMetricsSerializer(serializers.Serializer):
    efficiency_score = serializers.FloatField()
    on_time_completion_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    quality_score = serializers.FloatField()
    total_tasks_completed = serializers.IntegerField()
