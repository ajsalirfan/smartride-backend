from django.urls import path
from .enhanced_views import (
    enhanced_admin_dashboard, advanced_analytics, ai_recommendations,
    smart_rebalancing_dashboard
)

app_name = 'Admin_Enhanced'

urlpatterns = [
    path('dashboard/enhanced/', enhanced_admin_dashboard, name='enhanced-dashboard'),
    path('analytics/advanced/', advanced_analytics, name='advanced-analytics'),
    path('ai/recommendations/', ai_recommendations, name='ai-recommendations'),
    path('rebalancing/smart/', smart_rebalancing_dashboard, name='smart-rebalancing'),
]