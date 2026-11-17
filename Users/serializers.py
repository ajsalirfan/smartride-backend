# users/serializers.py - COMPLETE ORGANIZED VERSION
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
import re

from .models import (
    CustomUser, DocumentUpload, Wallet, LoginHistory, EmailOTP, Vehicle, Ride, 
    Payment, EmergencyContact, EmergencyAlert, Complaint, 
    UserFavorite, RideRecommendation, Notification, 
    VerificationHistory, VehicleLocationHistory
)


# ==================== AUTHENTICATION SERIALIZERS ====================

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password', 'placeholder': 'Enter your password'},
        help_text="Minimum 8 characters with letters and numbers",
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password', 'placeholder': 'Confirm your password'},
        help_text="Re-enter your password"
    )
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'your@email.com'},
        help_text="We'll send verification email to this address"
    )
    username = serializers.CharField(
        min_length=3,
        max_length=30,
        style={'input_type': 'text', 'placeholder': 'choose_username'},
        help_text="3-30 characters. Letters, numbers, and @/./+/-/_ only",
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Username can only contain letters, numbers and @/./+/-/_'
            )
        ]
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken. Choose another.")
        return value
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered. Use a different email.")
        return value.lower()
    
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords don't match."})
        
        password = attrs.get('password')
        if password and len(password) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = CustomUser.objects.create_user(**validated_data)
        Wallet.objects.create(user=user)
        
        LoginHistory.objects.create(
            user=user,
            ip_address=self.context.get('request').META.get('REMOTE_ADDR'),
            user_agent=self.context.get('request').META.get('HTTP_USER_AGENT', ''),
            success=True,
            location="Registration"
        )
        
        return user


class SimpleEmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'your@email.com'},
        help_text="Enter your registered email address",
        error_messages={
            'required': 'Email address is required',
            'invalid': 'Please enter a valid email address'
        }
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password', 'placeholder': 'Enter your password'},
        help_text="Enter your account password",
        error_messages={
            'required': 'Password is required'
        }
    )
    remember_me = serializers.BooleanField(
        required=False,
        style={'input_type': 'checkbox'},
        help_text="Keep me logged in for 30 days",
        default=False
    )

    def validate_email(self, value):
        if not value.strip():
            raise serializers.ValidationError("Email address is required")
        
        email = value.lower().strip()
        if not CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("No account found with this email address")
        
        return email

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        errors = {}
        
        if not email:
            errors['email'] = "Email address is required"
        if not password:
            errors['password'] = "Password is required"
        if errors:
            raise serializers.ValidationError(errors)
        
        try:
            user = CustomUser.objects.get(email=email)
            
            if not user.check_password(password):
                errors['non_field_errors'] = "Invalid email or password"
            elif not user.is_active:
                errors['non_field_errors'] = "Your account has been deactivated"
            else:
                data['user'] = user
                
        except CustomUser.DoesNotExist:
            errors['non_field_errors'] = "Invalid email or password"
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data


class QuickLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'Enter your email'},
        help_text="We'll send a magic link to your email"
    )

    def validate_email(self, value):
        try:
            user = CustomUser.objects.get(email=value.lower())
            return value.lower()
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No account found with this email address.")


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password', 'placeholder': 'Enter current password'},
        help_text="Your current account password"
    )
    new_password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password', 'placeholder': 'Enter new password'},
        help_text="New password must be at least 8 characters long",
        validators=[validate_password]
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password', 'placeholder': 'Confirm new password'},
        help_text="Re-enter your new password for confirmation"
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        
        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from current password."})
        
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'Enter your email'},
        help_text="We'll send password reset instructions to this email"
    )


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'Enter your email'}
    )
    otp_code = serializers.CharField(
        max_length=6,
        style={'input_type': 'text', 'placeholder': 'Enter 6-digit OTP'},
        help_text="Enter the OTP sent to your email"
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password', 'placeholder': 'Enter new password'},
        help_text="New password must be at least 8 characters long"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password', 'placeholder': 'Confirm new password'},
        help_text="Re-enter your new password"
    )

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'Enter your email'}
    )
    purpose = serializers.ChoiceField(
        choices=[
            ('login', 'Login'),
            ('verification', 'Verification'), 
            ('password_reset', 'Password Reset')
        ],
        style={'input_type': 'select', 'placeholder': 'Select purpose'},
        help_text="Select why you need the OTP"
    )


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(
        style={'input_type': 'email', 'placeholder': 'Enter your email'}
    )
    otp_code = serializers.CharField(
        max_length=6,
        style={'input_type': 'text', 'placeholder': 'Enter 6-digit OTP'},
        help_text="Enter the OTP sent to your email"
    )


# ==================== USER PROFILE SERIALIZERS ====================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'date_of_birth', 'preferred_vehicle_type',
            'is_verified', 'verification_status', 'total_rides_count',
            'total_distance_covered', 'carbon_saved_total', 'loyalty_points',
            'membership_tier', 'created_at'
        ]
        read_only_fields = [
            'id', 'is_verified', 'verification_status', 'total_rides_count',
            'total_distance_covered', 'carbon_saved_total', 'loyalty_points',
            'membership_tier', 'created_at'
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    aadhaar_card = serializers.FileField(
        required=True,
        style={'input_type': 'file', 'accept': 'image/*,.pdf'},
        help_text="Upload Aadhaar card (front or back)"
    )
    driving_license = serializers.FileField(
        required=True,
        style={'input_type': 'file', 'accept': 'image/*,.pdf'},
        help_text="Upload Driving License"
    )

    class Meta:
        model = DocumentUpload
        fields = ['aadhaar_card', 'driving_license']

    def create(self, validated_data):
        user = self.context['request'].user
        document = DocumentUpload.objects.create(
            user=user,
            **validated_data
        )

        # Update user flags
        user.documents_uploaded = True
        user.verification_status = 'pending'
        user.save()

        return document

class VerificationStatusSerializer(serializers.ModelSerializer):
    verification_history = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'verification_status', 'is_verified', 'verification_approved_at',
            'documents_uploaded', 'driving_license_front', 'driving_license_back', 'id_proof',
            'verification_history'
        ]
        read_only_fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_verified', 'verification_approved_at', 'documents_uploaded',
            'verification_history'
        ]

    def get_verification_history(self, obj):
        return VerificationHistorySerializer(
            obj.verification_history.all(), 
            many=True
        ).data


# ==================== VEHICLE & RIDE SERIALIZERS ====================
class VehicleSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "vehicle_id",
            "vehicle_type",
            "name",
            "model_name",
            "battery_level",
            "battery_status",
            "status",
            "is_available",
            "latitude",
            "longitude",
            "price_per_minute",
            "photo_url",
        ]

    def get_name(self, obj):
        return obj.model_name or getattr(obj, "name", None) or obj.vehicle_id

    def get_latitude(self, obj):
        try:
            return float(obj.current_location_lat) if obj.current_location_lat is not None else None
        except (TypeError, ValueError):
            return None

    def get_longitude(self, obj):
        try:
            return float(obj.current_location_lng) if obj.current_location_lng is not None else None
        except (TypeError, ValueError):
            return None

    def get_photo_url(self, obj):
        request = self.context.get("request")

        if obj.photo and hasattr(obj.photo, "url"):
            if request:
                return request.build_absolute_uri(obj.photo.url)  # FULL URL
            return obj.photo.url  # fallback (relative URL)

        return None  # no image

    def get_is_available(self, obj):
        try:
            return bool(obj.is_available)
        except Exception:
            return obj.status == "available" and (obj.battery_level is None or obj.battery_level > 10)

class RideStartSerializer(serializers.Serializer):
    booking_id = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Booking ID'},
        help_text="Booking ID returned from booking API"
    )
    vehicle_id = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Enter vehicle ID'},
        help_text="ID of the vehicle to start ride"
    )
    qr_code = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Scan QR code'},
        help_text="Scan vehicle QR code to unlock"
    )
    start_location_lat = serializers.DecimalField(
        max_digits=9, decimal_places=6,
        style={'input_type': 'number', 'step': '0.000001'},
        help_text="Starting latitude"
    )
    start_location_lng = serializers.DecimalField(
        max_digits=9, decimal_places=6,
        style={'input_type': 'number', 'step': '0.000001'},
        help_text="Starting longitude"
    )
    start_location_name = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Starting location'},
        help_text="Name of starting location"
    )



class RideEndSerializer(serializers.Serializer):
    ride_id = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Ride ID'},
        help_text="ID of the ride to end"
    )
    end_location_lat = serializers.DecimalField(
        max_digits=9, decimal_places=6,
        style={'input_type': 'number', 'step': '0.000001'},
        help_text="Ending latitude"
    )
    end_location_lng = serializers.DecimalField(
        max_digits=9, decimal_places=6,
        style={'input_type': 'number', 'step': '0.000001'},
        help_text="Ending longitude"
    )
    end_location_name = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Ending location'},
        help_text="Name of ending location"
    )


class RideSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleSerializer(source='vehicle', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Ride
        fields = [
            'ride_id', 'user', 'user_name', 'vehicle', 'vehicle_details',
            'status', 'start_location_lat', 'start_location_lng',
            'end_location_lat', 'end_location_lng', 'start_location_name',
            'end_location_name', 'start_time', 'end_time', 'duration',
            'distance', 'cost', 'carbon_saved', 'payment_status',
            'rating', 'feedback', 'created_at'
        ]
        read_only_fields = ['ride_id', 'created_at']

# ==================== PAYMENT SERIALIZERS ====================

class UpiPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        min_value=10,
        style={'input_type': 'number', 'step': '0.01', 'placeholder': 'Enter amount'},
        help_text="Amount to pay (minimum ₹10)"
    )
    upi_id = serializers.CharField(
        max_length=255,
        style={'input_type': 'text', 'placeholder': 'example@upi'},
        help_text="Enter your UPI ID"
    )
    ride_id = serializers.CharField(
        required=False, 
        allow_null=True,
        style={'input_type': 'text', 'placeholder': 'Ride ID (optional)'},
        help_text="Optional: Ride ID for payment"
    )


class WalletTopupSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        min_value=10,
        style={'input_type': 'number', 'step': '0.01', 'placeholder': 'Enter amount'},
        help_text="Amount to add to wallet (minimum ₹10)"
    )
    payment_method = serializers.ChoiceField(
        choices=[
            ('upi', 'UPI'),
            ('google_pay', 'Google Pay'),
            ('card', 'Card'), 
            ('netbanking', 'Net Banking')
        ],
        style={'input_type': 'select', 'placeholder': 'Select payment method'},
        help_text="Choose your payment method"
    )


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'ride', 'amount', 'payment_method', 'status',
            'transaction_id', 'payment_initiated_at', 'payment_completed_at'
        ]
        read_only_fields = ['id', 'user', 'transaction_id', 'payment_initiated_at']


# ✅ FIXED WALLET SERIALIZER (NO INVALID FIELDS)
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['balance']       # ONLY FIELD THAT EXISTS

# ==================== SAFETY & EMERGENCY SERIALIZERS ====================

class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ['id', 'name', 'phone_number', 'relationship', 'is_primary']
    
    def validate_phone_number(self, value):
        if not value.startswith('+'):
            value = '+91' + value
        return value


class EmergencyAlertSerializer(serializers.ModelSerializer):
    alert_type = serializers.ChoiceField(
        choices=EmergencyAlert.EMERGENCY_TYPES,
        style={'input_type': 'select'},
        help_text="Type of emergency"
    )

    message = serializers.CharField(
        required=False,
        allow_blank=True,
        style={'input_type': 'textarea'},
        help_text="Additional details about the emergency"
    )

    class Meta:
        model = EmergencyAlert
        fields = [
            'id',
            'alert_type',
            'message',
            'location_lat',
            'location_lng',
            'location_name',
            'is_resolved',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']




class ComplaintSerializer(serializers.ModelSerializer):
    complaint_type = serializers.ChoiceField(
        choices=Complaint.COMPLAINT_TYPES,
        style={'input_type': 'select', 'placeholder': 'Select complaint type'},
        help_text="Type of complaint"
    )
    title = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Complaint title'},
        help_text="Brief title for your complaint"
    )
    description = serializers.CharField(
        style={'input_type': 'textarea', 'placeholder': 'Describe your complaint...'},
        help_text="Detailed description of the issue"
    )

    # 📸 Photo upload field
    photo = serializers.ImageField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Complaint
        fields = [
            'id',
            'complaint_type',
            'title',
            'description',
            'photo',          # ← added
            'status',
            'admin_reply',
            'replied_at',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'admin_reply',
            'replied_at',
            'created_at'
        ]

# ==================== PREFERENCES & RECOMMENDATIONS ====================

class UserFavoriteSerializer(serializers.ModelSerializer):
    favorite_type = serializers.ChoiceField(
        choices=UserFavorite.FAVORITE_TYPES,
        style={'input_type': 'select', 'placeholder': 'Select favorite type'},
        help_text="Type of favorite item"
    )
    name = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Favorite name'},
        help_text="Name for this favorite"
    )

    class Meta:
        model = UserFavorite
        fields = [
            'id', 'favorite_type', 'name', 'data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RideRecommendationSerializer(serializers.ModelSerializer):
    vehicles = VehicleSerializer(many=True, read_only=True)
    
    class Meta:
        model = RideRecommendation
        fields = [
            'id', 'recommendation_type', 'title', 'description',
            'confidence_score', 'vehicles', 'display_order', 'expires_at'
        ]
        read_only_fields = ['id']


# ==================== NOTIFICATION & HISTORY SERIALIZERS ====================


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'data',
            'is_read',
            'created_at',
            'read_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'read_at',
        ]
class VerificationHistorySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = VerificationHistory
        fields = ['action', 'notes', 'created_by_name', 'created_at']
        read_only_fields = ['created_at']


class LoginHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginHistory
        fields = [
            'ip_address', 'user_agent', 'attempted_at', 
            'success', 'location'
        ]
        read_only_fields = ['attempted_at']


class EmailOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailOTP
        fields = ['otp', 'purpose', 'expires_at']
        read_only_fields = ['expires_at']


# ==================== RESPONSE SERIALIZERS ====================

class WelcomeMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    user_type = serializers.CharField()
    total_rides = serializers.IntegerField(default=0)
    loyalty_points = serializers.IntegerField(default=0)
    membership_tier = serializers.CharField(default='bronze')
    next_steps = serializers.ListField(child=serializers.CharField())


class LoginWelcomeSerializer(serializers.Serializer):
    message = serializers.CharField()
    user_name = serializers.CharField()
    total_logins = serializers.IntegerField()
    days_since_last_login = serializers.IntegerField(required=False)
    recent_activity = serializers.DictField(required=False)


class LoginResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    user = UserProfileSerializer()
    tokens = serializers.DictField()
    is_verified = serializers.BooleanField()
    requires_verification = serializers.BooleanField()


class RegistrationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    user = UserProfileSerializer()
    requires_verification = serializers.BooleanField()
    verification_method = serializers.CharField()


class StaffDirectorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    department = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(read_only=True)
    is_on_duty = serializers.BooleanField(read_only=True)
    profile_picture = serializers.ImageField(read_only=True)


# ==================== COMPATIBILITY SERIALIZERS ====================

class UserLoginSerializer(serializers.Serializer):
    """Legacy login serializer for compatibility"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include email and password.')


class SocialLoginSerializer(serializers.Serializer):
    """Social media login"""
    provider = serializers.ChoiceField(
        choices=[('google', 'Google'), ('facebook', 'Facebook'), ('apple', 'Apple')],
        style={'input_type': 'select', 'placeholder': 'Select provider'},
        help_text="Choose your social login provider"
    )
    access_token = serializers.CharField(
        style={'input_type': 'text', 'placeholder': 'Enter access token'},
        help_text="Social media access token",
        write_only=True
    )
    email = serializers.EmailField(
        required=False,
        style={'input_type': 'email', 'placeholder': 'Your email from social provider'},
        help_text="Email from your social account"
    )


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    reset_token = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords do not match.")
        return data
    
