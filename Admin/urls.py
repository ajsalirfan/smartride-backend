from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ✅ App Namespace
app_name = "Admin"

# -----------------------------
# 🔄 REST Framework Router Setup
# -----------------------------
router = DefaultRouter()

# Core Management Endpoints
router.register(r'users', views.UserManagementViewSet, basename='user-management')
router.register(r'staff', views.StaffManagementViewSet, basename='staff-management')
router.register(r'tasks', views.TaskManagementViewSet, basename='task-management')
router.register(r'vehicles', views.VehicleManagementViewSet, basename='vehicle-management')
router.register(r'rides', views.RideViewSet, basename='ride-management')
router.register(r'payments', views.PaymentViewSet, basename='payment-management')
router.register(r'complaints', views.ComplaintViewSet, basename='complaint-management')
router.register(r'maintenance', views.MaintenanceViewSet, basename='maintenance-management')
router.register(r'alerts', views.SystemAlertViewSet, basename='system-alerts')

# Analytics & Reports
router.register(r'trending-areas', views.TrendingAreaViewSet, basename='trending-areas')
router.register(r'demand-predictions', views.DemandPredictionViewSet, basename='demand-predictions')
router.register(r'rebalancing-routes', views.SmartRebalancingViewSet, basename='rebalancing-routes')
router.register(r'pricing-rules', views.DynamicPricingRuleViewSet, basename='pricing-rules')
router.register(r'maintenance-alerts', views.PredictiveMaintenanceViewSet, basename='maintenance-alerts')
router.register(r'reports', views.ReportViewSet, basename='reports')
router.register(r'dashboard-widgets', views.DashboardWidgetViewSet, basename='dashboard-widgets')
router.register(r'admin-settings', views.AdminSettingsViewSet, basename='admin-settings')

# -----------------------------
# 🌐 URL Patterns (API + HTML)
# -----------------------------
urlpatterns = [
    # ========================
    # 🔐 AUTHENTICATION
    # ========================
    path('auth/login/', views.AdminAuthenticationView.as_view(), name='admin-login'),
    path('auth/logout/', views.admin_logout, name='admin-logout'),
    path('auth/profile/', views.AdminProfileView.as_view(), name='admin-profile'),

    # ========================
    # 📊 DASHBOARD & ANALYTICS
    # ========================
    path('dashboard/api/', views.AdminDashboardView.as_view(), name='admin-dashboard-api'),  # JSON API
    path('dashboard/', views.dashboard, name='admin-dashboard'),  # HTML dashboard
    path('dashboard/quick-stats/', views.QuickStatsView.as_view(), name='quick-stats'),
    path('dashboard/analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('dashboard/recent-activity/', views.recent_activity, name='recent-activity'),

    # ========================
    # 👥 STAFF MANAGEMENT
    # ========================
    path('staff/register/', views.StaffRegistrationView.as_view(), name='staff-registration-api'),
    path('register-staff/', views.register_staff, name='register_staff'),  # HTML Form (Custom)

    # ========================
    # 📋 TASK MANAGEMENT
    # ========================
    path('tasks/assign/', views.TaskAssignmentView.as_view(), name='task-assignment'),

    # ========================
    # 🚗 VEHICLE MANAGEMENT
    # ========================
    path('vehicles/gps-monitoring/', views.GPSMonitoringView.as_view(), name='gps-monitoring'),
    path('vehicles/maintenance-schedule/', views.maintenance_schedule, name='maintenance-schedule'),

    # ========================
    # 🚘 RIDE MANAGEMENT
    # ========================
    path('rides/analytics/', views.ride_analytics_detailed, name='ride-analytics'),
    path('rides/<int:ride_id>/', views.ride_detail_view, name='ride-detail'),

    # ========================
    # 💰 PAYMENT & REVENUE
    # ========================
    path('payments/revenue-analytics/', views.revenue_analytics, name='revenue-analytics'),

    # ========================
    # 🔔 NOTIFICATION & ALERTS
    # ========================
    path('notifications/broadcast/', views.BroadcastNotificationView.as_view(), name='broadcast-notification'),
    path('notifications/emergency-alert/', views.send_emergency_alert, name='emergency-alert'),

    # ========================
    # 📈 ADVANCED ANALYTICS
    # ========================
    path('analytics/demand/', views.demand_analytics, name='demand-analytics'),
    path('analytics/user/', views.user_analytics, name='user-analytics'),
    path('analytics/advanced/', views.advanced_analytics, name='advanced-analytics'),
    path('analytics/real-time/', views.real_time_metrics, name='real-time-metrics'),

    # ========================
    # 🤖 SMART STAFFWORK
    # ========================
    path('smart-staffwork/dashboard/', views.smart_StaffWork_dashboard, name='smart-staffwork-dashboard'),

    # ========================
    # 🧾 ACTIVITY & LOGS
    # ========================
    path('activity/logs/', views.admin_activity_logs, name='admin-activity-logs'),

    # ========================
    # ⚙️ BULK OPERATIONS
    # ========================
    path('bulk/users/', views.bulk_user_action, name='bulk-user-action'),
    path('bulk/vehicles/', views.bulk_vehicle_action, name='bulk-vehicle-action'),

    # ========================
    # 📘 API DOCUMENTATION
    # ========================
    path('api-docs/', views.api_documentation, name='api-documentation'),

    # -----------------------------
    # 🔁 Include Router URLs
    # -----------------------------
    path('', include(router.urls)),
]

