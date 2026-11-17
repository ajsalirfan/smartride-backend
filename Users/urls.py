# users/urls.py - COMPLETE AND CLEAN URL CONFIGURATION WITH API ROOT
from django.urls import path
from rest_framework.routers import DefaultRouter

from Users.views_payment import create_razorpay_order, razorpay_payment_success
from . import views
from .views import UserRegistrationView

# Optional router (for ViewSets if added later)
router = DefaultRouter()
# router.register('vehicles', views.VehicleViewSet)

urlpatterns = [
    # ==================== 🌐 API ROOT ====================
    path('', views.api_root, name='api-root'),

    # ==================== 🔐 AUTHENTICATION URLS ====================
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', views.login_user, name='user-login'),
    path('logout/', views.logout_user, name='user-logout'),
    path('change-password/', views.change_password, name='change-password'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),

    # ==================== 👤 USER PROFILE URLS ====================
    path('profile/', views.user_profile, name='user-profile'),
    path('profile/update/', views.update_profile, name='update-profile'),
    path('profile/preferences/', views.update_preferences, name='update-preferences'),
    path('profile/delete/', views.delete_account, name='delete-account'),

    # ==================== 🪪 VERIFICATION URLS ====================
    path('verification/upload-documents/', views.upload_verification_documents, name='upload-documents'),
    path('verification/status/', views.verification_status, name='verification-status'),
    path('verification/history/', views.verification_history, name='verification-history'),
    path('verification/access-mode/', views.verification_access_mode, name='verification-access-mode'),



    # ==================== 🚗 VEHICLE URLS ====================
    path('vehicles/available/', views.available_vehicles, name='available-vehicles'),
    path('vehicles/nearby/', views.nearby_vehicles, name='nearby-vehicles'),
    path('vehicles/<str:vehicle_id>/', views.vehicle_detail, name='vehicle-detail'),
    path('vehicles/<str:vehicle_id>/location-history/', views.vehicle_location_history, name='vehicle-location-history'),

    # ==================== 🚲 RIDE MANAGEMENT URLS ====================
    path('rides/book/', views.book_ride, name='book-ride'),
    # path('bookings/active/', views.active_booking, name='active_booking'),
    path('rides/start/', views.start_ride, name='start-ride'),
    path('rides/end/', views.end_ride, name='end-ride'),
    path('rides/cancel/', views.cancel_booking, name='cancel_booking'),
    path('rides/<str:ride_id>/check-cancellation/', views.check_cancellation_eligibility, name='check_cancellation_eligibility'),
    path('rides/current/', views.current_ride, name='current-ride'),
    path('rides/history/', views.ride_history, name='ride-history'),
    path('rides/<int:ride_id>/', views.ride_detail, name='ride-detail'),
    path('rides/<int:ride_id>/cancel/', views.cancel_ride, name='cancel-ride'),
    path('rides/<int:ride_id>/rate/', views.rate_ride, name='rate-ride'),
    path('rides/active/', views.active_rides, name='active-rides'),
    path('rides/analytics/', views.ride_analytics, name='ride-analytics'),

    # ==================== 💰 PAYMENT & WALLET URLS ====================
    path('wallet/balance/', views.wallet_balance, name='wallet-balance'),
    path('wallet/topup/', views.add_wallet_balance, name='wallet-topup'),
    path('wallet/transactions/', views.wallet_transactions, name='wallet-transactions'),
    path('payments/process/', views.process_payment, name='process-payment'),
    path('payments/upi/', views.process_upi_payment, name='upi-payment'),
    path('payments/history/', views.payment_history, name='payment-history'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment-detail'),
    path('payments/request-refund/', views.request_refund, name='request-refund'),

    # ==================== 🚨 EMERGENCY & SAFETY URLS ====================
    path('emergency/alert/', views.emergency_alert, name='emergency-alert'),
    path('emergency/contacts/', views.emergency_contacts, name='emergency-contacts'),
    path('emergency/contacts/add/', views.add_emergency_contact, name='add-emergency-contact'),
    path('emergency/contacts/<int:contact_id>/', views.emergency_contact_detail, name='emergency-contact-detail'),
    path('emergency/contacts/<int:contact_id>/delete/', views.delete_emergency_contact, name='delete-emergency-contact'),
    path('emergency/alerts/history/', views.emergency_alerts_history, name='emergency-alerts-history'),

    # # ==================== 🧾 COMPLAINT & SUPPORT URLS ====================
    # path('complaints/create/', views.create_complaint, name='create-complaint'),
    # path('complaints/history/', views.complaints_history, name='complaints-history'),
    # path('complaints/<int:complaint_id>/', views.complaint_detail, name='complaint-detail'),

    # ==================== 🧾 COMPLAINT & SUPPORT URLS ====================
path('complaints/create/', views.create_complaint, name='create-complaint'),
path('complaints/history/', views.complaints_history, name='complaints-history'),
path('complaints/<int:complaint_id>/', views.complaint_detail, name='complaint-detail'),
path('complaints/<int:complaint_id>/update/', views.update_complaint),
path('complaints/<int:complaint_id>/delete/', views.delete_complaint),



    path("payments/create-order/", create_razorpay_order),
    path("payments/success/", razorpay_payment_success),

    # ==================== 🎯 RECOMMENDATION & FAVORITES URLS ====================
    path('recommendations/', views.get_recommendations, name='get-recommendations'),
    path('recommendations/vehicles/', views.vehicle_recommendations, name='vehicle-recommendations'),
    path('favorites/locations/', views.favorite_locations, name='favorite-locations'),
    path('favorites/locations/add/', views.add_favorite_location, name='add-favorite-location'),
    path('favorites/locations/<int:favorite_id>/', views.favorite_location_detail, name='favorite-location-detail'),
    path('favorites/locations/<int:favorite_id>/delete/', views.delete_favorite_location, name='delete-favorite-location'),
    path('favorites/vehicles/', views.favorite_vehicles, name='favorite-vehicles'),
    path('favorites/routes/', views.favorite_routes, name='favorite-routes'),
 path('favorites/', views.get_favorites, name='get-favorites'),

# ==================== 🔔 NOTIFICATION URLS (FINAL) ====================
path("notification-list/", views.notification_list, name="notification-list"),
path("notification/<int:notification_id>/", views.notification_detail, name="notification-detail"),
path("mark_notification_read/", views.mark_notification_read, name="mark-notification-read"),
path("mark_all_notifications_read/", views.mark_all_notifications_read, name="mark-all-notifications-read"),
path("unread_count/", views.unread_count, name="unread-count"),
path("unread_notifications/", views.unread_notifications, name="unread-notifications"),  # optional (returns unread list)
path("clear_all_notifications/", views.clear_all_notifications, name="clear-all-notifications"),

    # ==================== 📍 LOCATION & SERVICE URLS ====================
    path('location/check-service-area/', views.check_service_area, name='check-service-area'),
    path('location/check-eligibility/', views.check_ride_eligibility, name='check-ride-eligibility'),
    path('location/update/', views.update_user_location, name='update-user-location'),
    path('location/charging-stations/', views.nearby_charging_stations, name='nearby-charging-stations'),
    path('location/suggested-pickups/', views.suggested_pickup_locations, name='suggested-pickup-locations'),

    # ==================== 📊 ANALYTICS & HISTORY URLS ====================
    path('analytics/ride-statistics/', views.ride_statistics, name='ride-statistics'),
    path('analytics/carbon-savings/', views.carbon_savings, name='carbon-savings'),
    path('analytics/loyalty-points/', views.loyalty_points_history, name='loyalty-points-history'),
    path('analytics/login-history/', views.login_history, name='login-history'),
    path('analytics/activity-history/', views.user_activity_history, name='user-activity-history'),

    # ==================== 🧑‍💼 STAFF & SUPPORT URLS ====================
    path('staff/directory/', views.staff_directory, name='staff-directory'),
    path('staff/on-duty/', views.on_duty_staff, name='on-duty-staff'),
    path('staff/emergency-alert/', views.staff_emergency_alert, name='staff-emergency-alert'),
    path('support/contact/', views.contact_support, name='contact-support'),
    path('support/faqs/', views.faq_list, name='faq-list'),

    # ==================== ⚙️ SETTINGS & PREFERENCES URLS ====================
    path('settings/privacy/', views.privacy_settings, name='privacy-settings'),
    path('settings/notifications/', views.update_notification_settings, name='update-notification-settings'),
    path('settings/security/', views.security_settings, name='security-settings'),
    path('settings/ride-preferences/', views.ride_preferences, name='ride-preferences'),

    # ==================== 👑 ADMIN URLS ====================
    path('admin/verify-user/<int:user_id>/approve/', views.admin_approve_verification, name='admin-approve-verification'),
    path('admin/verify-user/<int:user_id>/reject/', views.admin_reject_verification, name='admin-reject-verification'),

    # ==================== 🧰 UTILITY URLS ====================
    path('health/', views.health_check, name='health-check'),
    path('app-version/', views.app_version, name='app-version'),
    path('maintenance-status/', views.maintenance_status, name='maintenance-status'),
    path('admin/clear-cache/', views.clear_cache, name='clear-cache'),

    
]

# Include router URLs (for any ViewSets in the future)
urlpatterns += router.urls
