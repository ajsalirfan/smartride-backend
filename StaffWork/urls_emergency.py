from django.urls import path
from .views_emergency import (
    staff_emergency_list,
    staff_emergency_detail,
    staff_update_emergency
)

urlpatterns = [
    path('emergencies/', staff_emergency_list, name='staff-emergency-list'),
    path('emergencies/<int:alert_id>/', staff_emergency_detail, name='staff-emergency-detail'),
    path('emergencies/<int:alert_id>/update/', staff_update_emergency, name='staff-emergency-update'),
]
