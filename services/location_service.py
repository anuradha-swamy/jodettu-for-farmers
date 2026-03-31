import requests
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import folium
from folium.plugins import HeatMap

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    postal_code: str = ""

class OpenStreetMapService:
    def __init__(self):
        """Initialize OpenStreetMap service with Nominatim API"""
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.reverse_url = "https://nominatim.openstreetmap.org/reverse"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.headers = {
            'User-Agent': 'JodettuApp/1.0 (https://jodettu.com; contact@jodettu.com)'
        }

    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Convert address to coordinates
        Args:
            address: Address string
        Returns:
            Dictionary with coordinates and location details
        """
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1,
                'countrycodes': 'in'  # Focus on India
            }
            
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return {"error": "Location not found"}
            
            result = data[0]
            location = Location(
                latitude=float(result['lat']),
                longitude=float(result['lon']),
                address=result.get('display_name', ''),
                city=result.get('address', {}).get('city', ''),
                state=result.get('address', {}).get('state', ''),
                country=result.get('address', {}).get('country', ''),
                postal_code=result.get('address', {}).get('postcode', '')
            )
            
            return {
                "success": True,
                "location": location,
                "coordinates": {
                    "lat": location.latitude,
                    "lon": location.longitude
                }
            }
            
        except Exception as e:
            return {"error": f"Geocoding failed: {str(e)}"}

    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Convert coordinates to address
        Args:
            lat: Latitude
            lon: Longitude
        Returns:
            Dictionary with address details
        """
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1
            }
            
            response = requests.get(self.reverse_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                return {"error": "Reverse geocoding failed"}
            
            address = data.get('display_name', '')
            address_parts = data.get('address', {})
            
            return {
                "success": True,
                "address": address,
                "components": {
                    "house_number": address_parts.get('house_number', ''),
                    "road": address_parts.get('road', ''),
                    "neighbourhood": address_parts.get('neighbourhood', ''),
                    "suburb": address_parts.get('suburb', ''),
                    "city": address_parts.get('city', address_parts.get('town', address_parts.get('village', ''))),
                    "county": address_parts.get('county', ''),
                    "state": address_parts.get('state', ''),
                    "postcode": address_parts.get('postcode', ''),
                    "country": address_parts.get('country', ''),
                    "country_code": address_parts.get('country_code', '')
                }
            }
            
        except Exception as e:
            return {"error": f"Reverse geocoding failed: {str(e)}"}

    async def find_nearby_places(self, lat: float, lon: float, place_type: str, radius: int = 5000) -> Dict[str, Any]:
        """
        Find nearby places using Overpass API
        Args:
            lat: Latitude
            lon: Longitude
            place_type: Type of place (e.g., 'hospital', 'school', 'market')
            radius: Search radius in meters
        Returns:
            Dictionary with nearby places
        """
        try:
            # Overpass QL query
            query = f"""
            [out:json][timeout:25];
            (
              node["{place_type}"](around:{radius},{lat},{lon});
              way["{place_type}"](around:{radius},{lat},{lon});
              relation["{place_type}"](around:{radius},{lat},{lon});
            );
            out body;
            >;
            out skel qt;
            """
            
            params = {'data': query}
            response = requests.get(self.overpass_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            
            places = []
            for element in data.get('elements', []):
                if element.get('type') == 'node' and 'lat' in element and 'lon' in element:
                    tags = element.get('tags', {})
                    place_info = {
                        "name": tags.get('name', 'Unknown'),
                        "type": tags.get(place_type, place_type),
                        "latitude": element['lat'],
                        "longitude": element['lon'],
                        "address": {
                            "housenumber": tags.get('addr:housenumber', ''),
                            "street": tags.get('addr:street', ''),
                            "city": tags.get('addr:city', ''),
                            "postcode": tags.get('addr:postcode', '')
                        },
                        "phone": tags.get('phone', tags.get('contact:phone', '')),
                        "website": tags.get('website', tags.get('contact:website', '')),
                        "opening_hours": tags.get('opening_hours', '')
                    }
                    places.append(place_info)
            
            return {
                "success": True,
                "places": places,
                "total_found": len(places),
                "search_center": {"lat": lat, "lon": lon},
                "search_radius": radius
            }
            
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    async def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
        """
        Calculate distance between two points using Haversine formula
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
        Returns:
            Dictionary with distance information
        """
        try:
            import math
            
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Haversine formula
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            a = (math.sin(dlat/2)**2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in kilometers
            r = 6371
            
            distance_km = r * c
            distance_miles = distance_km * 0.621371
            
            return {
                "success": True,
                "distance_km": round(distance_km, 2),
                "distance_miles": round(distance_miles, 2),
                "point1": {"lat": lat1, "lon": lon1},
                "point2": {"lat": lat2, "lon": lon2}
            }
            
        except Exception as e:
            return {"error": f"Distance calculation failed: {str(e)}"}

    async def create_map(self, locations: List[Dict], center_lat: float, center_lon: float, 
                        zoom: int = 12) -> Dict[str, Any]:
        """
        Create an interactive map with markers
        Args:
            locations: List of locations with lat, lon, and optional info
            center_lat, center_lon: Map center coordinates
            zoom: Initial zoom level
        Returns:
            Dictionary with map HTML and info
        """
        try:
            # Create map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom,
                tiles='OpenStreetMap'
            )
            
            # Add markers for each location
            for i, loc in enumerate(locations):
                lat = loc.get('lat', loc.get('latitude'))
                lon = loc.get('lon', loc.get('longitude'))
                
                if lat and lon:
                    popup_text = loc.get('name', f'Location {i+1}')
                    if loc.get('address'):
                        popup_text += f"<br>{loc['address']}"
                    
                    folium.Marker(
                        [lat, lon],
                        popup=popup_text,
                        tooltip=loc.get('name', f'Location {i+1}')
                    ).add_to(m)
            
            # Generate HTML
            map_html = m._repr_html_()
            
            return {
                "success": True,
                "map_html": map_html,
                "center": {"lat": center_lat, "lon": center_lon},
                "zoom": zoom,
                "markers_count": len(locations)
            }
            
        except Exception as e:
            return {"error": f"Map creation failed: {str(e)}"}

    async def get_route(self, start_lat: float, start_lon: float, 
                       end_lat: float, end_lon: float) -> Dict[str, Any]:
        """
        Get route between two points using OSRM (Open Source Routing Machine)
        Args:
            start_lat, start_lon: Starting point coordinates
            end_lat, end_lon: Ending point coordinates
        Returns:
            Dictionary with route information
        """
        try:
            # Using OSRM demo server (in production, use your own instance)
            osrm_url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
            
            params = {
                'overview': 'full',
                'geometries': 'geojson'
            }
            
            response = requests.get(osrm_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') != 'Ok':
                return {"error": "Route not found"}
            
            route = data['routes'][0]
            distance_km = route['distance'] / 1000
            duration_min = route['duration'] / 60
            
            return {
                "success": True,
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_min, 2),
                "geometry": route['geometry'],
                "start_point": {"lat": start_lat, "lon": start_lon},
                "end_point": {"lat": end_lat, "lon": end_lon}
            }
            
        except Exception as e:
            return {"error": f"Route calculation failed: {str(e)}"}

# Global instance
location_service = OpenStreetMapService()
