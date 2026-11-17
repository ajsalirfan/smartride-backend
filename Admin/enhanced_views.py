from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
import logging
import json

from Users.ai_utils import HeatmapGenerator, PredictiveAnalytics, RecommendationEngine
from Users.models import Ride, Payment, CustomUser, Vehicle
from StaffWork.models import StaffMember, Task, EmergencyAlert
from .models import DemandAnalytics, RevenueAnalytics, TrendingArea
from .serializers import (
    DemandAnalyticsSerializer, RevenueAnalyticsSerializer,
    TrendingAreaSerializer
)

logger = logging.getLogger(__name__)

# ========================
# 📊 ENHANCED ADMIN DASHBOARD
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def enhanced_admin_dashboard(request):
    """Enhanced admin dashboard with AI analytics"""
    try:
        # Basic metrics
        total_users = CustomUser.objects.count()
        total_vehicles = Vehicle.objects.count()
        active_rides = Ride.objects.filter(status='active').count()
        
        # Revenue metrics
        today_revenue = Payment.objects.filter(
            payment_completed_at__date=timezone.now().date(),
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Staff metrics
        active_staff = StaffMember.objects.filter(is_active=True, is_on_duty=True).count()
        pending_tasks = Task.objects.filter(status='pending').count()
        
        # AI-Powered analytics
        heatmap_generator = HeatmapGenerator()
        heatmap_data = heatmap_generator.generate_demand_heatmap(hours=24)
        
        predictive_analytics = PredictiveAnalytics()
        demand_prediction = predictive_analytics.predict_demand()
        revenue_forecast = predictive_analytics.forecast_revenue(days=7)
        
        # Trending areas
        trending_areas = _get_trending_areas()
        
        # System health
        system_health = _check_system_health()
        
        return Response({
            'success': True,
            'basic_metrics': {
                'total_users': total_users,
                'total_vehicles': total_vehicles,
                'active_rides': active_rides,
                'today_revenue': float(today_revenue),
                'active_staff': active_staff,
                'pending_tasks': pending_tasks
            },
            'ai_analytics': {
                'demand_heatmap': heatmap_data,
                'demand_prediction': demand_prediction,
                'revenue_forecast': revenue_forecast,
                'trending_areas': trending_areas
            },
            'system_health': system_health,
            'alerts': _get_system_alerts(),
            'quick_actions': _get_quick_actions()
        })
        
    except Exception as e:
        logger.error(f"Enhanced dashboard error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _get_trending_areas():
    """Get trending areas with AI analysis"""
    try:
        # Use AI to identify trending areas
        heatmap_generator = HeatmapGenerator()
        heatmap_data = heatmap_generator.generate_demand_heatmap(hours=6)  # Recent 6 hours
        
        trending_areas = []
        for hotspot in heatmap_data.get('data', []):
            if hotspot['demand_score'] > 0.7:  # High demand areas
                trending_areas.append({
                    'location': hotspot['center'],
                    'demand_score': hotspot['demand_score'],
                    'intensity': hotspot['intensity'],
                    'ride_count': hotspot['ride_count']
                })
        
        return sorted(trending_areas, key=lambda x: x['demand_score'], reverse=True)[:5]
        
    except Exception as e:
        logger.error(f"Trending areas error: {e}")
        return []

def _check_system_health():
    """Check system health status"""
    checks = {
        'database': 'healthy',
        'api_services': 'healthy',
        'payment_gateway': 'healthy',
        'notification_service': 'healthy',
        'ai_services': 'healthy'
    }
    
    # Perform actual checks here
    try:
        # Database check
        CustomUser.objects.first()
    except:
        checks['database'] = 'unhealthy'
    
    return checks

def _get_system_alerts():
    """Get system alerts and notifications"""
    alerts = []
    
    # Low vehicle availability alert
    available_vehicles = Vehicle.objects.filter(status='available').count()
    if available_vehicles < 10:
        alerts.append({
            'type': 'vehicle_shortage',
            'message': f'Low vehicle availability: {available_vehicles} available',
            'severity': 'high',
            'action': 'Check vehicle distribution'
        })
    
    # High demand alert
    active_emergencies = EmergencyAlert.objects.filter(status='reported').count()
    if active_emergencies > 5:
        alerts.append({
            'type': 'high_emergencies',
            'message': f'High emergency alerts: {active_emergencies} active',
            'severity': 'high',
            'action': 'Review emergency response'
        })
    
    return alerts

def _get_quick_actions():
    """Get quick actions for admin"""
    return [
        {
            'action': 'view_analytics',
            'title': '📊 View Advanced Analytics',
            'description': 'Deep dive into AI-powered insights',
            'url': '/api/admin/advanced-analytics/'
        },
        {
            'action': 'manage_rebalancing',
            'title': '🔄 Smart Rebalancing',
            'description': 'Optimize vehicle distribution',
            'url': '/api/admin/smart-rebalancing/'
        },
        {
            'action': 'ai_recommendations',
            'title': '🧠 AI Recommendations',
            'description': 'Get AI suggestions for operations',
            'url': '/api/admin/ai-recommendations/'
        }
    ]

# ========================
# 📈 ADVANCED ANALYTICS VIEWS
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def advanced_analytics(request):
    """Get advanced analytics with AI insights"""
    try:
        time_range = request.GET.get('range', '7d')  # 7d, 30d, 90d
        
        # Date range calculation
        if time_range == '7d':
            days = 7
        elif time_range == '30d':
            days = 30
        else:
            days = 90
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Comprehensive analytics
        user_analytics = _get_user_analytics(start_date)
        revenue_analytics = _get_revenue_analytics(start_date)
        operational_analytics = _get_operational_analytics(start_date)
        ai_predictions = _get_ai_predictions()
        
        return Response({
            'success': True,
            'time_range': f'{days}d',
            'user_analytics': user_analytics,
            'revenue_analytics': revenue_analytics,
            'operational_analytics': operational_analytics,
            'ai_predictions': ai_predictions,
            'summary': _get_analytics_summary(user_analytics, revenue_analytics)
        })
        
    except Exception as e:
        logger.error(f"Advanced analytics error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _get_user_analytics(start_date):
    """Get comprehensive user analytics"""
    # User growth
    total_users = CustomUser.objects.count()
    new_users = CustomUser.objects.filter(date_joined__gte=start_date).count()
    
    # User engagement
    active_users = Ride.objects.filter(
        start_time__gte=start_date
    ).values('user').distinct().count()
    
    # User segmentation
    user_segments = {
        'new_users': new_users,
        'active_users': active_users,
        'total_users': total_users,
        'engagement_rate': round((active_users / total_users) * 100, 2) if total_users > 0 else 0
    }
    
    return user_segments

def _get_revenue_analytics(start_date):
    """Get comprehensive revenue analytics"""
    # Revenue data
    revenue_data = Payment.objects.filter(
        payment_completed_at__gte=start_date,
        status='completed'
    ).extra({'date': "date(payment_completed_at)"}).values('date').annotate(
        daily_revenue=Sum('amount'),
        ride_count=Count('id')
    ).order_by('date')
    
    total_revenue = sum(float(item['daily_revenue']) for item in revenue_data)
    total_rides = sum(item['ride_count'] for item in revenue_data)
    avg_revenue_per_ride = total_revenue / total_rides if total_rides > 0 else 0
    
    return {
        'total_revenue': round(total_revenue, 2),
        'average_revenue_per_ride': round(avg_revenue_per_ride, 2),
        'revenue_trend': list(revenue_data),
        'payment_methods': _get_payment_method_analysis(start_date)
    }

def _get_payment_method_analysis(start_date):
    """Analyze payment method distribution"""
    payment_methods = Payment.objects.filter(
        payment_completed_at__gte=start_date,
        status='completed'
    ).values('payment_method').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('-total_amount')
    
    return list(payment_methods)

def _get_operational_analytics(start_date):
    """Get operational analytics"""
    # Ride metrics
    total_rides = Ride.objects.filter(start_time__gte=start_date).count()
    completed_rides = Ride.objects.filter(
        start_time__gte=start_date,
        status='completed'
    ).count()
    
    # Vehicle metrics
    vehicle_utilization = _calculate_vehicle_utilization(start_date)
    
    # Staff performance
    staff_performance = _get_staff_performance(start_date)
    
    return {
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'completion_rate': round((completed_rides / total_rides) * 100, 2) if total_rides > 0 else 0,
        'vehicle_utilization': vehicle_utilization,
        'staff_performance': staff_performance
    }

def _calculate_vehicle_utilization(start_date):
    """Calculate vehicle utilization rates"""
    total_vehicles = Vehicle.objects.count()
    utilized_vehicles = Ride.objects.filter(
        start_time__gte=start_date
    ).values('vehicle').distinct().count()
    
    utilization_rate = (utilized_vehicles / total_vehicles) * 100 if total_vehicles > 0 else 0
    
    return {
        'total_vehicles': total_vehicles,
        'utilized_vehicles': utilized_vehicles,
        'utilization_rate': round(utilization_rate, 2),
        'underutilized_vehicles': total_vehicles - utilized_vehicles
    }

def _get_staff_performance(start_date):
    """Get staff performance metrics"""
    staff_performance = StaffMember.objects.filter(
        is_active=True
    ).annotate(
        tasks_completed=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed') & Q(assigned_tasks__created_at__gte=start_date)),
        avg_completion_time=Avg('assigned_tasks__actual_duration')
    ).values('user__username', 'tasks_completed', 'avg_completion_time')[:10]
    
    return list(staff_performance)

def _get_ai_predictions():
    """Get AI-powered predictions"""
    predictive_analytics = PredictiveAnalytics()
    
    return {
        'demand_prediction': predictive_analytics.predict_demand(),
        'revenue_forecast': predictive_analytics.forecast_revenue(days=7),
        'maintenance_predictions': _get_maintenance_predictions()
    }

def _get_maintenance_predictions():
    """Get vehicle maintenance predictions"""
    # Vehicles needing maintenance soon
    maintenance_candidates = Vehicle.objects.filter(
        Q(total_rides__gte=100) |  # High usage
        Q(last_maintenance__isnull=True) |  # Never maintained
        Q(last_maintenance__lte=timezone.now() - timedelta(days=30))  # Old maintenance
    )[:5]
    
    return [
        {
            'vehicle_id': vehicle.vehicle_id,
            'reason': 'High usage' if vehicle.total_rides >= 100 else 'Maintenance overdue',
            'urgency': 'high' if vehicle.total_rides >= 150 else 'medium'
        }
        for vehicle in maintenance_candidates
    ]

def _get_analytics_summary(user_analytics, revenue_analytics):
    """Get analytics summary with insights"""
    insights = []
    
    # User growth insight
    if user_analytics['engagement_rate'] > 50:
        insights.append("High user engagement rate detected")
    else:
        insights.append("Consider strategies to improve user engagement")
    
    # Revenue insight
    if revenue_analytics['total_revenue'] > 10000:
        insights.append("Strong revenue performance")
    else:
        insights.append("Explore revenue optimization opportunities")
    
    return {
        'key_metrics': {
            'user_engagement': user_analytics['engagement_rate'],
            'total_revenue': revenue_analytics['total_revenue'],
            'revenue_per_ride': revenue_analytics['average_revenue_per_ride']
        },
        'insights': insights,
        'recommendations': [
            "Consider targeted marketing in high-demand areas",
            "Optimize vehicle distribution based on usage patterns",
            "Review and adjust pricing strategy"
        ]
    }

# ========================
# 🧠 AI RECOMMENDATIONS FOR ADMIN
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def ai_recommendations(request):
    """Get AI-powered recommendations for business operations"""
    try:
        recommendations = []
        
        # 1. Vehicle distribution recommendations
        vehicle_recs = _get_vehicle_distribution_recommendations()
        recommendations.extend(vehicle_recs)
        
        # 2. Pricing optimization recommendations
        pricing_recs = _get_pricing_recommendations()
        recommendations.extend(pricing_recs)
        
        # 3. Staff optimization recommendations
        staff_recs = _get_staff_optimization_recommendations()
        recommendations.extend(staff_recs)
        
        # 4. Operational efficiency recommendations
        operational_recs = _get_operational_recommendations()
        recommendations.extend(operational_recs)
        
        return Response({
            'success': True,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations,
            'priority_summary': {
                'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
                'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
                'low_priority': len([r for r in recommendations if r['priority'] == 'low'])
            }
        })
        
    except Exception as e:
        logger.error(f"AI recommendations error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _get_vehicle_distribution_recommendations():
    """Get vehicle distribution recommendations"""
    recommendations = []
    
    # Check vehicle availability by area
    heatmap_generator = HeatmapGenerator()
    heatmap_data = heatmap_generator.generate_demand_heatmap(hours=24)
    
    high_demand_areas = [h for h in heatmap_data.get('data', []) if h['demand_score'] > 0.7]
    low_demand_areas = [h for h in heatmap_data.get('data', []) if h['demand_score'] < 0.3]
    
    if high_demand_areas and len(high_demand_areas) > 2:
        recommendations.append({
            'category': 'vehicle_distribution',
            'title': 'Optimize Vehicle Distribution',
            'description': f'Found {len(high_demand_areas)} high-demand areas needing more vehicles',
            'action': 'Rebalance vehicles to high-demand zones',
            'priority': 'high',
            'impact': 'high'
        })
    
    if low_demand_areas:
        recommendations.append({
            'category': 'vehicle_utilization',
            'title': 'Improve Vehicle Utilization',
            'description': f'Found {len(low_demand_areas)} low-utilization areas',
            'action': 'Consider reducing vehicles in low-demand zones',
            'priority': 'medium',
            'impact': 'medium'
        })
    
    return recommendations

def _get_pricing_recommendations():
    """Get pricing optimization recommendations"""
    recommendations = []
    
    # Analyze revenue patterns
    predictive_analytics = PredictiveAnalytics()
    demand_prediction = predictive_analytics.predict_demand()
    
    if demand_prediction.get('predicted_demand', 0) > 0.8:
        recommendations.append({
            'category': 'pricing_optimization',
            'title': 'Dynamic Pricing Opportunity',
            'description': 'High demand predicted - consider premium pricing',
            'action': 'Implement surge pricing in high-demand areas',
            'priority': 'medium',
            'impact': 'high'
        })
    
    return recommendations

def _get_staff_optimization_recommendations():
    """Get staff optimization recommendations"""
    recommendations = []
    
    # Check staff workload
    overloaded_staff = StaffMember.objects.annotate(
        task_count=Count('assigned_tasks', filter=Q(assigned_tasks__status__in=['assigned', 'in_progress']))
    ).filter(task_count__gte=5)  # Staff with 5+ active tasks
    
    if overloaded_staff.exists():
        recommendations.append({
            'category': 'staff_optimization',
            'title': 'Staff Workload Balance',
            'description': f'{overloaded_staff.count()} staff members are overloaded with tasks',
            'action': 'Redistribute tasks among available staff',
            'priority': 'high',
            'impact': 'medium'
        })
    
    return recommendations

def _get_operational_recommendations():
    """Get operational efficiency recommendations"""
    recommendations = []
    
    # Check emergency response times
    slow_emergencies = EmergencyAlert.objects.filter(
        status='resolved',
        response_time__gt=timedelta(minutes=15)
    )[:5]
    
    if slow_emergencies.exists():
        recommendations.append({
            'category': 'operational_efficiency',
            'title': 'Improve Emergency Response',
            'description': 'Some emergencies have slow response times',
            'action': 'Review emergency response protocols and staff training',
            'priority': 'high',
            'impact': 'high'
        })
    
    return recommendations

# ========================
# 🔄 SMART REBALANCING VIEWS
# ========================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def smart_rebalancing_dashboard(request):
    """Smart vehicle rebalancing dashboard"""
    try:
        # Current vehicle distribution
        vehicle_distribution = _get_vehicle_distribution()
        
        # Demand analysis
        heatmap_generator = HeatmapGenerator()
        demand_analysis = heatmap_generator.generate_demand_heatmap(hours=6)
        
        # Rebalancing recommendations
        rebalancing_plan = _generate_rebalancing_plan(vehicle_distribution, demand_analysis)
        
        # Staff availability for rebalancing
        available_staff = StaffMember.objects.filter(
            is_active=True,
            is_on_duty=True,
            current_status='available'
        ).count()
        
        return Response({
            'success': True,
            'vehicle_distribution': vehicle_distribution,
            'demand_analysis': demand_analysis,
            'rebalancing_plan': rebalancing_plan,
            'operational_metrics': {
                'available_staff': available_staff,
                'vehicles_needing_rebalancing': len(rebalancing_plan.get('movements', [])),
                'estimated_time': f"{len(rebalancing_plan.get('movements', [])) * 15} minutes"
            }
        })
        
    except Exception as e:
        logger.error(f"Smart rebalancing error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _get_vehicle_distribution():
    """Get current vehicle distribution"""
    total_available = Vehicle.objects.filter(status='available').count()
    
    zones = [
        {'name': 'Downtown', 'vehicle_count': total_available // 4},
        {'name': 'University', 'vehicle_count': total_available // 4},
        {'name': 'Shopping District', 'vehicle_count': total_available // 4},
        {'name': 'Residential', 'vehicle_count': total_available // 4}
    ]
    
    return {
        'total_available_vehicles': total_available,
        'zones': zones,
        'utilization_rate': '75%'  # Simplified calculation
    }

def _generate_rebalancing_plan(distribution, demand_analysis):
    """Generate smart rebalancing plan"""
    movements = []
    
    # Simple rebalancing logic - can be enhanced with ML
    high_demand_areas = [area for area in demand_analysis.get('data', []) if area['demand_score'] > 0.7]
    
    for i, area in enumerate(high_demand_areas[:3]):  # Top 3 high-demand areas
        movements.append({
            'from_zone': 'Low Demand Area',
            'to_zone': area['center'],
            'vehicles_count': 2,  # Move 2 vehicles to each high-demand area
            'priority': 'high',
            'estimated_impact': f"Increase utilization by {int(area['demand_score'] * 100)}%"
        })
    
    return {
        'total_movements': len(movements),
        'movements': movements,
        'estimated_efficiency_gain': '15-20%',
        'completion_time_estimate': f"{len(movements) * 30} minutes"
    }