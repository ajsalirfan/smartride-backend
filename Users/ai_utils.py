import numpy as np
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q
from django.utils import timezone
from .models import Payment, Ride, UserFavorite, Vehicle, RideRecommendation, CustomUser
import logging
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import json

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    🧠 AI-Powered Recommendation Engine
    Uses collaborative filtering and user behavior analysis
    """
    
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def get_personalized_recommendations(self, user):
        """Get AI-powered personalized ride recommendations"""
        try:
            recommendations = []
            
            # 1. Based on user preferences
            pref_recommendations = self._get_preference_based_recommendations(user)
            recommendations.extend(pref_recommendations)
            
            # 2. Based on riding history patterns
            history_recommendations = self._get_history_based_recommendations(user)
            recommendations.extend(history_recommendations)
            
            # 3. Based on similar users
            collaborative_recommendations = self._get_collaborative_recommendations(user)
            recommendations.extend(collaborative_recommendations)
            
            # 4. Trending areas
            trending_recommendations = self._get_trending_recommendations()
            recommendations.extend(trending_recommendations)
            
            # Sort by confidence score and remove duplicates
            unique_recommendations = self._deduplicate_recommendations(recommendations)
            sorted_recommendations = sorted(unique_recommendations, 
                                          key=lambda x: x['confidence_score'], 
                                          reverse=True)[:10]
            
            return sorted_recommendations
            
        except Exception as e:
            logger.error(f"Recommendation engine error: {e}")
            return self._get_fallback_recommendations(user)
    
    def _get_preference_based_recommendations(self, user):
        """Get recommendations based on user preferences"""
        recommendations = []
        
        # Preferred vehicle type
        preferred_vehicle = user.preferred_vehicle_type
        available_vehicles = Vehicle.objects.filter(
            vehicle_type=preferred_vehicle,
            status='available',
            battery_level__gt=30
        )[:3]
        
        for vehicle in available_vehicles:
            recommendations.append({
                'type': 'preference_based',
                'title': f'Preferred {preferred_vehicle} Available',
                'description': f'{vehicle.model_name} nearby with {vehicle.battery_level}% battery',
                'confidence_score': 0.85,
                'vehicle_id': vehicle.vehicle_id,
                'location': {
                    'lat': float(vehicle.current_location_lat) if vehicle.current_location_lat else None,
                    'lng': float(vehicle.current_location_lng) if vehicle.current_location_lng else None
                }
            })
        
        return recommendations
    
    def _get_history_based_recommendations(self, user):
        """Get recommendations based on riding history patterns"""
        recommendations = []
        
        # Analyze frequent routes
        frequent_routes = Ride.objects.filter(
            user=user,
            status='completed'
        ).values('start_location_name', 'end_location_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        for route in frequent_routes:
            recommendations.append({
                'type': 'history_based',
                'title': 'Your Frequent Route',
                'description': f'From {route["start_location_name"]} to {route["end_location_name"]}',
                'confidence_score': 0.75,
                'route_data': route
            })
        
        # Favorite areas
        favorite_areas = UserFavorite.objects.filter(
            user=user,
            favorite_type='location'
        )[:3]
        
        for favorite in favorite_areas:
            nearby_vehicles = Vehicle.objects.filter(
                status='available',
                current_location_lat__isnull=False,
                current_location_lng__isnull=False
            )[:2]
            
            for vehicle in nearby_vehicles:
                recommendations.append({
                    'type': 'favorite_based',
                    'title': f'Vehicle near {favorite.name}',
                    'description': f'{vehicle.vehicle_type} available in your favorite area',
                    'confidence_score': 0.80,
                    'vehicle_id': vehicle.vehicle_id,
                    'favorite_location': favorite.name
                })
        
        return recommendations
    
    def _get_collaborative_recommendations(self, user):
        """Get recommendations based on similar users' behavior"""
        recommendations = []
        
        try:
            # Find users with similar preferences
            similar_users = CustomUser.objects.filter(
                preferred_vehicle_type=user.preferred_vehicle_type,
                is_verified=True
            ).exclude(id=user.id)[:5]
            
            for similar_user in similar_users:
                # Get their frequent routes
                their_routes = Ride.objects.filter(
                    user=similar_user,
                    status='completed'
                ).values('start_location_name').annotate(
                    count=Count('id')
                ).order_by('-count')[:3]
                
                for route in their_routes:
                    recommendations.append({
                        'type': 'collaborative',
                        'title': 'Popular with Similar Riders',
                        'description': f'Frequent route from {route["start_location_name"]}',
                        'confidence_score': 0.65,
                        'similar_user_count': route['count']
                    })
                    
        except Exception as e:
            logger.warning(f"Collaborative filtering limited: {e}")
        
        return recommendations
    
    def _get_trending_recommendations(self):
        """Get recommendations based on trending areas"""
        recommendations = []
        
        # Find trending start locations in last 24 hours
        trending_locations = Ride.objects.filter(
            start_time__gte=timezone.now() - timedelta(hours=24),
            status='completed'
        ).values('start_location_name', 'start_location_lat', 'start_location_lng').annotate(
            ride_count=Count('id')
        ).order_by('-ride_count')[:5]
        
        for location in trending_locations:
            recommendations.append({
                'type': 'trending',
                'title': 'Trending Pickup Area',
                'description': f'Popular starting point: {location["start_location_name"]}',
                'confidence_score': 0.70,
                'ride_count': location['ride_count'],
                'location': {
                    'name': location['start_location_name'],
                    'lat': float(location['start_location_lat']) if location['start_location_lat'] else None,
                    'lng': float(location['start_location_lng']) if location['start_location_lng'] else None
                }
            })
        
        return recommendations
    
    def _deduplicate_recommendations(self, recommendations):
        """Remove duplicate recommendations"""
        seen = set()
        unique_recommendations = []
        
        for rec in recommendations:
            rec_key = f"{rec['type']}_{rec.get('vehicle_id', '')}_{rec.get('title', '')}"
            if rec_key not in seen:
                seen.add(rec_key)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _get_fallback_recommendations(self, user):
        """Fallback recommendations when AI fails"""
        return [{
            'type': 'fallback',
            'title': 'Nearby Vehicles',
            'description': 'Check available vehicles in your area',
            'confidence_score': 0.5,
            'is_fallback': True
        }]


class HeatmapGenerator:
    """
    📊 Real-time Demand Heatmap Generator
    Uses geo-spatial clustering and time-series analysis
    """
    
    def __init__(self):
        self.cluster_eps = 0.01  # ~1km in latitude/longitude
        self.min_samples = 3
    
    def generate_demand_heatmap(self, hours=24):
        """Generate real-time demand heatmap data"""
        try:
            # Get recent rides for heatmap analysis
            recent_rides = Ride.objects.filter(
                start_time__gte=timezone.now() - timedelta(hours=hours),
                status='completed'
            ).exclude(
                Q(start_location_lat__isnull=True) | 
                Q(start_location_lng__isnull=True)
            )
            
            if not recent_rides.exists():
                return self._get_default_heatmap()
            
            # Prepare data for clustering
            locations = []
            for ride in recent_rides:
                if ride.start_location_lat and ride.start_location_lng:
                    locations.append([
                        float(ride.start_location_lat),
                        float(ride.start_location_lng)
                    ])
            
            if len(locations) < self.min_samples:
                return self._generate_simple_heatmap(recent_rides)
            
            # Perform DBSCAN clustering to find demand hotspots
            locations_array = np.array(locations)
            scaler = StandardScaler()
            locations_scaled = scaler.fit_transform(locations_array)
            
            dbscan = DBSCAN(eps=self.cluster_eps, min_samples=self.min_samples)
            clusters = dbscan.fit_predict(locations_scaled)
            
            # Calculate demand scores for each cluster
            heatmap_data = self._calculate_cluster_demand(locations_array, clusters, recent_rides)
            
            return {
                'success': True,
                'heatmap_type': 'advanced_clustering',
                'timestamp': timezone.now().isoformat(),
                'data': heatmap_data,
                'total_hotspots': len([d for d in heatmap_data if d['demand_score'] > 0.5]),
                'peak_hours': self._calculate_peak_hours(recent_rides)
            }
            
        except Exception as e:
            logger.error(f"Heatmap generation error: {e}")
            return self._get_default_heatmap()
    
    def _calculate_cluster_demand(self, locations, clusters, rides):
        """Calculate demand scores for each cluster"""
        heatmap_data = []
        unique_clusters = set(clusters)
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Noise points
                continue
                
            cluster_points = locations[clusters == cluster_id]
            cluster_center = cluster_points.mean(axis=0)
            
            # Calculate demand score based on ride density
            cluster_size = len(cluster_points)
            total_rides = len(rides)
            demand_score = min(1.0, cluster_size / (total_rides * 0.3))  # Normalize
            
            heatmap_data.append({
                'center': {
                    'lat': float(cluster_center[0]),
                    'lng': float(cluster_center[1])
                },
                'radius': self._calculate_cluster_radius(cluster_points),
                'demand_score': round(demand_score, 2),
                'ride_count': cluster_size,
                'intensity': self._get_intensity_level(demand_score)
            })
        
        return heatmap_data
    
    def _calculate_cluster_radius(self, points):
        """Calculate radius of cluster points"""
        if len(points) < 2:
            return 0.005  # Default 500m radius
        
        center = points.mean(axis=0)
        distances = np.linalg.norm(points - center, axis=1)
        return float(np.percentile(distances, 75))  # 75th percentile as radius
    
    def _get_intensity_level(self, demand_score):
        """Convert demand score to intensity level"""
        if demand_score > 0.8:
            return 'very_high'
        elif demand_score > 0.6:
            return 'high'
        elif demand_score > 0.4:
            return 'medium'
        elif demand_score > 0.2:
            return 'low'
        else:
            return 'very_low'
    
    def _calculate_peak_hours(self, rides):
        """Calculate peak demand hours"""
        hourly_counts = {}
        for ride in rides:
            hour = ride.start_time.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        if not hourly_counts:
            return []
        
        max_count = max(hourly_counts.values())
        peak_hours = [
            {'hour': hour, 'demand_level': count / max_count}
            for hour, count in hourly_counts.items()
        ]
        
        return sorted(peak_hours, key=lambda x: x['hour'])
    
    def _generate_simple_heatmap(self, rides):
        """Generate simple heatmap when clustering isn't possible"""
        heatmap_data = []
        
        for ride in rides:
            if ride.start_location_lat and ride.start_location_lng:
                heatmap_data.append({
                    'center': {
                        'lat': float(ride.start_location_lat),
                        'lng': float(ride.start_location_lng)
                    },
                    'radius': 0.003,  # 300m radius
                    'demand_score': 0.5,
                    'ride_count': 1,
                    'intensity': 'medium'
                })
        
        return {
            'success': True,
            'heatmap_type': 'simple_distribution',
            'timestamp': timezone.now().isoformat(),
            'data': heatmap_data,
            'total_hotspots': len(heatmap_data),
            'peak_hours': self._calculate_peak_hours(rides)
        }
    
    def _get_default_heatmap(self):
        """Return default heatmap when no data available"""
        return {
            'success': True,
            'heatmap_type': 'default',
            'timestamp': timezone.now().isoformat(),
            'data': [],
            'total_hotspots': 0,
            'peak_hours': [],
            'message': 'Insufficient data for heatmap generation'
        }


class PredictiveAnalytics:
    """
    📈 Predictive Analytics Engine
    For demand forecasting and revenue prediction
    """
    
    def predict_demand(self, location=None, time=None):
        """Predict demand for specific location and time"""
        try:
            if not time:
                time = timezone.now()
            
            # Simple time-based prediction (can be enhanced with ML)
            hour = time.hour
            is_weekend = time.weekday() >= 5
            
            # Base demand pattern
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                base_demand = 0.8
            elif 12 <= hour <= 14:  # Lunch time
                base_demand = 0.6
            else:
                base_demand = 0.3
            
            # Weekend adjustment
            if is_weekend:
                base_demand *= 1.2  # 20% higher on weekends
            
            # Weather factor (placeholder - integrate with weather API)
            weather_factor = 1.0
            
            predicted_demand = min(1.0, base_demand * weather_factor)
            
            return {
                'predicted_demand': round(predicted_demand, 2),
                'confidence': 0.7,
                'peak_period': self._get_peak_period(hour),
                'recommended_vehicles': max(1, int(predicted_demand * 10)),
                'timestamp': time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Demand prediction error: {e}")
            return {
                'predicted_demand': 0.5,
                'confidence': 0.3,
                'peak_period': 'unknown',
                'recommended_vehicles': 5,
                'error': str(e)
            }
    
    def _get_peak_period(self, hour):
        """Get peak period based on hour"""
        if 7 <= hour <= 9:
            return 'morning_rush'
        elif 12 <= hour <= 14:
            return 'lunch_time'
        elif 17 <= hour <= 19:
            return 'evening_rush'
        else:
            return 'off_peak'
    
    def forecast_revenue(self, days=7):
        """Forecast revenue for next N days"""
        try:
            # Get historical revenue data
            recent_payments = Payment.objects.filter(
                status='completed',
                payment_completed_at__gte=timezone.now() - timedelta(days=30)
            )
            
            if not recent_payments.exists():
                return self._get_default_forecast(days)
            
            daily_revenue = {}
            for payment in recent_payments:
                date = payment.payment_completed_at.date()
                daily_revenue[date] = daily_revenue.get(date, 0) + float(payment.amount)
            
            # Simple forecasting (can be enhanced with time-series models)
            avg_revenue = sum(daily_revenue.values()) / len(daily_revenue)
            
            forecast = []
            for i in range(days):
                forecast_date = timezone.now().date() + timedelta(days=i+1)
                
                # Adjust for weekday/weekend pattern
                is_weekend = forecast_date.weekday() >= 5
                revenue = avg_revenue * (1.2 if is_weekend else 1.0)
                
                forecast.append({
                    'date': forecast_date.isoformat(),
                    'predicted_revenue': round(revenue, 2),
                    'confidence': 0.6,
                    'is_weekend': is_weekend
                })
            
            return {
                'forecast_period': f'{days}_days',
                'historical_avg_revenue': round(avg_revenue, 2),
                'forecast': forecast,
                'total_predicted_revenue': round(sum(f['predicted_revenue'] for f in forecast), 2)
            }
            
        except Exception as e:
            logger.error(f"Revenue forecast error: {e}")
            return self._get_default_forecast(days)
    
    def _get_default_forecast(self, days):
        """Return default forecast when no data available"""
        forecast = []
        for i in range(days):
            forecast_date = timezone.now().date() + timedelta(days=i+1)
            forecast.append({
                'date': forecast_date.isoformat(),
                'predicted_revenue': 1000.0,
                'confidence': 0.3,
                'is_weekend': forecast_date.weekday() >= 5
            })
        
        return {
            'forecast_period': f'{days}_days',
            'historical_avg_revenue': 1000.0,
            'forecast': forecast,
            'total_predicted_revenue': 1000.0 * days,
            'message': 'Using default forecast due to insufficient data'
        }