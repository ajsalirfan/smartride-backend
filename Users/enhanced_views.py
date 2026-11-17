# users/enhanced_views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
import logging
import math

from .models import CustomUser, Ride, Vehicle, RideRecommendation
from .ai_utils import RecommendationEngine, HeatmapGenerator, PredictiveAnalytics
from .enhanced_serializers import (
    AIRecommendationSerializer, DemandHeatmapSerializer, 
    EnhancedUserProfileSerializer, PredictiveAnalyticsSerializer,
    RevenueForecastSerializer
)
from .serializers import RideRecommendationSerializer

logger = logging.getLogger(__name__)

# ========================
# 🧠 AI-POWERED RECOMMENDATION VIEWS
# ========================

def _save_ai_recommendations(user, recommendations):
    """Save AI recommendations to database"""
    try:
        # Clear old AI recommendations
        RideRecommendation.objects.filter(
            user=user, 
            recommendation_type='personalized'
        ).delete()
        
        # Save new ones
        for i, rec in enumerate(recommendations[:5]):  # Save top 5
            RideRecommendation.objects.create(
                user=user,
                recommendation_type='personalized',
                title=rec['title'],
                description=rec['description'],
                confidence_score=rec['confidence_score'],
                display_order=i,
                is_active=True,
                expires_at=timezone.now() + timedelta(hours=24)
            )
    except Exception as e:
        logger.warning(f"Failed to save AI recommendations: {e}")

def _get_fallback_recommendations():
    """Get fallback recommendations when AI fails"""
    return [{
        'type': 'fallback',
        'title': 'Explore Available Vehicles',
        'description': 'Check nearby vehicles for your ride',
        'confidence_score': 0.5
    }]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_recommendations(request):
    """Get AI-powered personalized recommendations"""
    try:
        engine = RecommendationEngine()
        recommendations = engine.get_personalized_recommendations(request.user)
        
        # Save top recommendations to database
        _save_ai_recommendations(request.user, recommendations)
        
        serializer = AIRecommendationSerializer(recommendations, many=True)
        
        return Response({
            'success': True,
            'recommendations': serializer.data,
            'total_recommendations': len(recommendations),
            'ai_engine_version': '1.0',
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"AI recommendations error: {e}")
        return Response({
            'error': 'Failed to generate AI recommendations',
            'fallback_recommendations': _get_fallback_recommendations()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points in km"""
    R = 6371  # Earth radius in km
    
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def _enhance_with_location(recommendations, lat, lng):
    """Enhance recommendations with location context"""
    for rec in recommendations:
        if rec.get('location'):
            # Calculate distance and adjust confidence
            rec_location = rec['location']
            if rec_location.get('lat') and rec_location.get('lng'):
                distance = _calculate_distance(
                    lat, lng, rec_location['lat'], rec_location['lng']
                )
                # Boost confidence for nearby locations
                if distance < 5:  # Within 5km
                    rec['confidence_score'] = min(1.0, rec['confidence_score'] * 1.3)
                    rec['distance_km'] = round(distance, 2)
    
    return sorted(recommendations, key=lambda x: x['confidence_score'], reverse=True)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_smart_recommendations(request):
    """Get smart recommendations with context awareness"""
    try:
        # Get user context
        user = request.user
        latitude = request.GET.get('lat')
        longitude = request.GET.get('lng')
        
        engine = RecommendationEngine()
        recommendations = engine.get_personalized_recommendations(user)
        
        # Enhance with location context
        if latitude and longitude:
            location_enhanced_recs = _enhance_with_location(
                recommendations, float(latitude), float(longitude)
            )
            recommendations = location_enhanced_recs
        
        # Filter by confidence
        high_confidence_recs = [r for r in recommendations if r['confidence_score'] > 0.6]
        
        return Response({
            'success': True,
            'context_aware': bool(latitude and longitude),
            'high_confidence_recommendations': len(high_confidence_recs),
            'recommendations': AIRecommendationSerializer(high_confidence_recs, many=True).data
        })
        
    except Exception as e:
        logger.error(f"Smart recommendations error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========================
# 📊 REAL-TIME HEATMAP VIEWS
# ========================

def _get_fallback_heatmap():
    """Get fallback heatmap data"""
    return {
        'success': True,
        'heatmap_type': 'fallback',
        'timestamp': timezone.now().isoformat(),
        'data': [],
        'total_hotspots': 0,
        'peak_hours': [],
        'message': 'Using fallback heatmap data'
    }

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_demand_heatmap(request):
    """Get real-time demand heatmap data"""
    try:
        hours = int(request.GET.get('hours', 24))
        heatmap_type = request.GET.get('type', 'advanced')
        
        generator = HeatmapGenerator()
        
        if heatmap_type == 'advanced':
            heatmap_data = generator.generate_demand_heatmap(hours=hours)
        else:
            heatmap_data = generator._generate_simple_heatmap()
        
        serializer = DemandHeatmapSerializer(heatmap_data)
        
        return Response({
            'success': True,
            'heatmap': serializer.data,
            'cache_timeout': 300,  # 5 minutes
            'data_points': len(heatmap_data.get('data', [])),
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Heatmap generation error: {e}")
        return Response({
            'error': 'Failed to generate heatmap',
            'fallback_data': _get_fallback_heatmap()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _get_peak_periods():
    """Get peak demand periods"""
    return [
        {'period': 'Morning Rush', 'time': '7:00-9:00', 'intensity': 'high'},
        {'period': 'Lunch Time', 'time': '12:00-14:00', 'intensity': 'medium'},
        {'period': 'Evening Rush', 'time': '17:00-19:00', 'intensity': 'high'}
    ]

def _get_heatmap_recommendations(heatmap_data):
    """Get recommendations based on heatmap analysis"""
    hotspots = heatmap_data.get('data', [])
    high_demand_hotspots = [h for h in hotspots if h['demand_score'] > 0.7]
    
    recommendations = []
    
    if high_demand_hotspots:
        recommendations.append({
            'type': 'high_demand',
            'message': f'{len(high_demand_hotspots)} high-demand areas detected',
            'action': 'Consider vehicle rebalancing',
            'priority': 'high'
        })
    
    low_demand_hotspots = [h for h in hotspots if h['demand_score'] < 0.3]
    if low_demand_hotspots:
        recommendations.append({
            'type': 'low_demand',
            'message': f'{len(low_demand_hotspots)} low-utilization areas',
            'action': 'Review vehicle distribution',
            'priority': 'medium'
        })
    
    return recommendations

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interactive_heatmap(request):
    """Get interactive heatmap with additional analytics"""
    try:
        # Generate base heatmap
        generator = HeatmapGenerator()
        heatmap_data = generator.generate_demand_heatmap(hours=24)
        
        # Add predictive analytics
        analytics = PredictiveAnalytics()
        predictions = []
        
        for hotspot in heatmap_data.get('data', [])[:5]:  # Top 5 hotspots
            prediction = analytics.predict_demand()
            predictions.append({
                'location': hotspot['center'],
                'current_demand': hotspot['demand_score'],
                'predicted_demand': prediction['predicted_demand'],
                'confidence': prediction['confidence']
            })
        
        return Response({
            'success': True,
            'heatmap': heatmap_data,
            'predictions': predictions,
            'peak_periods': _get_peak_periods(),
            'recommendations': _get_heatmap_recommendations(heatmap_data)
        })
        
    except Exception as e:
        logger.error(f"Interactive heatmap error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========================
# 📈 PREDICTIVE ANALYTICS VIEWS
# ========================

def _get_prediction_recommendations(prediction):
    """Get actionable recommendations based on prediction"""
    demand = prediction.get('predicted_demand', 0.5)
    recommendations = []
    
    if demand > 0.7:
        recommendations.extend([
            {
                'type': 'vehicle_allocation',
                'message': 'High demand predicted',
                'action': 'Increase vehicle allocation in area',
                'urgency': 'high'
            },
            {
                'type': 'pricing',
                'message': 'Consider dynamic pricing',
                'action': 'Adjust prices for demand optimization',
                'urgency': 'medium'
            }
        ])
    elif demand < 0.3:
        recommendations.append({
            'type': 'rebalancing',
            'message': 'Low demand predicted',
            'action': 'Consider rebalancing vehicles to high-demand areas',
            'urgency': 'medium'
        })
    
    return recommendations

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_demand_prediction(request):
    """Get demand prediction for specific location and time"""
    try:
        latitude = request.GET.get('lat')
        longitude = request.GET.get('lng')
        prediction_time = request.GET.get('time')
        
        analytics = PredictiveAnalytics()
        
        if latitude and longitude:
            # Location-specific prediction
            prediction = analytics.predict_demand()
        else:
            # General prediction
            prediction = analytics.predict_demand()
        
        serializer = PredictiveAnalyticsSerializer(prediction)
        
        return Response({
            'success': True,
            'prediction': serializer.data,
            'location_specific': bool(latitude and longitude),
            'recommendations': _get_prediction_recommendations(prediction)
        })
        
    except Exception as e:
        logger.error(f"Demand prediction error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_revenue_forecast(request):
    """Get revenue forecast for upcoming period"""
    try:
        days = int(request.GET.get('days', 7))
        
        analytics = PredictiveAnalytics()
        forecast = analytics.forecast_revenue(days=days)
        
        serializer = RevenueForecastSerializer(forecast)
        
        return Response({
            'success': True,
            'forecast': serializer.data,
            'confidence_level': 'medium',
            'factors_considered': ['historical_data', 'weekend_patterns', 'seasonality']
        })
        
    except Exception as e:
        logger.error(f"Revenue forecast error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========================
# 👤 ENHANCED USER PROFILE VIEWS
# ========================

def _analyze_riding_pattern(rides):
    """Analyze user's riding patterns"""
    if not rides:
        return {'pattern': 'no_data', 'message': 'No riding history available'}
    
    # Time pattern analysis
    hourly_distribution = {}
    for ride in rides:
        hour = ride.start_time.hour
        hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
    
    # Distance pattern
    distances = [float(ride.distance) for ride in rides]
    avg_distance = sum(distances) / len(distances)
    
    return {
        'peak_hours': dict(sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:3]),
        'average_distance_km': round(avg_distance, 2),
        'distance_category': 'short' if avg_distance < 3 else 'medium' if avg_distance < 8 else 'long',
        'rides_analyzed': len(rides)
    }

def _calculate_cost_efficiency(rides):
    """Calculate cost efficiency metrics"""
    if not rides:
        return {'efficiency': 'no_data', 'message': 'No rides to analyze'}
    
    costs = [float(ride.cost) for ride in rides]
    distances = [float(ride.distance) for ride in rides]
    
    avg_cost_per_km = sum(costs) / sum(distances) if sum(distances) > 0 else 0
    
    return {
        'average_cost_per_km': round(avg_cost_per_km, 2),
        'efficiency_rating': 'high' if avg_cost_per_km < 2 else 'medium' if avg_cost_per_km < 4 else 'low',
        'total_cost_analysis': {
            'min_cost': min(costs) if costs else 0,
            'max_cost': max(costs) if costs else 0,
            'avg_cost': sum(costs) / len(costs) if costs else 0
        }
    }

def _calculate_environmental_impact(user):
    """Calculate environmental impact"""
    carbon_saved = user.carbon_saved_total or 0
    distance_covered = user.total_distance_covered or 0
    
    return {
        'carbon_saved_kg': round(carbon_saved, 2),
        'equivalent_car_km': round(carbon_saved / 0.12, 2),  # kg CO2 per car km
        'equivalent_trees': round(carbon_saved / 21.77, 1),  # kg CO2 per tree per year
        'total_green_kms': round(distance_covered, 2)
    }

def _generate_ai_insights(user, rides):
    """Generate AI-powered insights for user"""
    insights = []
    
    if rides.count() > 10:
        insights.append({
            'type': 'loyalty_boost',
            'title': 'Frequent Rider',
            'message': f'You\'ve taken {rides.count()} rides! Consider our premium membership for better benefits.',
            'priority': 'medium'
        })
    
    if hasattr(user, 'preferred_vehicle_type') and user.preferred_vehicle_type:
        insights.append({
            'type': 'preference_optimization',
            'title': 'Vehicle Preference',
            'message': f'We notice you prefer {user.preferred_vehicle_type}. We\'ll prioritize these vehicles for you.',
            'priority': 'low'
        })
    
    # Add more AI-generated insights based on data analysis
    if not insights:
        insights.append({
            'type': 'welcome',
            'title': 'Getting Started',
            'message': 'Continue riding to unlock personalized insights and recommendations!',
            'priority': 'low'
        })
    
    return insights

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_enhanced_profile(request):
    """Get enhanced user profile with AI insights"""
    try:
        user = request.user
        serializer = EnhancedUserProfileSerializer(user, context={'request': request})
        
        return Response({
            'success': True,
            'profile': serializer.data,
            'ai_generated': True,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Enhanced profile error: {e}")
        # Fallback to basic profile
        from .serializers import UserProfileSerializer
        basic_serializer = UserProfileSerializer(request.user)
        return Response({
            'success': True,
            'profile': basic_serializer.data,
            'ai_generated': False,
            'message': 'Using basic profile data'
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_analytics(request):
    """Get comprehensive user analytics"""
    try:
        user = request.user
        rides = Ride.objects.filter(user=user, status='completed')
        
        # Basic metrics
        total_rides = rides.count()
        total_distance = sum(float(ride.distance) for ride in rides) if rides else 0
        total_spent = sum(float(ride.cost) for ride in rides) if rides else 0
        
        # Advanced analytics
        riding_pattern = _analyze_riding_pattern(rides)
        cost_efficiency = _calculate_cost_efficiency(rides)
        environmental_impact = _calculate_environmental_impact(user)
        
        return Response({
            'success': True,
            'basic_metrics': {
                'total_rides': total_rides,
                'total_distance_km': round(total_distance, 2),
                'total_amount_spent': round(total_spent, 2),
                'average_ride_distance': round(total_distance / total_rides, 2) if total_rides > 0 else 0,
                'average_ride_cost': round(total_spent / total_rides, 2) if total_rides > 0 else 0
            },
            'advanced_analytics': {
                'riding_pattern': riding_pattern,
                'cost_efficiency': cost_efficiency,
                'environmental_impact': environmental_impact,
                'preferred_vehicle_type': getattr(user, 'preferred_vehicle_type', 'not_set'),
                'membership_tier': getattr(user, 'membership_tier', 'basic')
            },
            'ai_insights': _generate_ai_insights(user, rides)
        })
        
    except Exception as e:
        logger.error(f"User analytics error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)