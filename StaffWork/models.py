# StaffWork/models.py - CLEANED VERSION
import uuid
import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from Users.models import Vehicle

# Try to import CustomUser from users app, fallback if not available
try:
    from Users.models import CustomUser
except ImportError:
    class CustomUser(AbstractUser):
        user_type = models.CharField(max_length=20, choices=[
            ('admin', 'Admin'),
            ('staff', 'Staff'),
            ('user', 'User')
        ], default='user')
        phone_number = models.CharField(max_length=15, blank=True)
        
        class Meta:
            swappable = 'AUTH_USER_MODEL'

class StaffMember(models.Model):
    STAFF_ROLES = [
        ('field_agent', '🚗 Field Agent'),
        ('maintenance_tech', '🔧 Maintenance Technician'), 
        ('rebalancer', '🔄 Rebalancing Staff'),
        ('support_agent', '🎯 Support Agent'),
        ('inspector', '🔍 Vehicle Inspector'),
        ('emergency_responder', '🚨 Emergency Responder'),
        ('supervisor', 'Supervisor'),
        ('manager', 'Manager'),
        ('admin', 'Admin')
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('on_break', 'On Break'),
        ('off_duty', 'Off Duty')
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=30, choices=STAFF_ROLES, default='field_agent')
    phone = models.CharField(max_length=15, blank=True)
    work_zone = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_on_duty = models.BooleanField(default=False)
    current_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='off_duty')
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Smart Rebalancing Assistant fields
    rebalancing_efficiency = models.FloatField(default=0.0)
    vehicles_rebalanced_today = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'staff_members'
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

class Task(models.Model):
    TASK_TYPES = [
        ('rebalancing', '🔄 Vehicle Rebalancing'),
        ('maintenance', '🔧 Maintenance'),
        ('battery_swap', '🔋 Battery Replacement'),
        ('emergency', '🚨 Emergency Response'),
        ('inspection', '🔍 Vehicle Inspection'),
        ('cleaning', '🧹 Cleaning'),
        ('user_support', '🎯 User Support'),
        ('repair', 'Repair'),
        ('other', 'Other')
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]

    TASK_STATUS = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    task_id = models.CharField(max_length=20, unique=True, primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')

    # 🛞 Vehicle association (CORRECT)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks'
    )

    # Smart Rebalancing Assistant
    is_smart_rebalancing = models.BooleanField(default=False)
    optimized_route = models.JSONField(null=True, blank=True)
    predicted_demand_zone = models.CharField(max_length=100, blank=True)

    # Assignment info
    assigned_to = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='assigned_tasks')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='user_created_tasks')
    assigned_at = models.DateTimeField(null=True, blank=True)

    # Location info
    location_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Timing info
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", null=True, blank=True)
    actual_duration = models.IntegerField(help_text="Actual duration in minutes", null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Additional data
    task_data = models.JSONField(null=True, blank=True, help_text="Additional task data in JSON format")

    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='deleted_tasks')

    class Meta:
        db_table = 'staffwork_tasks'
        verbose_name = 'Maintenance Task'
        verbose_name_plural = 'Maintenance Tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.task_id} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.task_id:
            self.task_id = f"TASK{timezone.now().strftime('%Y%m%d')}{Task.objects.count() + 1:04d}"

        if self.status == 'assigned' and not self.assigned_at:
            self.assigned_at = timezone.now()

        super().save(*args, **kwargs)


def task_attachment_path(instance, filename):
    return f'tasks/{instance.task.task_id}/attachments/{filename}'


class TaskAttachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=task_attachment_path)
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'task_attachments'
        verbose_name = 'Task Attachment'
        verbose_name_plural = 'Task Attachments'

    def __str__(self):
        return f"Attachment for {self.task.task_id} - {self.filename}"

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        if not self.filename and self.file:
            self.filename = self.file.name
        super().save(*args, **kwargs)

class EmergencyAlert(models.Model):
    EMERGENCY_TYPES = [
        ('accident', '🚑 Accident'),
        ('breakdown', '🚗 Vehicle Breakdown'),
        ('theft', '🚨 Theft Report'),
        ('user_injury', '🤕 User Injury'),
        ('vandalism', '⚡ Vandalism'),
        ('other', '❓ Other')
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled')
    ]
    
    alert_id = models.CharField(max_length=20, unique=True, primary_key=True)
    emergency_type = models.CharField(max_length=20, choices=EMERGENCY_TYPES)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    
    # Location info
    location_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # People involved
    reported_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='reported_emergencies')
    assigned_staff = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_emergencies')
    
    # Timestamps
    reported_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Dynamic Priority Alerts
    is_high_priority = models.BooleanField(default=False)
    response_time = models.IntegerField(null=True, blank=True)
    
    # Resolution info
    response_notes = models.TextField(blank=True)
    resolution_type = models.CharField(max_length=50, blank=True)
    
    # Additional data
    emergency_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'staff_emergency_alerts'
        verbose_name = 'Emergency Alert'
        verbose_name_plural = 'Emergency Alerts'
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['reported_at']),
            models.Index(fields=['is_high_priority', 'reported_at']),
        ]

    def __str__(self):
        return f"{self.alert_id} - {self.emergency_type}"

    def save(self, *args, **kwargs):
        if not self.alert_id:
            self.alert_id = f"EMG{timezone.now().strftime('%Y%m%d')}{EmergencyAlert.objects.count() + 1:04d}"
        
        # Auto-set high priority for critical emergencies
        if self.severity in ['high', 'critical']:
            self.is_high_priority = True
            
        super().save(*args, **kwargs)



class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('scooter', 'E-Scooter'),
        ('bike', 'E-Bike'),
        
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('low_battery', 'Low Battery'),
        ('offline', 'Offline'),
    ]
    
    vehicle_id = models.CharField(max_length=20, unique=True, primary_key=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # 📍 Location Info
    current_zone = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # 🔋 Battery Info
    battery_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100
    )

    # 🧰 Maintenance Info
    last_maintenance = models.DateTimeField(null=True, blank=True)
    maintenance_notes = models.TextField(blank=True)
    total_distance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # 🖼️ Optional Photo (for staff visual verification)
    photo = models.ImageField(upload_to='vehicles/staff_photos/', blank=True, null=True)

    # ⚙️ System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        indexes = [
            models.Index(fields=['status', 'vehicle_type']),
            models.Index(fields=['current_zone']),
        ]

    def __str__(self):
        return f"{self.vehicle_id} - {self.vehicle_type}"

    def save(self, *args, **kwargs):
        """Auto-mark low_battery or maintenance based on conditions."""
        if self.battery_level < 20 and self.status == 'available':
            self.status = 'low_battery'
        if self.status == 'in_use':
            self.last_location_update = timezone.now()
        super().save(*args, **kwargs)

class DemandZone(models.Model):
    DEMAND_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High')
    ]
    
    zone_name = models.CharField(max_length=100, unique=True)
    demand_level = models.CharField(max_length=20, choices=DEMAND_LEVELS, default='medium')
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius = models.DecimalField(max_digits=8, decimal_places=2, help_text="Radius in meters", default=500)
    
    # Vehicle counts
    current_vehicle_count = models.IntegerField(default=0)
    optimal_vehicle_count = models.IntegerField(default=10)
    
    # Demand prediction
    predicted_demand = models.JSONField(null=True, blank=True)
    rebalancing_needed = models.BooleanField(default=False)
    
    # Analytics
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'demand_zones'
        verbose_name = 'Demand Zone'
        verbose_name_plural = 'Demand Zones'
        indexes = [
            models.Index(fields=['demand_level']),
            models.Index(fields=['rebalancing_needed']),
        ]

    def __str__(self):
        return f"{self.zone_name} - {self.demand_level}"

class RebalancingTask(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    zone = models.ForeignKey(DemandZone, on_delete=models.CASCADE, related_name='rebalancing_tasks')
    assigned_staff = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True, related_name='rebalancing_tasks')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Vehicle movement
    vehicles_to_move = models.IntegerField(default=0)
    vehicles_moved = models.IntegerField(default=0)
    source_zone = models.CharField(max_length=100, blank=True)
    target_zone = models.CharField(max_length=100)
    
    # Timing
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    completion_notes = models.TextField(blank=True)
    optimized_route = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rebalancing_tasks'
        verbose_name = 'Rebalancing Task'
        verbose_name_plural = 'Rebalancing Tasks'

    def __str__(self):
        return f"Rebalancing to {self.target_zone} - {self.status}"

class StaffPerformance(models.Model):
    staff_member = models.OneToOneField(StaffMember, on_delete=models.CASCADE, related_name='performance')
    
    # Task metrics
    total_tasks_assigned = models.IntegerField(default=0)
    tasks_completed = models.IntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Time metrics
    average_response_time = models.IntegerField(help_text="Average response time in minutes", default=0)
    average_task_duration = models.IntegerField(help_text="Average task duration in minutes", default=0)
    
    # Quality metrics
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    customer_rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    
    # Emergency metrics
    emergencies_handled = models.IntegerField(default=0)
    emergency_response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Period
    period_start = models.DateField()
    period_end = models.DateField()
    
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_performance'
        verbose_name = 'Staff Performance'
        verbose_name_plural = 'Staff Performances'
        indexes = [
            models.Index(fields=['period_start', 'period_end']),
        ]

    def __str__(self):
        return f"Performance - {self.staff_member.employee_id}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_updated', 'Task Updated'),
        ('task_completed', 'Task Completed'),
        ('emergency_alert', 'Emergency Alert'),
        ('system_alert', 'System Alert'),
        ('maintenance_reminder', 'Maintenance Reminder'),
        ('rebalancing_alert', 'Rebalancing Alert')
    ]
    
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related entities
    related_task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    related_emergency = models.ForeignKey(EmergencyAlert, on_delete=models.CASCADE, null=True, blank=True)
    related_vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'staff_notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['staff_member', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.staff_member.employee_id}"

class DemandHeatmap(models.Model):
    zone_name = models.CharField(max_length=200)
    demand_score = models.FloatField(default=0.0)
    vehicle_count = models.IntegerField(default=0)
    recommended_vehicles = models.IntegerField(default=0)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    prediction_confidence = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'demand_heatmaps'
        verbose_name = 'Demand Heatmap'
        verbose_name_plural = 'Demand Heatmaps'
        ordering = ['-demand_score']

    def __str__(self):
        return f"{self.zone_name} - Score: {self.demand_score}"

class StaffWorkAnalytics(models.Model):
    staff_member = models.ForeignKey(StaffMember, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    tasks_completed = models.IntegerField(default=0)
    emergencies_handled = models.IntegerField(default=0)
    avg_completion_time = models.FloatField(default=0.0)
    on_time_completion_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Staff Work Analytics"
        verbose_name_plural = "Staff Work Analytics"
        db_table = 'staff_work_analytics'
        unique_together = ['staff_member', 'date']
    
    def __str__(self):
        return f"{self.staff_member.user.get_full_name()} - {self.date}"

class DemandPrediction(models.Model):
    prediction_id = models.CharField(max_length=20, unique=True, primary_key=True)
    zone_name = models.CharField(max_length=200)
    prediction_type = models.CharField(max_length=50)
    prediction_time = models.DateTimeField()
    demand_score = models.FloatField(default=0.0)
    confidence_level = models.FloatField(default=0.0)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.FloatField(default=1.0)
    predicted_vehicles_needed = models.IntegerField(default=0)
    weather_impact = models.FloatField(default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'demand_predictions'

    def __str__(self):
        return f"DemandPrediction-{self.prediction_id}"

    def save(self, *args, **kwargs):
        if not self.prediction_id:
            self.prediction_id = f"PRED{timezone.now().strftime('%Y%m%d')}{DemandPrediction.objects.count() + 1:04d}"
        super().save(*args, **kwargs)

class DynamicPricingRule(models.Model):
    rule_id = models.CharField(max_length=20, unique=True, primary_key=True)
    rule_name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=50)
    zone_name = models.CharField(max_length=200)
    base_price_multiplier = models.FloatField(default=1.0)
    min_price = models.DecimalField(max_digits=8, decimal_places=2, default=10.0)
    max_price = models.DecimalField(max_digits=8, decimal_places=2, default=100.0)
    activation_threshold = models.FloatField(default=0.7)
    is_active = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    days_of_week = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dynamic_pricing_rules'

    def __str__(self):
        return f"PricingRule-{self.rule_id}"

    def save(self, *args, **kwargs):
        if not self.rule_id:
            self.rule_id = f"RULE{timezone.now().strftime('%Y%m%d')}{DynamicPricingRule.objects.count() + 1:04d}"
        super().save(*args, **kwargs)

class PredictiveMaintenanceAlert(models.Model):
    alert_id = models.CharField(max_length=20, unique=True, primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    description = models.TextField()
    predicted_failure_date = models.DateTimeField()
    confidence_score = models.FloatField(default=0.0)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(StaffMember, on_delete=models.SET_NULL, null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'predictive_maintenance_alerts'

    def __str__(self):
        return f"MaintenanceAlert-{self.alert_id}"

    def save(self, *args, **kwargs):
        if not self.alert_id:
            self.alert_id = f"MALERT{timezone.now().strftime('%Y%m%d')}{PredictiveMaintenanceAlert.objects.count() + 1:04d}"
        super().save(*args, **kwargs)

class StaffDashboard(models.Model):
    staff_member = models.OneToOneField(StaffMember, on_delete=models.CASCADE)
    
    # Today's metrics
    tasks_assigned_today = models.IntegerField(default=0)
    tasks_completed_today = models.IntegerField(default=0)
    emergencies_handled_today = models.IntegerField(default=0)
    vehicles_rebalanced_today = models.IntegerField(default=0)
    
    # Performance metrics
    completion_rate = models.FloatField(default=0.0)
    average_response_time = models.FloatField(default=0.0)
    efficiency_score = models.FloatField(default=0.0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'staff_dashboard'
    
    def __str__(self):
        return f"Dashboard - {self.staff_member.employee_id}"

# Aliases at the end
Staff = StaffMember
StaffTask = Task


