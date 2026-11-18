# users/views.py - COMPLETE WITH EMAIL NOTIFICATIONS
from django.contrib.auth import authenticate, login as django_login
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from .models import CustomUser
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.reverse import reverse
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Q, F, Avg
from django.core.files.storage import default_storage
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
import uuid
import random
import json
from datetime import timedelta
from decimal import Decimal
# JWT IMPORTS
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser

from StaffWork.views import get_client_ip

from .models import (
    CustomUser, LoginHistory, Wallet, Vehicle, Ride, Payment, EmergencyContact, 
    EmergencyAlert, Complaint, UserFavorite, RideRecommendation,
    Notification, VerificationHistory, EmailOTP, PasswordResetToken,
    VehicleLocationHistory, DocumentUpload,RideBooking
)

from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, VerificationHistorySerializer,
    VerificationStatusSerializer, DocumentUploadSerializer,
    NotificationSerializer, RideSerializer, PaymentSerializer,
    ComplaintSerializer, VehicleSerializer, WalletSerializer,
    EmergencyContactSerializer, EmergencyAlertSerializer,
    UserFavoriteSerializer, RideRecommendationSerializer,
    SimpleEmailLoginSerializer, PasswordChangeSerializer,
    OTPRequestSerializer, OTPVerifySerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
    LoginHistorySerializer, StaffDirectorySerializer,
    RideStartSerializer, RideEndSerializer, UpiPaymentSerializer, WalletTopupSerializer
)

# ✅ IMPORT EMAIL UTILITIES
from .email_utils import (
    send_welcome_email, send_welcome_back_email, 
    send_verification_email, send_verification_approved_email,
    send_verification_rejected_email, send_document_upload_confirmation_email,
    send_ride_started_email, send_ride_completed_email, send_payment_success_email,
    send_emergency_alert_email, send_staff_emergency_alert,
    send_password_reset_email, send_otp_email
)

# ✅ IMPORT STAFF MODELS FROM STAFFWORK
try:
    from StaffWork.models import StaffProfile, StaffEmergencyContact, EmergencyCallLog
except ImportError:
    class StaffProfile:
        pass
    class StaffEmergencyContact:
        pass  
    class EmergencyCallLog:
        pass

# ========================
# 🔐 AUTHENTICATION & REGISTRATION
# ========================

class UserRegistrationView(generics.CreateAPIView):
    """User Registration with Welcome Email"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create login history
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # ✅ ഇമെയിൽ അയക്കുന്ന ഭാഗം താൽക്കാലികമായി ഒഴിവാക്കാം
        # try:
        #     email_sent = send_welcome_email(user)
        # except Exception as e:
        #     print(f"⚠️ Welcome email failed: {e}")
        
        email_sent = False # താൽക്കാലികമായി False എന്ന് വെക്കുക

        welcome_data = {
            "message": f"🎉 Welcome to Smart Ride, {user.username}!",
            "next_steps": [
                "Verify your email",
                "Add a payment method",
                "Start your first ride!"
            ]
        }

        return Response({
            "success": True,
            "message": "User registered successfully.",
            "email_sent": email_sent,
            "welcome_message": welcome_data,
            "user_id": user.id,
            "email": user.email
        }, status=201)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """
    Smart Ride Unified Login API
    ✅ Single login for Admin, Staff, and User
    ✅ Authenticates by email + password
    ✅ Creates Django session (for dashboards)
    ✅ Returns JWT tokens (for frontend)
    ✅ Redirects correctly for each role
    ✅ Handles duplicate email records safely
    """
    try:
        data = request.data
        email = data.get('email')
        password = data.get('password')

        # 🧩 Validate required fields
        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 🧩 Fetch user safely (avoids duplicate crash)
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

        # 🧩 Authenticate (Django uses username internally)
        user_auth = authenticate(request, username=user.username, password=password)
        print(f"🪄 DEBUG LOGIN => User: {user.username}, Type: {user.user_type}, Authenticated: {bool(user_auth)}")

        if not user_auth:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Create Django session (important for admin/staff dashboards)
        django_login(request, user_auth)

        # ✅ Generate JWT Tokens
        refresh = RefreshToken.for_user(user_auth)

        # ✅ Update last login timestamp
        user_auth.last_login = timezone.now()
        user_auth.save()

        # ✅ Determine redirect URL based on user type
        if user_auth.is_superuser or user_auth.user_type == 'admin':
            redirect_url = '/admin-site/'
        elif user_auth.user_type == 'staff':
            redirect_url = '/staff/dashboard/'
        elif user_auth.user_type == 'customer':
            redirect_url = '/user/home/'
        else:
            redirect_url = '/'

        # ✅ Send JSON Response
        return Response({
            'success': True,
            'message': f"Welcome back, {user_auth.username}!",
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': {
                'id': user_auth.id,
                'username': user_auth.username,
                'email': user_auth.email,
                'user_type': user_auth.user_type,
                'is_verified': getattr(user_auth, 'is_verified', False),
                'is_superuser': user_auth.is_superuser,
                'redirect_url': redirect_url,
            },
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print("⚠️ LOGIN ERROR TRACEBACK:")
        traceback.print_exc()
        return Response({'error': f'Login failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    """Logout"""
    logout(request)
    return Response({'message': 'Logout successful'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change Password"""
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Incorrect current password'}, status=400)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully'})
    return Response(serializer.errors, status=400)


# ========================
# 🔑 FORGOT & RESET PASSWORD
# ========================

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    email = (request.data.get("email") or "").strip().lower()
    if not email:
        return Response({'error': 'Email is required'}, status=400)

    user = CustomUser.objects.filter(email__iexact=email).first()
    if not user:
        return Response({'error': 'User not found'}, status=404)

    otp = str(random.randint(100000, 999999))

    EmailOTP.objects.create(
        email=email,
        otp=otp,
        purpose='password_reset',
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_password_reset_email(user, otp)

    return Response({
        'success': True,
        'message': 'OTP sent successfully to your email'
    })

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """Reset password using OTP"""

    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    # Normalize email
    email = (serializer.validated_data['email'] or "").strip().lower()
    otp_code = serializer.validated_data['otp_code']
    new_password = serializer.validated_data['new_password']

    # Get latest valid OTP (SAFE – never crashes)
    otp_obj = EmailOTP.objects.filter(
        email__iexact=email,
        otp=otp_code,
        is_used=False,
        purpose="password_reset",
        expires_at__gt=timezone.now()
    ).order_by("-created_at").first()

    if not otp_obj:
        return Response({'error': 'Invalid or expired OTP'}, status=400)

    # Get the user (SAFE – chooses first match)
    user = CustomUser.objects.filter(email__iexact=email).first()
    if not user:
        return Response({'error': 'User not found'}, status=404)

    # Reset password
    user.set_password(new_password)
    user.save()

    # Mark OTP as used
    otp_obj.is_used = True
    otp_obj.save()

    return Response({'success': True, 'message': 'Password reset successfully!'})

# ========================
# 👤 PROFILE & VERIFICATION VIEWS
# ========================

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """Get or update user profile"""
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = UserProfileSerializer(
        request.user, 
        data=request.data, 
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_account(request):
    """Delete user account"""
    user = request.user
    user.is_active = False
    user.save()
    return Response({'message': 'Account deleted successfully'})


    
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_verification_documents(request):
    """
    Upload user verification documents (Driving License + Aadhaar)
    """

    user = request.user

    # FRONTEND → backend fields
    dl = request.FILES.get("driving_license")   # driving license
    aadhaar = request.FILES.get("id_proof")     # aadhaar card uploaded as id_proof

    # Validation
    if not dl or not aadhaar:
        return Response(
            {"error": "Driving License and Aadhaar Card are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Save record
    document = DocumentUpload.objects.create(
        user=user,
        driving_license=dl,
        aadhaar_card=aadhaar,
    )

    # Update user status
    user.verification_status = "pending"
    user.is_verified = False
    user.documents_uploaded = True
    user.save()

    # Send confirmation email
    try:
        send_document_upload_confirmation_email(user)
        print(f"📩 User confirmation email sent → {user.email}")
    except Exception as e:
        print(f"❌ Email error: {e}")

    # Notify admin
    try:
        from .email_utils import send_admin_document_alert
        send_admin_document_alert(user)
        print(f"📩 Admin alert sent for → {user.username}")
    except Exception as e:
        print(f"❌ Admin email error: {e}")

    # Verification history
    VerificationHistory.objects.create(
        user=user,
        action='documents_uploaded',
        status='pending',
        notes='User uploaded Driving License + Aadhaar'
    )

    return Response(
        {
            "success": True,
            "message": "Documents uploaded successfully! Confirmation email sent.",
            "verification_status": "pending"
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def verification_status(request):
    """Get verification status"""
    serializer = VerificationStatusSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_preferences(request):
    """Update user preferences"""
    user = request.user
    data = request.data
    
    # Update preferences
    if 'preferred_vehicle_type' in data:
        user.preferred_vehicle_type = data['preferred_vehicle_type']
    if 'preferred_riding_times' in data:
        user.preferred_riding_times = data['preferred_riding_times']
    if 'favorite_areas' in data:
        user.favorite_areas = data['favorite_areas']
    
    user.save()
    return Response({'message': 'Preferences updated successfully'})


# ========================
# 🚗 VEHICLE VIEWS
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def available_vehicles(request):
    # DEBUG: see which user is calling this endpoint (check server console)
    try:
        print("AVAILABLE_VEHICLES CALLED - user:", request.user.username, "user_type:", getattr(request.user, 'user_type', None))
    except Exception:
        print("AVAILABLE_VEHICLES CALLED - user: (unknown)")

    # conservative queryset: any vehicle that is not explicitly non-available
    # vehicles = Vehicle.objects.exclude(status__in=['maintenance','offline'])
    vehicles = Vehicle.objects.filter(status='available')

    # If you want strict only 'available' use the original filter below:
    # vehicles = Vehicle.objects.filter(status='available')

    serializer = VehicleSerializer(vehicles, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nearby_vehicles(request):
    """Get nearby vehicles based on location"""
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    radius = request.GET.get('radius', 5)  # Default 5km radius
    
    if not lat or not lng:
        return Response(
            {'error': 'Latitude and longitude required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Basic nearby filtering (implement proper geospatial query)
    vehicles = Vehicle.objects.filter(status='available')
    serializer = VehicleSerializer(vehicles, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vehicle_detail(request, vehicle_id):
    """Get vehicle details"""
    try:
        vehicle = Vehicle.objects.get(vehicle_id=vehicle_id)
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data)
    except Vehicle.DoesNotExist:
        return Response(
            {'error': 'Vehicle not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

# ========================
# 🚲 RIDE MANAGEMENT VIEWS
# ========================

from datetime import timedelta  # already imported above, re-use

ADVANCE_AMOUNT = Decimal('300.00')
BOOKING_HOLD_MINUTES = 15  # how long booking is valid
CANCELLATION_REFUND_HOURS = 1  # full refund if cancelled within this time


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def book_ride(request):
    """
    Book a vehicle and debit ₹300 advance from wallet.
    Flow:
    - Check verification
    - Check wallet >= 300
    - Debit 300
    - Mark vehicle as 'booked'
    - Create RideBooking record
    """
    user = request.user

    # must be verified (already same rule as start_ride)
    if not user.can_book_ride():
        return Response(
            {
                "success": False,
                "error": "Verification required. Please upload documents and wait for admin approval."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    vehicle_id = request.data.get('vehicle_id')
    if not vehicle_id:
        return Response({"error": "vehicle_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # vehicle must be free
    try:
        vehicle = Vehicle.objects.get(vehicle_id=vehicle_id, status='available')
    except Vehicle.DoesNotExist:
        return Response(
            {"success": False, "error": "Vehicle not available for booking"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # wallet check
    wallet, _ = Wallet.objects.get_or_create(user=user)

    if wallet.balance < ADVANCE_AMOUNT:
        return Response(
            {
                "success": False,
                "error": "Insufficient wallet balance. Minimum ₹300 required to book a ride.",
                "wallet_balance": str(wallet.balance)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # if user already has a pending booking on this vehicle, block
    existing = RideBooking.objects.filter(
        user=user,
        vehicle=vehicle,
        status='pending'
    ).first()
    if existing:
        return Response(
            {
                "success": False,
                "error": "You already have an active booking for this vehicle.",
                "booking_id": existing.booking_id
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # debit advance
    wallet.balance = wallet.balance - ADVANCE_AMOUNT
    wallet.save()

    # create booking
    expires_at = timezone.now() + timedelta(minutes=BOOKING_HOLD_MINUTES)
    booking = RideBooking.objects.create(
        booking_id=f"BOOK{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}",
        user=user,
        vehicle=vehicle,
        status='pending',
        advance_amount=ADVANCE_AMOUNT,
        expires_at=expires_at
    )

    # lock vehicle
    vehicle.status = 'booked'
    vehicle.save()

    return Response(
        {
            "success": True,
            "message": "Vehicle booked successfully. ₹300 advance debited from wallet.",
            "booking_id": booking.booking_id,
            "advance_amount": str(booking.advance_amount),
            "expires_at": booking.expires_at,
            "wallet_balance": str(wallet.balance),
            "vehicle_id": vehicle.vehicle_id,
        },
        status=status.HTTP_201_CREATED
    )


# ============================================
# 🚀 START RIDE (WITH VERIFICATION CHECK)
# ============================================
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def start_ride(request):
    """
    Start ride AFTER booking:
    - Requires booking_id + qr_code + start location
    - Booking must be pending & not expired
    - Vehicle set to in_use
    - Ride created and linked to booking
    """
    user = request.user

    # verification check
    if not user.can_book_ride():
        return Response(
            {
                "success": False,
                "error": "Verification required. Please upload documents and wait for admin approval."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = RideStartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    booking_id = serializer.validated_data['booking_id']
    vehicle_id = serializer.validated_data['vehicle_id']
    qr_code = serializer.validated_data['qr_code']

    try:
        booking = RideBooking.objects.select_related('vehicle').get(
            booking_id=booking_id,
            user=user
        )
    except RideBooking.DoesNotExist:
        return Response(
            {"success": False, "error": "Booking not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # check booking still valid
    if not booking.is_valid:
        booking.status = 'expired'
        booking.save()
        return Response(
            {"success": False, "error": "Booking expired. Please book again."},
            status=status.HTTP_400_BAD_REQUEST
        )

    vehicle = booking.vehicle

    # safety: vehicle id must match
    if vehicle.vehicle_id != vehicle_id:
        return Response(
            {"success": False, "error": "Vehicle does not match this booking."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 🔐 NOTE: this assumes you already have `qr_code` field in Vehicle model
    try:
        # only allow start if vehicle is booked or available
        if vehicle.status not in ['booked', 'available']:
            return Response(
                {"success": False, "error": "Vehicle is not ready to start ride."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # If you store QR on vehicle, validate here:
        # if vehicle.qr_code != qr_code:
        #     return Response({"success": False, "error": "Invalid QR code."}, status=status.HTTP_400_BAD_REQUEST)

    except AttributeError:
        # If no qr_code field exists, just skip strict QR validation
        pass

    # ensure no other active ride
    active_ride = Ride.objects.filter(user=user, status='active').first()
    if active_ride:
        return Response(
            {'error': 'You already have an active ride.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # create ride
    ride = Ride.objects.create(
        user=user,
        vehicle=vehicle,
        start_location_lat=serializer.validated_data['start_location_lat'],
        start_location_lng=serializer.validated_data['start_location_lng'],
        start_location_name=serializer.validated_data['start_location_name'],
        status='active',
        start_time=timezone.now()
    )

    # link booking → ride
    booking.ride = ride
    booking.status = 'active'
    booking.save()

    # move vehicle to in_use
    vehicle.status = 'in_use'
    vehicle.save()

    # email
    send_ride_started_email(user, ride, vehicle)

    return Response(
        {
            "success": True,
            "message": "Ride started successfully.",
            "ride": RideSerializer(ride).data,
            "booking_id": booking.booking_id
        },
        status=status.HTTP_201_CREATED
    )


# ============================================
# 🚀 END RIDE (FARE + BATTERY + STATS)
# ============================================
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_ride(request):
    user = request.user
    serializer = RideEndSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    ride_id = serializer.validated_data['ride_id']

    # 1) Fetch active ride
    try:
        ride = Ride.objects.get(
            ride_id=ride_id,
            user=user,
            status='active'
        )
    except Ride.DoesNotExist:
        return Response({'error': 'Active ride not found'}, status=404)

    end_time = timezone.now()
    duration_minutes = (end_time - ride.start_time).total_seconds() / 60

    PRICE_PER_MIN = Decimal('5')
    ADVANCE_AMOUNT = Decimal('300.00')

    # ⭐ TOTAL FARE (FULL DEDUCT)
    total_fare = (Decimal(str(duration_minutes)) * PRICE_PER_MIN).quantize(Decimal('0.01'))

    # ⭐ Wallet fetch
    wallet, _ = Wallet.objects.get_or_create(user=user)
    old_balance = wallet.balance

    payment_status = "paid"

    # ⭐ Deduct FULL fare from wallet (not fare - 300)
    if wallet.balance >= total_fare:
        wallet.balance -= total_fare
        wallet.save()
        deduction_message = f" ₹{total_fare} deducted from wallet."
    else:
        # Not enough balance
        payment_status = "pending"
        deduction_message = (
            f" ₹{total_fare} pending. Insufficient wallet balance."
        )

    # ⭐ Update ride
    ride.end_location_lat = serializer.validated_data['end_location_lat']
    ride.end_location_lng = serializer.validated_data['end_location_lng']
    ride.end_location_name = serializer.validated_data.get('end_location_name', "End Point")
    ride.end_time = end_time
    ride.duration = end_time - ride.start_time
    ride.cost = total_fare
    ride.status = 'completed'
    ride.payment_status = payment_status
    ride.save()

    # ⭐ Update vehicle
    vehicle = ride.vehicle
    vehicle.status = 'available'
    vehicle.current_location_lat = ride.end_location_lat
    vehicle.current_location_lng = ride.end_location_lng
    vehicle.battery_level = max(0, vehicle.battery_level - 10)
    vehicle.save()

    # ⭐ Update booking
    booking = getattr(ride, 'booking', None)
    if booking:
        booking.status = 'completed'
        booking.save()

    # ⭐ Final response
    return Response({
        "success": True,
        "message": "Ride completed successfully." + deduction_message,
        "fare_summary": {
            "ride_id": ride.ride_id,
            "total_fare": str(total_fare),
            "advance_paid": "300.00",
            "wallet_before": str(old_balance),
            "wallet_after": str(wallet.balance),
            "payment_status": payment_status,
        }
    })

# ============================================
# 🚀 CANCEL BOOKING
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_booking(request):
    user = request.user
    booking_id = request.data.get("booking_id")

    if not booking_id:
        return Response({'error': 'booking_id required'}, status=400)

    try:
        booking = RideBooking.objects.select_related('vehicle').get(
            booking_id=booking_id,
            user=user,
            status__in=['pending', 'booked']  # FIXED ✔
        )
    except RideBooking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=404)

    current_time = timezone.now()
    elapsed_hours = (current_time - booking.created_at).total_seconds() / 3600

    wallet, _ = Wallet.objects.get_or_create(user=user)
    refund_amount = Decimal('0.00')

    if elapsed_hours <= CANCELLATION_REFUND_HOURS:
        refund_amount = ADVANCE_AMOUNT
        wallet.balance = Decimal(wallet.balance) + refund_amount
        wallet.save(update_fields=["balance"])
        message = "Booking cancelled. ₹300 refunded."
    else:
        message = "Booking cancelled. No refund (after 1 hour)."

    booking.status = 'cancelled'
    booking.refund_amount = refund_amount
    booking.cancelled_at = current_time
    booking.save(update_fields=['status','refund_amount','cancelled_at'])

    booking.vehicle.status = "available"
    booking.vehicle.save(update_fields=["status"])

    return Response({
        "success": True,
        "message": message,
        "refund_amount": str(refund_amount),
        "wallet_balance": str(wallet.balance)
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_cancellation_eligibility(request, booking_id):
    """
    Check if user can cancel booking and get refund
    """
    user = request.user
    
    try:
        booking = RideBooking.objects.get(
            booking_id=booking_id,
            user=user,
            status='pending'
        )
    except RideBooking.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Active booking not found'
        }, status=status.HTTP_404_NOT_FOUND)

    current_time = timezone.now()
    booking_time = booking.created_at
    time_diff = current_time - booking_time
    time_diff_hours = time_diff.total_seconds() / 3600

    can_cancel = time_diff_hours <= CANCELLATION_REFUND_HOURS
    refund_amount = ADVANCE_AMOUNT if can_cancel else Decimal('0.00')
    time_remaining_for_refund = max(0, (CANCELLATION_REFUND_HOURS * 3600) - time_diff.total_seconds())

    return Response({
        "success": True,
        "can_cancel": can_cancel,
        "refund_eligible": can_cancel,
        "refund_amount": str(refund_amount),
        "booking_time": booking_time,
        "current_time": current_time,
        "time_remaining_for_refund_seconds": time_remaining_for_refund,
        "time_remaining_minutes": round(time_remaining_for_refund / 60, 1),
        "time_since_booking_hours": round(time_diff_hours, 2),
        "booking_details": {
            "booking_id": booking.booking_id,
            "vehicle_id": booking.vehicle.vehicle_id,
            "vehicle_name": booking.vehicle.name,
            "advance_paid": str(booking.advance_amount)
        }
    })


# ============================================
# 🚀 GET CURRENT RIDE
# ============================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_ride(request):
    try:
        ride = Ride.objects.get(user=request.user, status='active')
        return Response(RideSerializer(ride).data)
    except Ride.DoesNotExist:
        return Response({"active_ride": False})



# ============================================
# 🚀 RIDE HISTORY
# ============================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ride_history(request):
    rides = Ride.objects.filter(user=request.user).order_by('-created_at')
    return Response(RideSerializer(rides, many=True).data)



# ============================================
# 🚀 RIDE DETAILS
# ============================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ride_detail(request, ride_id):
    try:
        ride = Ride.objects.get(id=ride_id, user=request.user)
        return Response(RideSerializer(ride).data)
    except Ride.DoesNotExist:
        return Response(
            {'error': 'Ride not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

# ========================
# 💰 PAYMENT & WALLET VIEWS
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wallet_balance(request):
    """Get wallet balance"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    serializer = WalletSerializer(wallet)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_wallet_balance(request):
    """Add money to wallet"""
    serializer = WalletTopupSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.balance += float(amount)
        wallet.save()
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            amount=amount,
            payment_method=payment_method,
            status='completed'
        )
        
        # ✅ SEND PAYMENT SUCCESS EMAIL
        send_payment_success_email(request.user, payment, 'wallet_topup')
        
        return Response(WalletSerializer(wallet).data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_upi_payment(request):
    """Process UPI payment for ride"""
    serializer = UpiPaymentSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data['amount']
        upi_id = serializer.validated_data['upi_id']
        ride_id = serializer.validated_data.get('ride_id')
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            amount=amount,
            payment_method='upi',
            upi_id=upi_id,
            status='completed'
        )
        
        # Update ride payment status if ride_id provided
        if ride_id:
            try:
                ride = Ride.objects.get(id=ride_id, user=request.user)
                ride.payment_status = 'paid'
                ride.payment_method = 'upi'
                ride.save()
                payment.ride = ride
                payment.save()
            except Ride.DoesNotExist:
                pass
        
        # ✅ SEND PAYMENT SUCCESS EMAIL
        send_payment_success_email(request.user, payment, 'ride_payment')
        
        return Response({
            'message': 'Payment processed successfully',
            'transaction_id': payment.transaction_id,
            'amount': amount
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_history(request):
    """Get payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-payment_initiated_at')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

# ========================
# 🚨 EMERGENCY & SAFETY VIEWS
# ========================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def emergency_alert(request):
    """Send emergency alert"""
    serializer = EmergencyAlertSerializer(data=request.data)
    if serializer.is_valid():
        alert = serializer.save(user=request.user)
        
        # ✅ SEND EMERGENCY ALERT EMAIL TO USER
        send_emergency_alert_email(request.user, alert)
        
        # ✅ SEND STAFF EMERGENCY ALERT
        send_staff_emergency_alert(alert)
        
        # Notify emergency contacts
        contacts = EmergencyContact.objects.filter(user=request.user, is_primary=True)
        for contact in contacts:
            # In real implementation, send SMS/email to contacts
            pass
        
        return Response(EmergencyAlertSerializer(alert).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def emergency_contacts(request):
    """Get or add emergency contacts"""
    if request.method == 'GET':
        contacts = EmergencyContact.objects.filter(user=request.user)
        serializer = EmergencyContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = EmergencyContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_complaint(request):
    """Create complaint"""
    serializer = ComplaintSerializer(data=request.data)
    if serializer.is_valid():
        complaint = serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ========================
# 🎯 RECOMMENDATION & FAVORITES VIEWS
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_recommendations(request):
    """Get ride recommendations"""
    recommendations = RideRecommendation.objects.filter(
        user=request.user, 
        is_active=True
    ).order_by('display_order')
    serializer = RideRecommendationSerializer(recommendations, many=True)
    return Response(serializer.data)

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def favorite_locations(request):
    """Get or add favorite locations"""
    if request.method == 'GET':
        favorites = UserFavorite.objects.filter(
            user=request.user, 
            favorite_type='location'
        )
        serializer = UserFavoriteSerializer(favorites, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        request.data['favorite_type'] = 'location'
        serializer = UserFavoriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ========================
# 🔔 NOTIFICATION VIEWS
# ========================
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list(request):
    """Get user notifications with unread count"""
    
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    serializer = NotificationSerializer(notifications, many=True)

    unread_count = notifications.filter(is_read=False).count()

    return Response({
        "unread_count": unread_count,
        "notifications": serializer.data
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request):
    """Mark notification as read"""
    notification_id = request.data.get('notification_id')
    
    try:
        notification = Notification.objects.get(
            id=notification_id, 
            user=request.user
        )
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def clear_all_notifications(request):
    user = request.user
    Notification.objects.filter(user=user).delete()

    return Response({
        "message": "All notifications cleared!",
        "unread_count": 0,
        "notifications": []
    })


# ========================
# 📊 ANALYTICS & HISTORY VIEWS
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ride_statistics(request):
    """Get ride statistics"""
    user = request.user
    rides = Ride.objects.filter(user=user, status='completed')
    
    stats = {
        'total_rides': rides.count(),
        'total_distance': rides.aggregate(total=Sum('distance'))['total'] or 0,
        'total_spent': rides.aggregate(total=Sum('cost'))['total'] or 0,
        'total_carbon_saved': rides.aggregate(total=Sum('carbon_saved'))['total'] or 0,
        'average_rating': rides.aggregate(avg=Avg('rating'))['avg'] or 0
    }
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def login_history(request):
    """Get login history"""
    history = LoginHistory.objects.filter(user=request.user).order_by('-attempted_at')
    serializer = LoginHistorySerializer(history, many=True)
    return Response(serializer.data)

# ========================
# 👑 ADMIN VIEWS
# ========================

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_approve_verification(request, user_id):
    """Admin approve user verification"""
    try:
        user = CustomUser.objects.get(id=user_id)
        user.verification_status = 'approved'
        user.is_verified = True
        user.verification_approved_at = timezone.now()
        user.save()
        
        # ✅ SEND VERIFICATION APPROVED EMAIL
        send_verification_approved_email(user)
        
        # Create verification history
        VerificationHistory.objects.create(
            user=user,
            action='verification_approved',
            status='approved',
            notes='Admin approved verification',
            processed_by=request.user
        )
        
        return Response({'message': f'User {user.username} verification approved'})
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_reject_verification(request, user_id):
    """Admin reject user verification"""
    rejection_reason = request.data.get('rejection_reason', '')
    
    if not rejection_reason:
        return Response(
            {'error': 'Rejection reason required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = CustomUser.objects.get(id=user_id)
        user.verification_status = 'rejected'
        user.is_verified = False
        user.verification_rejected_at = timezone.now()
        user.verification_rejection_reason = rejection_reason
        user.save()
        
        # ✅ SEND VERIFICATION REJECTED EMAIL
        send_verification_rejected_email(user, rejection_reason)
        
        # Create verification history
        VerificationHistory.objects.create(
            user=user,
            action='verification_rejected',
            status='rejected',
            notes=f'Rejection reason: {rejection_reason}',
            processed_by=request.user
        )
        
        return Response({'message': f'User {user.username} verification rejected'})
    except CustomUser.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

# ========================
# 🔧 UTILITY VIEWS
# ========================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })

# ========================
# 🚀 STAFF SPECIFIC VIEWS
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def staff_directory(request):
    """Get staff directory"""
    try:
        if request.user.user_type != 'staff' and request.user.user_type != 'admin':
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        staff = CustomUser.objects.filter(user_type='staff', is_active=True)
        staff_data = []
        
        for staff_member in staff:
            staff_data.append({
                'id': staff_member.id,
                'name': staff_member.get_full_name() or staff_member.username,
                'email': staff_member.email,
                'phone': staff_member.phone_number,
                'role': 'Staff Member',
                'department': 'Operations',
                'is_on_duty': True  # This would come from StaffProfile in real implementation
            })
        
        return Response({'staff': staff_data})
    except Exception as e:
        return Response({'staff': []})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def staff_emergency_alert(request):
    """Staff emergency alert endpoint"""
    if request.user.user_type != 'staff':
        return Response(
            {'error': 'Access denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = EmergencyAlertSerializer(data=request.data)
    if serializer.is_valid():
        alert = serializer.save(user=request.user)
        
        # ✅ SEND STAFF EMERGENCY ALERT TO ADMIN
        send_staff_emergency_alert(alert, is_staff_alert=True)
        
        return Response({
            'message': 'Emergency alert sent successfully',
            'alert_id': alert.id
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Add this to Users/views.py (anywhere after the imports)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def verification_history(request):
    """Get user verification history"""
    try:
        history = VerificationHistory.objects.filter(user=request.user).order_by('-created_at')
        # Create a simple serializer for the response
        history_data = []
        for item in history:
            history_data.append({
                'id': item.id,
                'action': item.action,
                'status': item.status,
                'notes': item.notes,
                'created_at': item.created_at
            })
        return Response(history_data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# ========================
# 🚗 VEHICLE VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vehicle_location_history(request, vehicle_id):
    """Get vehicle location history"""
    try:
        vehicle = Vehicle.objects.get(vehicle_id=vehicle_id)
        # Return empty list for now - implement later
        return Response([])
    except Vehicle.DoesNotExist:
        return Response(
            {'error': 'Vehicle not found'},
            status=status.HTTP_404_NOT_FOUND
        )

# ========================
# 🚲 RIDE MANAGEMENT VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def ride_analytics(request):
    """Get ride analytics"""
    return Response({'message': 'Ride analytics endpoint'})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_ride(request, ride_id):
    """Cancel ride"""
    try:
        ride = Ride.objects.get(id=ride_id, user=request.user)
        ride.status = 'cancelled'
        ride.save()
        return Response({'message': 'Ride cancelled successfully'})
    except Ride.DoesNotExist:
        return Response(
            {'error': 'Ride not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def rate_ride(request, ride_id):
    """Rate ride"""
    rating = request.data.get('rating')
    feedback = request.data.get('feedback', '')
    
    try:
        ride = Ride.objects.get(id=ride_id, user=request.user)
        ride.rating = rating
        ride.feedback = feedback
        ride.save()
        return Response({'message': 'Ride rated successfully'})
    except Ride.DoesNotExist:
        return Response(
            {'error': 'Ride not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def active_rides(request):
    """Get active rides"""
    rides = Ride.objects.filter(user=request.user, status='active')
    serializer = RideSerializer(rides, many=True)
    return Response(serializer.data)

# ========================
# 💰 PAYMENT & WALLET VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wallet_transactions(request):
    """Get wallet transactions"""
    return Response({'transactions': []})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def process_payment(request):
    """Process payment"""
    return Response({'message': 'Payment processed'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_detail(request, payment_id):
    """Get payment details"""
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)
    except Payment.DoesNotExist:
        return Response(
            {'error': 'Payment not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_refund(request):
    """Request refund"""
    return Response({'message': 'Refund requested'})

# ========================
# 🚨 EMERGENCY & SAFETY VIEWS (Missing)
# ========================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_emergency_contact(request):
    """Add emergency contact"""
    serializer = EmergencyContactSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def emergency_contact_detail(request, contact_id):
    """Emergency contact detail"""
    try:
        contact = EmergencyContact.objects.get(id=contact_id, user=request.user)
        
        if request.method == 'GET':
            serializer = EmergencyContactSerializer(contact)
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            serializer = EmergencyContactSerializer(contact, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            contact.delete()
            return Response({'message': 'Contact deleted'})
            
    except EmergencyContact.DoesNotExist:
        return Response(
            {'error': 'Contact not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_emergency_contact(request, contact_id):
    """Delete emergency contact"""
    try:
        contact = EmergencyContact.objects.get(id=contact_id, user=request.user)
        contact.delete()
        return Response({'message': 'Contact deleted'})
    except EmergencyContact.DoesNotExist:
        return Response(
            {'error': 'Contact not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def emergency_alerts_history(request):
    """Get emergency alerts history"""
    alerts = EmergencyAlert.objects.filter(user=request.user).order_by('-created_at')
    serializer = EmergencyAlertSerializer(alerts, many=True)
    return Response(serializer.data)

# ========================
# 📊 COMPLAINT & SUPPORT VIEWS (Missing)
# ========================
# ================================
# 📌 COMPLAINT VIEWS (FINAL)
# ================================
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def complaints_history(request):
    complaints = Complaint.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return Response([
        {
            "id": c.id,
            "complaint_type": c.complaint_type,   # FIXED
            "title": c.title,
            "status": c.status,
            "created_at": c.created_at,
            "photo": request.build_absolute_uri(c.photo.url) if c.photo else None
        }
        for c in complaints
    ])

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def complaint_detail(request, complaint_id):
    """
    Get full complaint detail including photos, admin reply, timestamps
    """
    try:
        complaint = Complaint.objects.get(
            id=complaint_id,
            user=request.user
        )
    except Complaint.DoesNotExist:
        return Response(
            {"error": "Complaint not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ComplaintSerializer(complaint, context={"request": request})

    return Response({
        "success": True,
        "complaint": serializer.data
    })
@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_complaint(request, complaint_id):
    """Delete a user complaint (allowed only when status = 'open')."""
    try:
        complaint = Complaint.objects.get(id=complaint_id, user=request.user)
    except Complaint.DoesNotExist:
        return Response({"error": "Complaint not found"}, status=404)

    # User can delete only OPEN complaints
    if complaint.status != "open":
        return Response(
            {"error": "Only open complaints can be deleted"},
            status=400
        )

    complaint.delete()
    return Response({"message": "Complaint deleted successfully"}, status=200)

@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_complaint(request, complaint_id):
    try:
        complaint = Complaint.objects.get(id=complaint_id, user=request.user)
    except Complaint.DoesNotExist:
        return Response({"error": "Complaint not found"}, status=404)

    # Only open complaints can be edited
    if complaint.status != "open":
        return Response({"error": "You can only edit OPEN complaints."}, status=400)

    print("FILES:", request.FILES)                    # DEBUG
    print("DATA:", request.data)                      # DEBUG

    serializer = ComplaintSerializer(
        complaint,
        data=request.data,
        partial=True,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()

        # ⭐ If photos uploaded → add them manually
        if 'photos' in request.FILES:
            for file in request.FILES.getlist('photos'):
                complaint.photos.create(image=file)

        return Response({
            "message": "Complaint updated successfully",
            "data": serializer.data
        }, status=200)

    print("SERIALIZER ERRORS:", serializer.errors)    # DEBUG
    return Response(serializer.errors, status=400)



# ========================
# 🎯 RECOMMENDATION & FAVORITES VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vehicle_recommendations(request):
    """Get vehicle recommendations"""
    return Response({'recommendations': []})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_favorite_location(request):
    """Add favorite location"""
    request.data['favorite_type'] = 'location'
    serializer = UserFavoriteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def favorite_location_detail(request, favorite_id):
    """Favorite location detail"""
    try:
        favorite = UserFavorite.objects.get(id=favorite_id, user=request.user, favorite_type='location')
        
        if request.method == 'GET':
            serializer = UserFavoriteSerializer(favorite)
            return Response(serializer.data)
            
        elif request.method == 'PUT':
            serializer = UserFavoriteSerializer(favorite, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        elif request.method == 'DELETE':
            favorite.delete()
            return Response({'message': 'Favorite location deleted'})
            
    except UserFavorite.DoesNotExist:
        return Response(
            {'error': 'Favorite not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_favorite_location(request, favorite_id):
    """Delete favorite location"""
    try:
        favorite = UserFavorite.objects.get(id=favorite_id, user=request.user, favorite_type='location')
        favorite.delete()
        return Response({'message': 'Favorite location deleted'})
    except UserFavorite.DoesNotExist:
        return Response(
            {'error': 'Favorite not found'},
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def favorite_vehicles(request):
    """Get favorite vehicles"""
    favorites = UserFavorite.objects.filter(user=request.user, favorite_type='vehicle')
    serializer = UserFavoriteSerializer(favorites, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def favorite_routes(request):
    """Get favorite routes"""
    favorites = UserFavorite.objects.filter(user=request.user, favorite_type='route')
    serializer = UserFavoriteSerializer(favorites, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_favorites(request):
    """Get all favorites"""
    favorites = UserFavorite.objects.filter(user=request.user)
    serializer = UserFavoriteSerializer(favorites, many=True)
    return Response(serializer.data)
# ============================
# 🔔 NOTIFICATION VIEWS
# ============================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone

from Users.models import Notification
from Users.serializers import NotificationSerializer


# ------------------------------------------------------------
# GET: All unread notifications
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_notifications(request):
    """Return all unread notifications for the authenticated user (consistent shape)."""
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    serializer = NotificationSerializer(notifications, many=True)
    count = notifications.count()

    return Response({
        "unread_count": count,
        "notifications": serializer.data
    })

# ------------------------------------------------------------
# POST: Mark ALL notifications as read
# ------------------------------------------------------------
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all unread notifications as read and return updated count."""
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )

    # return updated unread_count for the frontend
    unread_after = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({
        "message": "All notifications marked as read",
        "unread_count": unread_after
    })

# ------------------------------------------------------------
# GET: Single notification detail
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_detail(request, notification_id):
    """Return details of a specific notification."""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = NotificationSerializer(notification)
    return Response(serializer.data)


# ------------------------------------------------------------
# GET: Count unread notifications
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def unread_count(request):
    """Return count of unread notifications."""
    count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return Response({'unread_count': count})


# ------------------------------------------------------------
# GET/PUT: Notification Settings (Future expansion)
# ------------------------------------------------------------
@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def notification_settings(request):
    """
    Placeholder for notification preferences (sound, type filters, etc.)
    Currently returns an empty settings object to avoid frontend errors.
    """
    return Response({'settings': {}})

# ========================
# 📍 LOCATION & SERVICE VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_service_area(request):
    """Check service area"""
    return Response({'in_service_area': True})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_ride_eligibility(request):
    """Check ride eligibility"""
    return Response({'eligible': True})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_user_location(request):
    """Update user location"""
    return Response({'message': 'Location updated'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def nearby_charging_stations(request):
    """Get nearby charging stations"""
    return Response({'charging_stations': []})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def suggested_pickup_locations(request):
    """Get suggested pickup locations"""
    return Response({'suggested_locations': []})

# ========================
# 📊 ANALYTICS & HISTORY VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def carbon_savings(request):
    """Get carbon savings"""
    user = request.user
    return Response({
        'total_carbon_saved': user.carbon_saved_total,
        'equivalent_trees': user.carbon_saved_total * 0.1  # Example calculation
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def loyalty_points_history(request):
    """Get loyalty points history"""
    return Response({'history': []})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity_history(request):
    """Get user activity history"""
    return Response({'activity': []})

# ========================
# 👑 STAFF & SUPPORT VIEWS (Missing)
# ========================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def on_duty_staff(request):
    """Get on-duty staff"""
    return Response({'staff': []})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def contact_support(request):
    """Contact support"""
    return Response({'message': 'Support contacted'})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def faq_list(request):
    """Get FAQ list"""
    return Response({'faqs': []})

# ========================
# ⚙️ SETTINGS & PREFERENCES VIEWS (Missing)
# ========================

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def privacy_settings(request):
    """Get or update privacy settings"""
    return Response({'settings': {}})

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_notification_settings(request):
    """Update notification settings"""
    return Response({'message': 'Notification settings updated'})

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def security_settings(request):
    """Get or update security settings"""
    return Response({'settings': {}})

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def ride_preferences(request):
    """Get or update ride preferences"""
    return Response({'preferences': {}})
# ========================
# 🔧 UTILITY VIEWS (END)
# ========================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def app_version(request):
    """Get app version"""
    return Response({'version': '1.0.0'})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def maintenance_status(request):
    """Get maintenance status"""
    return Response({'under_maintenance': False})

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def clear_cache(request):
    """Clear cache"""
    return Response({'message': 'Cache cleared'})

# ========================
# 🌐 SMART RIDE API ROOT
# ========================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request, format=None):
    """
    📋 SmartRide Users API Root
    Provides an overview of all available user API endpoints
    """
    return Response({
        # 🔐 AUTHENTICATION ENDPOINTS
        'user-register': reverse('user-register', request=request, format=format),
        'user-login': reverse('user-login', request=request, format=format),
        'user-logout': reverse('user-logout', request=request, format=format),
        'change-password': reverse('change-password', request=request, format=format),
        'forgot-password': reverse('forgot-password', request=request, format=format),
        'reset-password': reverse('reset-password', request=request, format=format),

        # 👤 USER PROFILE ENDPOINTS
        'user-profile': reverse('user-profile', request=request, format=format),
        'update-profile': reverse('update-profile', request=request, format=format),
        'verification-status': reverse('verification-status', request=request, format=format),

        # 🚗 VEHICLE ENDPOINTS
        'available-vehicles': reverse('available-vehicles', request=request, format=format),
        'nearby-vehicles': reverse('nearby-vehicles', request=request, format=format),

        # 🚲 RIDE MANAGEMENT ENDPOINTS
        'start-ride': reverse('start-ride', request=request, format=format),
        'end-ride': reverse('end-ride', request=request, format=format),
        'current-ride': reverse('current-ride', request=request, format=format),
        'ride-history': reverse('ride-history', request=request, format=format),

        # 💰 PAYMENT & WALLET ENDPOINTS
        'wallet-balance': reverse('wallet-balance', request=request, format=format),
        'wallet-topup': reverse('wallet-topup', request=request, format=format),
        'upi-payment': reverse('upi-payment', request=request, format=format),

        # 🚨 EMERGENCY & SAFETY ENDPOINTS
        'emergency-alert': reverse('emergency-alert', request=request, format=format),
        'emergency-contacts': reverse('emergency-contacts', request=request, format=format),

        # 🔔 NOTIFICATION ENDPOINTS
        'notification-list': reverse('notification-list', request=request, format=format),
        'unread-notifications': reverse('unread-notifications', request=request, format=format),

        # 📊 ANALYTICS ENDPOINTS
        'ride-statistics': reverse('ride-statistics', request=request, format=format),
        'carbon-savings': reverse('carbon-savings', request=request, format=format),

        # ⚙️ UTILITY ENDPOINTS
        'health-check': reverse('health-check', request=request, format=format),
        'app-version': reverse('app-version', request=request, format=format),
        'maintenance-status': reverse('maintenance-status', request=request, format=format),
    })
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def verification_access_mode(request):
    """
    Determine the user's current access mode based on verification status.
    - Before admin approval: 'view_only'
    - After approval: 'full_access'
    """
    user = request.user
    mode = "full_access" if user.is_verified and user.verification_status == "approved" else "view_only"

    return Response({
        "user_id": user.id,
        "username": user.username,
        "is_verified": user.is_verified,
        "verification_status": user.verification_status,
        "mode": mode,
        "functions_locked": mode == "view_only",
        "message": "✅ Full access granted" if mode == "full_access" else "⏳ Verification pending — limited view mode"
    })
