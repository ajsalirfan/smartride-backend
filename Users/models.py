from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from decimal import Decimal
import uuid
import logging
from django.db import models
from django.conf import settings
logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """Custom manager that ensures proper user_type setup."""
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Ensure all superusers automatically have user_type='admin'."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')

        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(username, email, password, **extra_fields)



class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )

    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    # Basic info
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # Verification system (NO SELFIE REQUIRED)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_requested_at = models.DateTimeField(null=True, blank=True)
    verification_approved_at = models.DateTimeField(null=True, blank=True)
    verification_rejected_at = models.DateTimeField(null=True, blank=True)
    verification_rejection_reason = models.TextField(blank=True)

    # Documents (Only Driving License + ID Proof - NO SELFIE)
    driving_license_front = models.FileField(upload_to='documents/license/front/', null=True, blank=True)
    driving_license_back = models.FileField(upload_to='documents/license/back/', null=True, blank=True)
    id_proof = models.FileField(upload_to='documents/id_proof/', null=True, blank=True)
    documents_uploaded = models.BooleanField(default=False)

    # Preferences
    preferred_vehicle_type = models.CharField(
        max_length=20,
        choices=[('escooter', 'E-Scooter'), ('ebike', 'E-Bike')],
        default='escooter'
    )
    preferred_riding_times = models.JSONField(default=dict, blank=True)
    favorite_areas = models.JSONField(default=list, blank=True)

    # Safety features
    emergency_contacts_added = models.BooleanField(default=False)

    # Statistics
    total_rides_count = models.PositiveIntegerField(default=0)
    total_distance_covered = models.FloatField(default=0.0)
    carbon_saved_total = models.FloatField(default=0.0)
    loyalty_points = models.PositiveIntegerField(default=0)
    membership_tier = models.CharField(max_length=20, default='bronze')

    # Map preferences
    map_style = models.CharField(
        max_length=20,
        default='standard',
        choices=[
            ('standard', 'Standard'),
            ('satellite', 'Satellite'),
            ('dark', 'Dark Mode')
        ]
    )
    show_trending_areas = models.BooleanField(default=True)
    show_favorite_locations = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ Attach the custom manager
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        """
        Automatically syncs user_type with Django permission flags.
        Ensures correct roles: Admin / Staff / Customer.
        """
        if self.is_superuser:
            self.user_type = 'admin'
            self.is_staff = True
        elif self.is_staff and self.user_type not in ['admin', 'staff']:
            self.user_type = 'staff'
        elif not self.is_staff and not self.is_superuser:
            self.user_type = 'customer'
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.user_type})"

    def can_book_ride(self):
        """Check if user can book rides (approved verification)"""
        return self.is_verified and self.verification_status == 'approved'

    def get_verification_documents_status(self):
        """Check if all required documents are uploaded"""
        return bool(self.driving_license_front and self.driving_license_back and self.id_proof)

    def request_verification(self):
        """Mark user as requesting verification"""
        if self.get_verification_documents_status():
            self.verification_status = 'pending'
            self.verification_requested_at = timezone.now()
            self.save()
            return True
        return False

class Vehicle(models.Model):
    VEHICLE_TYPES = (
        ('escooter', 'E-Scooter'),
        ('ebike', 'E-Bike'),
    )
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('booked', 'Booked'),
        ('maintenance', 'Under Maintenance'),
        ('low_battery', 'Low Battery'),
        ('offline', 'Offline'),
    )
    
    BATTERY_STATUS = (
        ('full', 'Full (81-100%)'),
        ('high', 'High (61-80%)'),
        ('medium', 'Medium (41-60%)'),
        ('low', 'Low (21-40%)'),
        ('critical', 'Critical (0-20%)'),
    )
    
    vehicle_id = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES, default='escooter')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Technical specs
    model_name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    battery_level = models.PositiveIntegerField(default=100)
    battery_status = models.CharField(max_length=10, choices=BATTERY_STATUS, default='full')
    max_speed = models.PositiveIntegerField(help_text="km/h")
    max_range = models.PositiveIntegerField(help_text="km")
    
    # 📸 Vehicle Photo
    photo = models.ImageField(upload_to='vehicles/photos/', blank=True, null=True)
    
    # Location
    current_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    # Pricing
    price_per_minute = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    
    # Stats
    total_rides = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Cluster info for map optimization
    cluster_id = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"{self.vehicle_id} - {self.vehicle_type}"

    def save(self, *args, **kwargs):
        """Auto-update battery status and active timestamp."""
        if self.battery_level >= 81:
            self.battery_status = 'full'
        elif self.battery_level >= 61:
            self.battery_status = 'high'
        elif self.battery_level >= 41:
            self.battery_status = 'medium'
        elif self.battery_level >= 21:
            self.battery_status = 'low'
        else:
            self.battery_status = 'critical'
        
        if self.status == 'in_use':
            self.last_active = timezone.now()
            
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        """Check if vehicle is available for new ride."""
        return self.status == 'available' and self.battery_level > 10

    def get_nearby_vehicles(self, latitude, longitude, radius_km=2):
        """Get nearby available vehicles within the specified radius (simple calculation)."""
        return Vehicle.objects.filter(
            status='available',
            battery_level__gte=20
        ).extra(
            where=["""
                (6371 * acos(cos(radians(%s)) * cos(radians(current_location_lat)) 
                * cos(radians(current_location_lng) - radians(%s)) 
                + sin(radians(%s)) * sin(radians(current_location_lat)))) < %s
            """],
            params=[latitude, longitude, latitude, radius_km]
        )


class Ride(models.Model):
    RIDE_STATUS = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    )

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    ride_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rides')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='rides')
    status = models.CharField(max_length=20, choices=RIDE_STATUS, default='active')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)

    # 🌍 Locations
    start_location_lat = models.DecimalField(max_digits=9, decimal_places=6)
    start_location_lng = models.DecimalField(max_digits=9, decimal_places=6)
    end_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    end_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    start_location_name = models.CharField(max_length=200)
    end_location_name = models.CharField(max_length=200, blank=True)

    # 🕒 Timing
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    # 📊 Metrics
    distance = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    carbon_saved = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    # 💳 Payment
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=50, blank=True)

    # ⭐ Rating / Feedback
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    # 🕓 Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rides'
        verbose_name = 'Ride'
        verbose_name_plural = 'Rides'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ride_id} - {self.user.username}"

    def save(self, *args, **kwargs):
        """Generate unique Ride ID if missing."""
        if not self.ride_id:
            self.ride_id = f"RIDE{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    # ✅ Simplified start (no QR)
    def start_ride(self):
        """Start the ride and mark vehicle as in use."""
        self.status = 'active'
        self.start_time = timezone.now()
        self.vehicle.status = 'in_use'
        self.vehicle.save()
        self.save()
        return True

    # ✅ Complete Ride
    def complete_ride(self, end_lat, end_lng, end_location, distance):
        """Complete the ride and calculate cost dynamically."""
        self.end_location_lat = end_lat
        self.end_location_lng = end_lng
        self.end_location_name = end_location
        self.distance = distance
        self.end_time = timezone.now()

        # Duration and cost calculations
        duration = self.end_time - self.start_time
        self.duration = duration
        minutes = duration.total_seconds() / 60
        self.cost = 10 + (minutes * 2)
        self.carbon_saved = distance * 0.2
        self.status = 'completed'
        self.payment_status = 'pending'

        # Update vehicle status
        self.vehicle.status = 'available'
        self.vehicle.current_location_lat = end_lat
        self.vehicle.current_location_lng = end_lng
        self.vehicle.battery_level = max(0, self.vehicle.battery_level - 10)
        self.vehicle.save()

        # Update user stats
        self.user.total_rides_count += 1
        self.user.total_distance_covered += float(distance)
        self.user.carbon_saved_total += float(self.carbon_saved)
        self.user.save()

        self.save()
        return self.cost

    # ✅ Cancel Ride
    def cancel_ride(self):
        """Cancel the ride and free the vehicle."""
        self.status = 'cancelled'
        self.end_time = timezone.now()
        self.vehicle.status = 'available'
        self.vehicle.save()
        self.save()

# =======================================================

class RideBooking(models.Model):
    BOOKING_STATUS = (
        ('pending', 'Pending'),     # booked, waiting to start
        ('active', 'Active'),       # ride started
        ('completed', 'Completed'), # ride finished
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    booking_id = models.CharField(max_length=30, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ride_bookings')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='ride_bookings')

    status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')

    # 💰 money
    advance_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('300.00'))
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))

    # 🔗 link to actual Ride
    ride = models.OneToOneField(
        'Ride',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='booking'
    )

    # ⏱ timing
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ride_bookings'
        verbose_name = 'Ride Booking'
        verbose_name_plural = 'Ride Bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking_id} - {self.user.username} - {self.status}"

    @property
    def is_valid(self):
        """True if booking still usable for starting ride."""
        return self.status == 'pending' and self.expires_at > timezone.now()


# ========================================================

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('upi', 'UPI'),
        ('google_pay', 'Google Pay'),
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('wallet', 'Wallet'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    transaction_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # UPI/Google Pay details
    upi_id = models.CharField(max_length=50, blank=True)
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    payment_initiated_at = models.DateTimeField(auto_now_add=True)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"{self.transaction_id} - {self.user.username} - ₹{self.amount}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def process_upi_payment(self, upi_id):
        """Process UPI payment (simulated)"""
        self.payment_method = 'upi'
        self.upi_id = upi_id
        self.status = 'completed'
        self.payment_completed_at = timezone.now()
        
        # Update ride payment status
        self.ride.payment_status = 'paid'
        self.ride.payment_method = 'upi'
        self.ride.save()
        self.save()
        return True

# ======================================================
# EmergencyAlert Model — SmartRide Integrated Edition
# ======================================================
class EmergencyAlert(models.Model):

    EMERGENCY_TYPES = (
        ('accident', 'Accident / Crash'),
        ('harassment', 'Harassment / Safety Threat'),
        ('vehicle_breakdown', 'Vehicle Breakdown'),
        ('medical', 'Medical Emergency'),
        ('theft', 'Theft / Robbery'),
        ('other', 'Other Emergency'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='emergency_alerts')
    ride = models.ForeignKey(Ride, on_delete=models.SET_NULL, null=True, blank=True, related_name='emergency_alerts')

    alert_type = models.CharField(
        max_length=20,
        choices=EMERGENCY_TYPES,
        default='accident'   # ✔ safest
    )

    message = models.TextField(blank=True)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6)
    location_name = models.CharField(max_length=200, blank=True)

    admin_response = models.TextField(blank=True, null=True)
    response_sent_at = models.DateTimeField(null=True, blank=True)

    contacts_notified = models.JSONField(default=list, blank=True)

    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        'CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='user_resolved_alerts'
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class EmergencyContact(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    relationship = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'emergency_contacts'
        verbose_name = 'Emergency Contact'
        verbose_name_plural = 'Emergency Contacts'

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class SupportTicket(models.Model):
    TICKET_TYPES = (
        ('technical', 'Technical Issue'),
        ('billing', 'Billing Issue'),
        ('safety', 'Safety Concern'),
        ('general', 'General Inquiry'),
        ('emergency', 'Emergency Support'),
        ('verification', 'Verification Help'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='support_tickets')
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, default='open', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ])
    
    # Staff assignment
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='assigned_tickets', limit_choices_to={'user_type': 'staff'})
    
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'support_tickets'
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'

    def __str__(self):
        return f"{self.ticket_type} - {self.user.username} - {self.status}"


UserModel = settings.AUTH_USER_MODEL

class NotificationQuerySet(models.QuerySet):
    def unread(self):
        return self.filter(is_read=False)

    def read(self):
        return self.filter(is_read=True)

class NotificationManager(models.Manager):
    def get_queryset(self):
        return NotificationQuerySet(self.model, using=self._db)

    def unread_for_user(self, user):
        return self.get_queryset().filter(user=user, is_read=False)

    def create_for_user(self, user, notification_type, title, message, data=None, is_sent=True):
        return self.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            is_sent=is_sent
        )

from django.db import models
from django.utils import timezone
from Users.models import UserModel


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('ride', 'Ride'),
        ('payment', 'Payment'),
        ('promotion', 'Promotion'),
        ('safety', 'Safety'),
        ('system', 'System'),
        ('verification', 'Verification'),
        ('task_assigned', 'Task Assigned'),
        ('task_updated', 'Task Updated'),
        ('task_completed', 'Task Completed'),
        ('emergency_alert', 'Emergency Alert'),
        ('rebalancing_alert', 'Rebalancing Alert'),
    )

    # Notification can target EITHER user or staff
    user = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_notifications'
    )

    staff_member = models.ForeignKey(
        'StaffWork.StaffMember',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='staff_notifications'
    )

    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)

    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        if self.staff_member:
            return f"Staff {self.staff_member.employee_id} - {self.title}"
        if self.user:
            return f"User {self.user.username} - {self.title}"
        return self.title

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def mark_as_unread(self):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save()

    @classmethod
    def send_to_user(cls, user, notification_type, title, message, data=None):
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            is_sent=True
        )

    @classmethod
    def send_to_staff(cls, staff_member, notification_type, title, message, data=None):
        return cls.objects.create(
            staff_member=staff_member,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            is_sent=True
        )

class TrendingArea(models.Model):
    """Real-time trending locations for recommendations"""
    area_name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    popularity_score = models.FloatField(default=0.0)
    ride_count_24h = models.IntegerField(default=0)
    vehicle_availability = models.IntegerField(default=0)
    trend_direction = models.CharField(max_length=10, choices=[('up', 'Rising'), ('down', 'Falling'), ('stable', 'Stable')])
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trending_areas'
        verbose_name = 'Trending Area'
        verbose_name_plural = 'Trending Areas'

    def __str__(self):
        return f"{self.area_name} - Score: {self.popularity_score}"


class RideRecommendation(models.Model):
    RECOMMENDATION_TYPES = (
        ('nearby', 'Nearby Vehicles'),
        ('personalized', 'Personalized'),
        ('trending', 'Trending Areas'),
        ('favorite', 'Based on Favorites'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    # Recommendation data
    recommended_vehicles = models.ManyToManyField(Vehicle, blank=True)
    recommended_areas = models.ManyToManyField(TrendingArea, blank=True)
    
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ride_recommendations'
        verbose_name = 'Ride Recommendation'
        verbose_name_plural = 'Ride Recommendations'

    def __str__(self):
        return f"{self.user.username} - {self.recommendation_type} - {self.title}"


class UserFavorite(models.Model):
    FAVORITE_TYPES = (
        ('vehicle', 'Vehicle'),
        ('location', 'Location'),
        ('route', 'Route'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorites')
    favorite_type = models.CharField(max_length=20, choices=FAVORITE_TYPES)
    name = models.CharField(max_length=200)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_favorites'
        verbose_name = 'User Favorite'
        verbose_name_plural = 'User Favorites'
        unique_together = ['user', 'favorite_type', 'name']

    def __str__(self):
        return f"{self.user.username} - {self.favorite_type} - {self.name}"


class StaffTask(models.Model):
    TASK_TYPES = (
        ('rebalancing', 'Vehicle Rebalancing'),
        ('maintenance', 'Vehicle Maintenance'),
        ('support', 'User Support'),
        ('emergency', 'Emergency Response'),
        ('inspection', 'Vehicle Inspection'),
    )
    
    PRIORITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    TASK_STATUS = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    task_id = models.CharField(max_length=20, unique=True)
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS, default='medium')
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')
    
    # Assignment
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='assigned_tasks', limit_choices_to={'user_type': 'staff'})
    assigned_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, 
                                   related_name='created_tasks', limit_choices_to={'user_type': 'admin'})
    
    # Location
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=200, blank=True)
    
    # Vehicles involved
    vehicles = models.ManyToManyField(Vehicle, blank=True)
    
    # Timing
    assigned_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    
    # Results
    completion_notes = models.TextField(blank=True)
    time_taken = models.DurationField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff_tasks'
        verbose_name = 'Staff Task'
        verbose_name_plural = 'Staff Tasks'

    def __str__(self):
        return f"{self.task_id} - {self.task_type} - {self.status}"

    def save(self, *args, **kwargs):
        if not self.task_id:
            self.task_id = f"TASK{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def assign_to_staff(self, staff_user):
        """Assign task to staff member"""
        if staff_user.user_type == 'staff':
            self.assigned_to = staff_user
            self.status = 'assigned'
            self.assigned_at = timezone.now()
            self.save()
            return True
        return False

    def mark_completed(self, notes):
        """Mark task as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.completion_notes = notes
        
        if self.started_at:
            self.time_taken = self.completed_at - self.started_at
        
        self.save()


# ======================================================
# Complaint Model — SmartRide Integrated Edition
# ======================================================

class Complaint(models.Model):
    COMPLAINT_TYPES = (
        ('vehicle_issue', 'Vehicle Issue'),
        ('safety_concern', 'Safety Concern'),
        ('payment_issue', 'Payment Issue'),
        ('app_issue', 'App Issue'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='complaints'
    )

    complaint_type = models.CharField(max_length=20, choices=COMPLAINT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # 📸 Optional Photo Evidence
    photo = models.ImageField(
        upload_to='complaints/photos/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )

    # 👇 Admin reply after review
    admin_reply = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'complaints'
        verbose_name = "Complaint"
        verbose_name_plural = "Complaints"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def mark_as_replied(self, reply_text):
        """Helper for admin replying to the complaint"""
        from django.utils import timezone
        self.admin_reply = reply_text
        self.replied_at = timezone.now()
        self.status = 'resolved'
        self.save()

class Wallet(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='wallet',
        unique=True       # ✔ correct place
    )
    balance = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wallets'
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_user_wallet')  # ✔ DB-level unique
        ]

class VehicleLocationHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='location_history')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    battery_level = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicle_location_history'

# ========================
# 📄 DOCUMENT & VERIFICATION MODELS
# ========================

class DocumentUpload(models.Model):
    # ✅ Explicitly link to CustomUser model
    user = models.ForeignKey(
        'Users.CustomUser',
        on_delete=models.CASCADE,
        related_name='document_uploads'
    )

    # ✅ Separate file fields for Aadhaar and Driving License
    aadhaar_card = models.FileField(
        upload_to='user_documents/aadhaar_cards/',
        null=True,
        blank=True,
        verbose_name='Aadhaar Card'
    )
    driving_license = models.FileField(
        upload_to='user_documents/driving_licenses/',
        null=True,
        blank=True,
        verbose_name='Driving License'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    verified_by = models.ForeignKey(
        'Users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'document_uploads'
        app_label = 'Admin'
        verbose_name = '📄 Document Upload'
        verbose_name_plural = '📄 Document Uploads'

    def __str__(self):
        return f"{self.user.username} - Documents"

class EmailOTP(models.Model):
    OTP_PURPOSES = (
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('phone_verification', 'Phone Verification'),
    )
    
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=OTP_PURPOSES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'email_otps'
    
    def __str__(self):
        return f"{self.email} - {self.purpose} - {self.otp}"
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class PasswordResetToken(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
    
    def __str__(self):
        return f"{self.user.username} - {self.token}"
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at


class VerificationHistory(models.Model):
    VERIFICATION_ACTIONS = (
        ('documents_uploaded', 'Documents Uploaded'),
        ('verification_approved', 'Verification Approved'),
        ('verification_rejected', 'Verification Rejected'),
        ('documents_updated', 'Documents Updated'),
    )
    
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='verification_history')
    action = models.CharField(max_length=50, choices=VERIFICATION_ACTIONS)
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='processed_verifications')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'verification_history'
        verbose_name = 'Verification History'
        verbose_name_plural = 'Verification Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.status}"

class LoginHistory(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='login_history')
    login_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)  # Add this line
    success = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'login_history'
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
    

# ======================================================
# Feedback Model — SmartRide Integrated Edition
# ======================================================
class Feedback(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='feedbacks')
    ride = models.ForeignKey('Ride', on_delete=models.CASCADE, related_name='feedbacks', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=0)
    comment = models.TextField(blank=True)
    admin_reply = models.TextField(blank=True, null=True)  # 👈 Admin’s response to user
    replied_at = models.DateTimeField(null=True, blank=True)  # 👈 Timestamp when replied
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedback'
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.rating}★"

    def mark_as_replied(self, reply_text):
        """Helper method for admin replies"""
        from django.utils import timezone
        self.admin_reply = reply_text
        self.replied_at = timezone.now()
        self.save()
