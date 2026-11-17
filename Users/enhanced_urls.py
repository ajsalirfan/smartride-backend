from django.urls import path
from .enhanced_views import (
    get_ai_recommendations, get_smart_recommendations, get_demand_heatmap,
    get_interactive_heatmap, get_demand_prediction, get_revenue_forecast,
    get_enhanced_profile, get_user_analytics
)

app_name = 'Users_Enhanced'

urlpatterns = [
    # AI Recommendation Endpoints
    path('ai/recommendations/', get_ai_recommendations, name='ai-recommendations'),
    path('ai/smart-recommendations/', get_smart_recommendations, name='smart-recommendations'),
    
    # Heatmap & Analytics Endpoints
    path('analytics/demand-heatmap/', get_demand_heatmap, name='demand-heatmap'),
    path('analytics/interactive-heatmap/', get_interactive_heatmap, name='interactive-heatmap'),
    path('analytics/demand-prediction/', get_demand_prediction, name='demand-prediction'),
    path('analytics/revenue-forecast/', get_revenue_forecast, name='revenue-forecast'),
    
    # Enhanced User Profile
    path('profile/enhanced/', get_enhanced_profile, name='enhanced-profile'),
    path('analytics/user-insights/', get_user_analytics, name='user-analytics'),
]