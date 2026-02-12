# utils/location_service.py
import requests
import re
import json
from ipware import get_client_ip
from django.conf import settings

class LocationService:
    """Service to extract and process location data for check-in/check-out"""
    
    # Common Pune area mappings
    PUNE_AREAS = [
        "Wakad", "Hinjawadi", "Baner", "Pimple Saudagar", "Pimple Nilakh", 
        "Pimple Gurav", "Ravet", "Tathawade", "Mumbai Pune Highway",
        "Nigdi", "Pradhikaran", "Akurdi", "Chinchwad", "Swargate", 
        "Shivajinagar", "Deccan", "FC Road", "JM Road", "Kothrud",
        "Karve Nagar", "Erandwane", "Model Colony", "Katraj", 
        "Dhankawadi", "Sahakar Nagar", "Bhosari", "Dapodi", "Khadki",
        "Aundh", "Sangvi", "Hadapsar", "Magarpatta", "Kharadi", 
        "Viman Nagar", "Yervada", "Kalyani Nagar", "Koregaon Park",
        "Camp", "Pune Station", "Bhavani Peth", "Gultekdi", 
        "Market Yard", "Ambegaon", "Balewadi", "Shaniwar Peth",
        "Budhwar Peth", "Sadashiv Peth"
    ]
    
    @staticmethod
    def extract_area_name(request):
        """
        Extract area name from request with priority:
        1. Direct area name from request
        2. From coordinates (latitude/longitude)
        3. From address string
        4. From IP address (city name)
        """
        data = request.data
        
        # 1. Direct area name (most preferred)
        if 'area' in data and data['area']:
            return data['area'].strip().title()
        
        # 2. From coordinates
        if 'latitude' in data and 'longitude' in data:
            lat = data['latitude']
            lon = data['longitude']
            try:
                full_address = LocationService._reverse_geocode(lat, lon)
                area = LocationService._extract_area_from_address(full_address)
                if area and area != "Unknown Area":
                    return area
            except:
                pass
        
        # 3. From address string
        if 'address' in data and data['address']:
            area = LocationService._extract_area_from_address(data['address'])
            if area and area != "Unknown Area":
                return area
        
        # 4. From IP address (fallback)
        return LocationService._get_city_from_ip(request)
    
    @staticmethod
    def _reverse_geocode(latitude, longitude):
        """Convert coordinates to address using Nominatim"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'HRMS-App/1.0 (hrms@example.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Reverse geocoding failed: {e}")
        
        return None
    
    @staticmethod
    def _extract_area_from_address(address_data):
        """Extract area name from address data"""
        if not address_data:
            return "Unknown Area"
        
        # If address_data is a dict (from reverse geocode)
        if isinstance(address_data, dict):
            address_components = address_data.get('address', {})
            
            # Priority of address components for area extraction
            priority_keys = ['suburb', 'neighbourhood', 'quarter', 
                            'city_district', 'village', 'town', 'city']
            
            for key in priority_keys:
                if key in address_components:
                    area = address_components[key]
                    # Check if it's a known Pune area
                    normalized_area = LocationService._normalize_area_name(area)
                    if normalized_area:
                        return normalized_area
            
            # Try display_name
            display_name = address_data.get('display_name', '')
            if display_name:
                return LocationService._extract_area_from_text(display_name)
        
        # If address_data is a string
        elif isinstance(address_data, str):
            return LocationService._extract_area_from_text(address_data)
        
        return "Unknown Area"
    
    @staticmethod
    def _extract_area_from_text(text):
        """Extract area name from text using pattern matching"""
        if not text:
            return "Unknown Area"
        
        text_lower = text.lower()
        
        # Check for each Pune area
        for area in LocationService.PUNE_AREAS:
            area_lower = area.lower()
            # Check exact match or contains with word boundaries
            if area_lower in text_lower:
                # Ensure it's not part of another word
                pattern = r'\b' + re.escape(area_lower) + r'\b'
                if re.search(pattern, text_lower):
                    return area
        
        # Try to find pattern like "Near [Area]" or "[Area], Pune"
        pattern = r'\b(near\s+)?([a-z\s]+?)(?:,|\s+pune|\s+maharashtra)'
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            possible_area = match.group(2).strip()
            for area in LocationService.PUNE_AREAS:
                if area.lower() in possible_area:
                    return area
        
        return "Unknown Area"
    
    @staticmethod
    def _normalize_area_name(area):
        """Normalize area name to match our known areas"""
        if not area:
            return None
        
        area_lower = area.lower().strip()
        
        # Common variations mapping
        variations = {
            'wakad': 'Wakad',
            'baner': 'Baner',
            'hinjewadi': 'Hinjawadi',
            'hinjawadi': 'Hinjawadi',
            'kothrud': 'Kothrud',
            'swargate': 'Swargate',
            'shivaji nagar': 'Shivajinagar',
            'shivajinagar': 'Shivajinagar',
            'aundh': 'Aundh',
            'viman nagar': 'Viman Nagar',
            'kharadi': 'Kharadi',
            'hadapsar': 'Hadapsar',
            'pimple saudagar': 'Pimple Saudagar',
            'ravet': 'Ravet',
            'nigdi': 'Nigdi',
            'chinchwad': 'Chinchwad',
            'deccan': 'Deccan',
            'camp area': 'Camp',
            'model colony': 'Model Colony',
        }
        
        # Check variations
        if area_lower in variations:
            return variations[area_lower]
        
        # Check if it matches any Pune area
        for pune_area in LocationService.PUNE_AREAS:
            if pune_area.lower() == area_lower:
                return pune_area
        
        return None
    
    @staticmethod
    def _get_city_from_ip(request):
        """Get city name from IP address"""
        client_ip, _ = get_client_ip(request)
        
        if not client_ip or client_ip == "127.0.0.1":
            return "Office"  # For local development
        
        try:
            # Using ip-api.com (free, 150 requests/min)
            response = requests.get(f"http://ip-api.com/json/{client_ip}", timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    city = data.get('city', '')
                    region = data.get('regionName', '')

                    # If in Pune region, return city
                    if 'Pune' in region or 'Pune' in city:
                        return city if city else "Pune"
                    else:
                        return f"Remote ({city})" if city else "Remote"
        except:
            pass
        
        return "Remote"
    
    @staticmethod
    def get_location_data(request):
        """Get complete location data"""
        area_name = LocationService.extract_area_name(request)
        
        # Get IP for additional info
        client_ip, _ = get_client_ip(request)
        
        return {
            'area': area_name,
            'ip_address': client_ip,
            'source': 'direct' if 'area' in request.data else 
                     'coordinates' if 'latitude' in request.data else 
                     'address' if 'address' in request.data else 
                     'ip'
        }