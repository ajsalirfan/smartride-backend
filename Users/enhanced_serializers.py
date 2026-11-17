from rest_framework import serializers
from .models import CustomUser, Ride, Vehicle, RideRecommendation
from .ai_utils import RecommendationEngine, HeatmapGenerator, PredictiveAnalytics

class EnhancedRideRecommendationSerializer(serializers.ModelSerializer):
    vehicles = serializers.SerializerMethodField()
    ai_confidence = serializers.SerializerMethodField()
    recommendation_engine = serializers.SerializerMethodField()
    
    class Meta:
        model = RideRecommendation
        fields = [
            'id', 'recommendation_type', 'title', 'description',
            'confidence_score', 'vehicles', 'ai_confidence', 
            'recommendation_engine', 'display_order', 'expires_at'
        ]
    
    def get_vehicles(self, obj):
        from .serializers import VehicleSerializer
        return VehicleSerializer(obj.vehicles.all()[:5], many=True).data
    
    def get_ai_confidence(self, obj):
        # Enhance confidence score with AI analysis
        engine = RecommendationEngine()
        user = self.context.get('request').user if self.context.get('request') else None
        
        if user and obj.recommendation_type == 'personalized':
            # Boost score for personalized recommendations
            return min(1.0, obj.confidence_score * 1.2)
        return obj.confidence_score
    
    def get_recommendation_engine(self, obj):
        return "AI_Enhanced" if obj.recommendation_type == 'personalized' else "Basic"

class AIRecommendationSerializer(serializers.Serializer):
    """Serializer for AI-generated recommendations"""
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    confidence_score = serializers.FloatField()
    vehicle_id = serializers.CharField(required=False, allow_null=True)
    location = serializers.DictField(required=False)
    route_data = serializers.DictField(required=False)
    similar_user_count = serializers.IntegerField(required=False)
    ride_count = serializers.IntegerField(required=False)
    is_fallback = serializers.BooleanField(default=False)

class HeatmapDataSerializer(serializers.Serializer):
    """Serializer for heatmap data"""
    center = serializers.DictField()
    radius = serializers.FloatField()
    demand_score = serializers.FloatField()
    ride_count = serializers.IntegerField()
    intensity = serializers.CharField()

class DemandHeatmapSerializer(serializers.Serializer):
    """Serializer for complete heatmap response"""
    success = serializers.BooleanField()
    heatmap_type = serializers.CharField()
    timestamp = serializers.DateTimeField()
    data = HeatmapDataSerializer(many=True)
    total_hotspots = serializers.IntegerField()
    peak_hours = serializers.ListField()

class PredictiveAnalyticsSerializer(serializers.Serializer):
    """Serializer for predictive analytics results"""
    predicted_demand = serializers.FloatField()
    confidence = serializers.FloatField()
    peak_period = serializers.CharField()
    recommended_vehicles = serializers.IntegerField()
    timestamp = serializers.DateTimeField()

class RevenueForecastSerializer(serializers.Serializer):
    """Serializer for revenue forecasting"""
    forecast_period = serializers.CharField()
    historical_avg_revenue = serializers.FloatField()
    forecast = serializers.ListField()
    total_predicted_revenue = serializers.FloatField()

class EnhancedUserProfileSerializer(serializers.ModelSerializer):
    """Enhanced user profile with AI insights"""
    ai_insights = serializers.SerializerMethodField()
    recommended_vehicles = serializers.SerializerMethodField()
    demand_forecast = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'preferred_vehicle_type', 'is_verified',
            'total_rides_count', 'total_distance_covered', 'carbon_saved_total',
            'loyalty_points', 'membership_tier', 'ai_insights',
            'recommended_vehicles', 'demand_forecast'
        ]
    
    def get_ai_insights(self, obj):
        """Get AI-powered insights for user"""
        analytics = PredictiveAnalytics()
        demand_prediction = analytics.predict_demand()
        
        return {
            'riding_pattern': self._analyze_riding_pattern(obj),
            'preferred_times': self._get_preferred_times(obj),
            'demand_prediction': demand_prediction,
            'savings_impact': self._calculate_savings_impact(obj)
        }
    
    def get_recommended_vehicles(self, obj):
        """Get AI-recommended vehicles"""
        engine = RecommendationEngine()
        recommendations = engine.get_personalized_recommendations(obj)
        
        # Filter to only vehicle recommendations
        vehicle_recommendations = [
            rec for rec in recommendations 
            if rec.get('vehicle_id') and rec['confidence_score'] > 0.6
        ][:3]
        
        return vehicle_recommendations
    
    def get_demand_forecast(self, obj):
        """Get demand forecast for user's common areas"""
        analytics = PredictiveAnalytics()
        return analytics.forecast_revenue(days=3)
    
    def _analyze_riding_pattern(self, user):
        """Analyze user's riding patterns"""
        recent_rides = Ride.objects.filter(user=user, status='completed')[:10]
        
        if not recent_rides.exists():
            return "New rider - patterns developing"
        
        avg_distance = sum(float(ride.distance) for ride in recent_rides) / len(recent_rides)
        avg_cost = sum(float(ride.cost) for ride in recent_rides) / len(recent_rides)
        
        if avg_distance < 2:
            pattern = "Short distance commuter"
        elif avg_distance < 5:
            pattern = "Medium distance traveler"
        else:
            pattern = "Long distance rider"
        
        return {
            'pattern_type': pattern,
            'average_distance_km': round(avg_distance, 2),
            'average_cost': round(avg_cost, 2),
            'total_rides': len(recent_rides)
        }
    
    def _get_preferred_times(self, user):
        """Get user's preferred riding times"""
        rides = Ride.objects.filter(user=user, status='completed')
        
        if not rides.exists():
            return "No riding history yet"
        
        hourly_counts = {}
        for ride in rides:
            hour = ride.start_time.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        if not hourly_counts:
            return "No time pattern detected"
        
        peak_hour = max(hourly_counts, key=hourly_counts.get)
        
        return {
            'peak_hour': f"{peak_hour}:00",
            'peak_hour_rides': hourly_counts[peak_hour],
            'total_analyzed_rides': len(rides)
        }
    
    def _calculate_savings_impact(self, user):
        """Calculate environmental and cost savings"""
        total_distance = user.total_distance_covered or 0
        carbon_saved = user.carbon_saved_total or 0
        
        # Assuming car emits 0.2kg CO2 per km and costs ₹8 per km
        car_emissions = total_distance * 0.2
        car_cost = total_distance * 8
        
        return {
            'carbon_saved_kg': round(carbon_saved, 2),
            'equivalent_car_emissions_kg': round(car_emissions, 2),
            'estimated_car_cost_saved': round(car_cost, 2),
            'equivalent_trees': round(carbon_saved / 21.77, 1)  # kg CO2 per tree per year
        }