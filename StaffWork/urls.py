# StaffWork/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

# Emergency views (new)
from .views_emergency import (
    staff_emergency_list,
    staff_emergency_detail,
    staff_update_emergency,
)

from .views import (
    StaffProfileView,
    StaffProfileUpdateView,
    StaffPasswordChangeView,
    StaffNotificationsView,
    MarkNotificationReadView,
    MarkAllNotificationsReadView,
    ClearAllNotificationsView,
)

app_name = 'StaffWork'

router = DefaultRouter()

urlpatterns = [

    # ===========================
    # ROOT
    # ===========================
    path('', views.api_root, name='api-root'),

    # ===========================
    # AUTH
    # ===========================
    path('auth/login/', views.StaffAuthenticationView.as_view(), name='staff-login'),
    path('auth/logout/', views.StaffLogoutView.as_view(), name='staff-logout'),
    path('auth/token/refresh/', views.TokenRefreshView.as_view(), name='staff-token-refresh'),
    path('auth/password/change/', views.StaffPasswordView.as_view(), name='password-change'),

    # ===========================
    # DASHBOARD
    # ===========================
    path('dashboard/', views.StaffDashboardView.as_view(), name='staff-dashboard'),
    path('dashboard/health/', views.DashboardHealthView.as_view(), name='dashboard-health'),

    # ===========================
    # TASKS
    # ===========================
    path('tasks/', views.TaskManagementView.as_view(), name='staff-tasks'),
    path('tasks/<str:task_id>/status/', views.TaskManagementView.as_view(), name='update-task-status'),
    path('tasks/<str:task_id>/attachments/', views.TaskAttachmentView.as_view(), name='task-attachments'),

    # ===========================
    # ADMIN TASK ASSIGNMENT
    # ===========================
    path('admin/tasks/', views.AdminTaskAssignmentView.as_view(), name='admin-tasks'),
    path('admin/tasks/assign/', views.AdminTaskAssignmentView.as_view(), name='admin-assign-task'),

    # ===========================
    # 🚨 STAFF EMERGENCY MODULE (NEW)
    # ===========================
    path('emergencies/', staff_emergency_list, name='staff-emergency-list'),
    path('emergencies/<int:alert_id>/', staff_emergency_detail, name='staff-emergency-detail'),
    path('emergencies/<int:alert_id>/update/', staff_update_emergency, name='staff-emergency-update'),

    # ===========================
    # REBALANCING
    # ===========================
    path('rebalancing/', views.RebalancingView.as_view(), name='rebalancing'),

    # ===========================
    # ANALYTICS
    # ===========================
    path('analytics/demand/', views.DemandAnalyticsView.as_view(), name='demand-analytics'),
    path('analytics/performance/', views.StaffAnalyticsView.as_view(), name='staff-performance'),

    # ===========================
    # VEHICLES
    # ===========================
    path('vehicles/', views.VehicleManagementView.as_view(), name='vehicle-management'),

    # ===========================
    # ISSUES
    # ===========================
    path('issues/', views.IssueResolutionView.as_view(), name='issue-resolution'),

    # ===========================
    # NOTIFICATIONS
    # ===========================
    path('notifications/', StaffNotificationsView.as_view(), name='staff-notifications'),
    path('notifications/mark-read/', MarkNotificationReadView.as_view(), name='mark-notification-read'),
    path('notifications/mark-all-read/', MarkAllNotificationsReadView.as_view(), name='mark-all-notifications-read'),
    path('notifications/clear-all/', ClearAllNotificationsView.as_view(), name='clear-all-notifications'),

    # ===========================
    # STAFF ADMIN
    # ===========================
    path('admin/staff/', views.StaffAdminView.as_view(), name='admin-staff-list'),
    path('admin/staff/register/', views.StaffRegistrationView.as_view(), name='register-staff'),

    # ===========================
    # STAFF PROFILE
    # ===========================
    path('profile/', StaffProfileView.as_view(), name="staff-profile"),
    path('profile/update/', StaffProfileUpdateView.as_view(), name="staff-profile-update"),
    path('profile/change-password/', StaffPasswordChangeView.as_view(), name="staff-password-change"),

    # ===========================
    # ALL STAFF LIST
    # ===========================
    path("all/", views.get_all_staff, name="all-staff"),
]
