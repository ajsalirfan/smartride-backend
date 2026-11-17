import math
from django.db.models import Q
from .models import Vehicle

class GPSUtils:
    """
    GPS utilities for location-based operations
    """
    
    # Service area boundaries (Bangalore coordinates)
    SERVICE_AREA_BOUNDS = {
        'min_lat': 12.75,
        'max_lat': 13.15,
        'min_lng': 77.35,
        'max_lng': 77.85
    }
    
    @staticmethod
    def calculate_distance(lat1, lng1, lat2, lng2):
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in kilometers
        """
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(float(lat1))
        lat2_rad = math.radians(float(lat2))
        delta_lat = math.radians(float(lat2) - float(lat1))
        delta_lng = math.radians(float(lng2) - float(lng1))
        
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) * math.sin(delta_lng / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def is_in_service_area(lat, lng):
        """
        Check if coordinates are within service area
        """
        return (GPSUtils.SERVICE_AREA_BOUNDS['min_lat'] <= float(lat) <= GPSUtils.SERVICE_AREA_BOUNDS['max_lat'] and
                GPSUtils.SERVICE_AREA_BOUNDS['min_lng'] <= float(lng) <= GPSUtils.SERVICE_AREA_BOUNDS['max_lng'])
    
    @staticmethod
    def get_nearby_vehicles(user_lat, user_lng, radius_km=5, vehicle_type=None, min_battery=20):
        """
        Find vehicles within specified radius
        """
        if not GPSUtils.is_in_service_area(user_lat, user_lng):
            return Vehicle.objects.none()
        
        vehicles = Vehicle.objects.filter(
            status='available',
            battery_level__gte=min_battery
        )
        
        if vehicle_type:
            vehicles = vehicles.filter(vehicle_type=vehicle_type)
        
        # Calculate distance for each vehicle and filter
        nearby_vehicles = []
        for vehicle in vehicles:
            if vehicle.current_location_lat and vehicle.current_location_lng:
                distance = GPSUtils.calculate_distance(
                    user_lat, user_lng,
                    vehicle.current_location_lat, vehicle.current_location_lng
                )
                if distance <= radius_km:
                    vehicle.distance = distance
                    nearby_vehicles.append(vehicle)
        
        # Sort by distance
        return sorted(nearby_vehicles, key=lambda x: x.distance)
    
    @staticmethod
    def calculate_ride_distance(start_lat, start_lng, end_lat, end_lng):
        """
        Calculate distance for a ride
        """
        return GPSUtils.calculate_distance(start_lat, start_lng, end_lat, end_lng)
    
    @staticmethod
    def get_address_from_coordinates(lat, lng):
        """
        Mock function for reverse geocoding
        In production, integrate with Google Maps API or similar
        """
        # This is a mock implementation
        locations = {
            (12.9716, 77.5946): "MG Road, Bangalore",
            (12.9352, 77.6245): "Koramangala, Bangalore", 
            (13.0225, 77.5500): "Hebbal, Bangalore",
            (12.9784, 77.6408): "HSR Layout, Bangalore"
        }
        
        # Find closest known location
        min_distance = float('inf')
        closest_location = "Unknown Location"
        
        for known_lat, known_lng in locations.keys():
            distance = GPSUtils.calculate_distance(lat, lng, known_lat, known_lng)
            if distance < min_distance and distance < 2.0:  # Within 2km
                min_distance = distance
                closest_location = locations[(known_lat, known_lng)]
        
        return closest_location