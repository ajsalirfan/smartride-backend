# admin/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class AdminDepartment(models.Model):
    """🏢 Admin departments with specific permissions"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Admin Department"
        verbose_name_plural = "Admin Departments"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AdminRole(models.Model):
    """👨‍💼 Admin roles with specific access levels"""
    ROLE_LEVELS = [
        ('super_admin', '👑 Super Admin'),
        ('department_head', '👨‍💼 Department Head'),
        ('manager', '💼 Manager'),
        ('support_staff', '👨‍🔧 Support Staff'),
        ('viewer', '👀 Viewer'),
    ]
    
    name = models.CharField(max_length=100)
    department = models.ForeignKey(AdminDepartment, on_delete=models.CASCADE, null=True, blank=True)
    role_level = models.CharField(max_length=50, choices=ROLE_LEVELS, default='support_staff')
    permissions = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Admin Role"
        verbose_name_plural = "Admin Roles"
        ordering = ['department', 'name']
    
    def __str__(self):
        if self.department:
            return f"{self.name} - {self.department.name}"
        return self.name


class AdminUser(models.Model):
    """👨‍💼 Admin user profiles with department and role assignments"""
    DEPARTMENT_CHOICES = [
        ('fleet', '🚗 Fleet Management'),
        ('support', '🎯 Customer Support'), 
        ('finance', '💰 Finance & Payments'),
        ('safety', '🛡️ Safety & Compliance'),
        ('operations', '⚡ Operations'),
        ('analytics', '📊 Analytics & Reporting'),
        ('super_admin', '👑 Super Admin')
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='operations')
    role = models.ForeignKey(AdminRole, on_delete=models.SET_NULL, null=True, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    permissions = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_department_display()})"
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = f"ADM{self.user.id:04d}"
        super().save(*args, **kwargs)


class SystemConfiguration(models.Model):
    """⚙️ System-wide configuration settings"""
    CONFIG_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
        ('float', 'Float'),
    ]
    
    CONFIG_CATEGORIES = [
        ('general', 'General'),
        ('payment', 'Payment'),
        ('ride', 'Ride Settings'),
        ('vehicle', 'Vehicle Management'),
        ('notification', 'Notifications'),
        ('security', 'Security'),
        ('api', 'API Settings'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict, blank=True)
    data_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='string')
    category = models.CharField(max_length=50, choices=CONFIG_CATEGORIES, default='general')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        ordering = ['category', 'key']
    
    def __str__(self):
        return self.key


class AuditTrail(models.Model):
    """📝 Comprehensive audit trail for all admin actions"""
    ACTION_CATEGORIES = [
        ('user_management', 'User Management'),
        ('vehicle_management', 'Vehicle Management'),
        ('ride_management', 'Ride Management'),
        ('payment_management', 'Payment Management'),
        ('system_config', 'System Configuration'),
        ('security', 'Security'),
        ('data_export', 'Data Export'),
    ]
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_trails')
    action = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=ACTION_CATEGORIES, blank=True)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)  # Changed to CharField for flexibility
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Audit Trail'
        verbose_name_plural = 'Audit Trails'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.admin_user} - {self.action}"


class AdminLog(models.Model):
    """📋 Admin activity logging system"""
    LOG_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('create', 'Create Operation'),
        ('update', 'Update Operation'),
        ('delete', 'Delete Operation'),
        ('export', 'Data Export'),
        ('system', 'System Operation'),
        ('security', 'Security Event'),
    ]
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=200)
    action_type = models.CharField(max_length=50, choices=LOG_TYPES, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Admin Log'
        verbose_name_plural = 'Admin Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
        ]
    
    def __str__(self):
        if self.admin_user:
            return f"{self.admin_user.username} - {self.action}"
        return f"System - {self.action}"


class SystemAlert(models.Model):
    """🚨 System alerts and notifications"""
    ALERT_TYPES = [
        ('system', 'System Issue'),
        ('security', 'Security Alert'),
        ('performance', 'Performance Warning'),
        ('maintenance', 'Maintenance Required'),
        ('billing', 'Billing Issue'),
        ('compliance', 'Compliance Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    affected_components = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Alert'
        verbose_name_plural = 'System Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'priority']),
            models.Index(fields=['is_resolved', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.priority})"


class APIKey(models.Model):
    """🔑 API Key management for external integrations"""
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    permissions = models.JSONField(default=list, blank=True)
    rate_limit = models.IntegerField(default=1000, help_text="Requests per hour")
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class DataExport(models.Model):
    """📤 Data export requests and management"""
    EXPORT_FORMATS = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    ]
    
    EXPORT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    export_name = models.CharField(max_length=200)
    data_model = models.CharField(max_length=100)
    filters = models.JSONField(default=dict, blank=True)
    format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='csv')
    status = models.CharField(max_length=20, choices=EXPORT_STATUS, default='pending')
    file = models.FileField(upload_to='exports/%Y/%m/%d/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Data Export'
        verbose_name_plural = 'Data Exports'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.export_name
    
    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class SystemHealthCheck(models.Model):
    """❤️ System health monitoring"""
    COMPONENT_STATUS = [
        ('operational', 'Operational'),
        ('degraded', 'Degraded Performance'),
        ('partial_outage', 'Partial Outage'),
        ('major_outage', 'Major Outage'),
    ]
    
    component = models.CharField(max_length=100)
    status = models.CharField(max_length=50, choices=COMPONENT_STATUS)
    response_time = models.FloatField(null=True, blank=True)
    last_check = models.DateTimeField(auto_now=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'System Health Check'
        verbose_name_plural = 'System Health Checks'
        ordering = ['component']
    
    def __str__(self):
        return f"{self.component} - {self.status}"


class Analytics(models.Model):
    """📊 Daily analytics snapshot"""
    date = models.DateField(default=timezone.now)
    total_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    total_vehicles = models.IntegerField(default=0)
    available_vehicles = models.IntegerField(default=0)
    total_rides = models.IntegerField(default=0)
    completed_rides = models.IntegerField(default=0)
    cancelled_rides = models.IntegerField(default=0)
    daily_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    active_rides = models.IntegerField(default=0)
    average_ride_duration = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Analytics'
        verbose_name_plural = 'Analytics'
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f"Analytics for {self.date}"


class FleetMaintenance(models.Model):
    """🔧 Fleet maintenance scheduling and tracking"""
    MAINTENANCE_STATUS = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]
    
    MAINTENANCE_TYPES = [
        ('routine', 'Routine Check'),
        ('repair', 'Repair'),
        ('battery', 'Battery Replacement'),
        ('tire', 'Tire Replacement'),
        ('brake', 'Brake Service'),
        ('software', 'Software Update'),
        ('other', 'Other'),
    ]
    
    vehicle_id = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=50, blank=True)
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES, default='routine')
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=MAINTENANCE_STATUS, default='scheduled')
    description = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assigned_staff = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fleet Maintenance'
        verbose_name_plural = 'Fleet Maintenance'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"Maintenance for {self.vehicle_id} - {self.get_maintenance_type_display()}"


class TrendingArea(models.Model):
    vehicle = models.ForeignKey('StaffWork.Vehicle', on_delete=models.CASCADE, null=True, blank=True)
    assigned_staff = models.ForeignKey('StaffWork.StaffMember', on_delete=models.SET_NULL, null=True, blank=True)
    # ... your other fields
    """📈 Trending areas based on ride demand"""
    area_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    popularity_score = models.FloatField(default=0.0)
    ride_count = models.IntegerField(default=0)
    average_demand = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Trending Area'
        verbose_name_plural = 'Trending Areas'
        ordering = ['-popularity_score']
    
    def __str__(self):
        return self.area_name


class DemandPrediction(models.Model):
    """🔮 Demand prediction analytics"""
    zone_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    prediction_time = models.DateTimeField()
    demand_score = models.FloatField(default=0.0)
    confidence_level = models.FloatField(default=0.0, help_text="Prediction confidence 0-1")
    predicted_rides = models.IntegerField(default=0)
    actual_rides = models.IntegerField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Demand Prediction'
        verbose_name_plural = 'Demand Predictions'
        ordering = ['-prediction_time']
    
    def __str__(self):
        return f"{self.zone_name} - {self.prediction_time.strftime('%Y-%m-%d %H:%M')}"


class SmartRebalancingRoute(models.Model):
    """🔄 Smart vehicle rebalancing routes"""
    ROUTE_STATUS = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    route_name = models.CharField(max_length=200)
    source_zone = models.CharField(max_length=100)
    target_zone = models.CharField(max_length=100)
    vehicles_to_move = models.IntegerField(default=0)
    estimated_duration = models.IntegerField(help_text="Duration in minutes", null=True, blank=True)
    optimized_path = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=ROUTE_STATUS, default='planned')
    assigned_staff = models.CharField(max_length=100, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Smart Rebalancing Route'
        verbose_name_plural = 'Smart Rebalancing Routes'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.route_name


class DynamicPricingRule(models.Model):
    """💰 Dynamic pricing rules and configurations"""
    PRICING_TYPES = [
        ('demand_based', 'Demand Based'),
        ('time_based', 'Time Based'),
        ('location_based', 'Location Based'),
        ('event_based', 'Event Based'),
    ]
    
    name = models.CharField(max_length=200)
    pricing_type = models.CharField(max_length=20, choices=PRICING_TYPES, default='demand_based')
    rules = models.JSONField(default=dict, blank=True)
    multiplier = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    applicable_zones = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dynamic Pricing Rule'
        verbose_name_plural = 'Dynamic Pricing Rules'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PredictiveMaintenanceAlert(models.Model):
    """⚠️ Predictive maintenance alerts"""
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    vehicle_id = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=50, blank=True)
    alert_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    message = models.TextField()
    predicted_issue = models.CharField(max_length=200)
    confidence = models.FloatField(default=0.0)
    recommended_action = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Predictive Maintenance Alert'
        verbose_name_plural = 'Predictive Maintenance Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.vehicle_id} - {self.alert_type}"


class AdminSettings(models.Model):
    """⚙️ Admin-specific settings and preferences"""
    SETTING_CATEGORIES = [
        ('dashboard', 'Dashboard'),
        ('notifications', 'Notifications'),
        ('reports', 'Reports'),
        ('security', 'Security'),
        ('ui', 'User Interface'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField(default=dict, blank=True)
    category = models.CharField(max_length=50, choices=SETTING_CATEGORIES, default='dashboard')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Admin Setting'
        verbose_name_plural = 'Admin Settings'
        ordering = ['category', 'key']
    
    def __str__(self):
        return self.key


class Report(models.Model):
    """📄 Report generation and management"""
    REPORT_TYPES = [
        ('user_activity', 'User Activity'),
        ('revenue', 'Revenue Report'),
        ('vehicle_usage', 'Vehicle Usage'),
        ('ride_analytics', 'Ride Analytics'),
        ('maintenance', 'Maintenance Report'),
        ('system_health', 'System Health'),
        ('custom', 'Custom Report'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, default='custom')
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    file = models.FileField(upload_to='reports/%Y/%m/%d/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return self.title


class DashboardWidget(models.Model):
    """📊 Dashboard widgets configuration"""
    WIDGET_TYPES = [
        ('statistic', 'Statistic'),
        ('chart', 'Chart'),
        ('table', 'Table'),
        ('progress', 'Progress'),
        ('alert', 'Alert Panel'),
    ]
    
    title = models.CharField(max_length=200)
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPES, default='statistic')
    data_source = models.CharField(max_length=100, blank=True)
    position = models.IntegerField(default=0)
    size = models.CharField(max_length=20, default='medium')  # small, medium, large
    configuration = models.JSONField(default=dict, blank=True)
    is_visible = models.BooleanField(default=True)
    refresh_interval = models.IntegerField(default=300, help_text="Refresh interval in seconds")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dashboard Widget'
        verbose_name_plural = 'Dashboard Widgets'
        ordering = ['position']
    
    def __str__(self):
        return self.title


class GPSMonitoring(models.Model):
    """📍 Real-time GPS monitoring data"""
    VEHICLE_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
        ('low_battery', 'Low Battery'),
        ('offline', 'Offline'),
    ]
    
    vehicle_id = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    speed = models.FloatField(null=True, blank=True)
    battery_level = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=VEHICLE_STATUS, default='active')
    heading = models.FloatField(null=True, blank=True, help_text="Direction in degrees")
    
    class Meta:
        verbose_name = "GPS Monitoring"
        verbose_name_plural = "GPS Monitoring"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vehicle_id', 'timestamp']),
            models.Index(fields=['status', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.vehicle_id} at ({self.latitude}, {self.longitude})"


class RevenueAnalytics(models.Model):
    """💰 Revenue analytics and financial reporting"""
    date = models.DateField()
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    ride_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    subscription_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    other_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    trip_count = models.IntegerField()
    average_fare = models.DecimalField(max_digits=8, decimal_places=2)
    revenue_per_user = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Revenue Analytic"
        verbose_name_plural = "Revenue Analytics"
        ordering = ['-date']
        unique_together = ['date']

    def __str__(self):
        return f"Revenue for {self.date}: ${self.total_revenue}"


class DemandAnalytics(models.Model):
    """📈 Demand analytics for strategic planning"""
    DEMAND_LEVELS = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Medium'),
        (4, 'High'),
        (5, 'Very High'),
    ]
    
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    timestamp = models.DateTimeField()
    demand_level = models.IntegerField(choices=DEMAND_LEVELS)
    ride_requests = models.IntegerField(default=0)
    available_vehicles = models.IntegerField(default=0)
    fulfillment_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Demand Analytic"
        verbose_name_plural = "Demand Analytics"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['location', 'timestamp']),
        ]

    def __str__(self):
        return f"Demand at {self.location} - {self.timestamp}"
    
