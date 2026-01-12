import requests
from typing import List, Dict, Optional
from fastapi import HTTPException
import uuid
from datetime import datetime
from database import get_table, DATA_TYPE_SAVED_LOCATION

class LocationService:
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        self.table = get_table()
    
    def find_food_locations(
        self,
        latitude: float,
        longitude: float,
        radius: int = 5000,  # meters
        location_types: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None
    ) -> List[Dict]:
        """Find food-related locations near a coordinate"""
        
        # Default to all food location types if not specified
        if not location_types:
            location_types = ['food_bank', 'soup_kitchen', 'shelter']
        
        # Build Overpass query
        query = self._build_overpass_query(latitude, longitude, radius, location_types)
        
        try:
            response = requests.post(
                self.overpass_url,
                data={"data": query},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse and format results
            locations = self._parse_overpass_results(data, dietary_restrictions)
            
            return locations
            
        except Exception as e:
            print(f"Error querying OpenStreetMap: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search locations: {str(e)}"
            )
    
    def _build_overpass_query(
        self,
        lat: float,
        lon: float,
        radius: int,
        location_types: List[str]
    ) -> str:
        """Build Overpass API query for food locations"""
        
        # Map our types to OSM tags
        osm_queries = []
        
        if 'food_bank' in location_types:
            osm_queries.append('node["amenity"="food_bank"]')
            osm_queries.append('way["amenity"="food_bank"]')
        
        if 'soup_kitchen' in location_types:
            osm_queries.append('node["amenity"="social_facility"]["social_facility"="soup_kitchen"]')
            osm_queries.append('way["amenity"="social_facility"]["social_facility"="soup_kitchen"]')
        
        if 'shelter' in location_types:
            osm_queries.append('node["amenity"="shelter"]')
            osm_queries.append('way["amenity"="shelter"]')
            osm_queries.append('node["amenity"="social_facility"]["social_facility"="shelter"]')
            osm_queries.append('way["amenity"="social_facility"]["social_facility"="shelter"]')
        
        # Also search for community centers and charities that might provide food
        osm_queries.append('node["amenity"="community_centre"]')
        osm_queries.append('way["amenity"="community_centre"]')
        
        # Build the full query
        query_parts = [f"({q}(around:{radius},{lat},{lon}););" for q in osm_queries]
        
        query = f"""
        [out:json][timeout:25];
        (
            {''.join(query_parts)}
        );
        out body center;
        """
        
        return query
    
    def _parse_overpass_results(
        self,
        data: Dict,
        dietary_restrictions: Optional[List[str]] = None
    ) -> List[Dict]:
        """Parse Overpass API results into our format"""
        locations = []
        
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            
            # Determine location type
            location_type = self._determine_location_type(tags)
            
            # Get coordinates
            if element['type'] == 'node':
                lat = element['lat']
                lon = element['lon']
            elif 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            else:
                continue
            
            # Extract location info
            location = {
                'id': str(element['id']),
                'name': tags.get('name', 'Unnamed Location'),
                'type': location_type,
                'latitude': lat,
                'longitude': lon,
                'address': self._format_address(tags),
                'phone': tags.get('phone', tags.get('contact:phone', '')),
                'website': tags.get('website', tags.get('contact:website', '')),
                'hours': tags.get('opening_hours', ''),
                'description': tags.get('description', ''),
                'wheelchair_accessible': tags.get('wheelchair') == 'yes',
                'dietary_options': self._extract_dietary_info(tags)
            }
            
            # Filter by dietary restrictions if provided
            if dietary_restrictions and location['dietary_options']:
                if not any(diet in location['dietary_options'] for diet in dietary_restrictions):
                    continue
            
            locations.append(location)
        
        return locations
    
    def _determine_location_type(self, tags: Dict) -> str:
        """Determine the type of food location"""
        amenity = tags.get('amenity', '')
        social_facility = tags.get('social_facility', '')
        
        if amenity == 'food_bank':
            return 'food_bank'
        elif social_facility == 'soup_kitchen':
            return 'soup_kitchen'
        elif amenity == 'shelter' or social_facility == 'shelter':
            return 'shelter'
        elif amenity == 'community_centre':
            return 'community_center'
        else:
            return 'food_assistance'
    
    def _format_address(self, tags: Dict) -> str:
        """Format address from OSM tags"""
        parts = []
        
        if 'addr:housenumber' in tags and 'addr:street' in tags:
            parts.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
        elif 'addr:street' in tags:
            parts.append(tags['addr:street'])
        
        if 'addr:city' in tags:
            parts.append(tags['addr:city'])
        
        if 'addr:state' in tags:
            parts.append(tags['addr:state'])
        
        if 'addr:postcode' in tags:
            parts.append(tags['addr:postcode'])
        
        return ', '.join(parts) if parts else 'Address not available'
    
    def _extract_dietary_info(self, tags: Dict) -> List[str]:
        """Extract dietary information from tags"""
        dietary_options = []
        
        if tags.get('diet:vegetarian') == 'yes':
            dietary_options.append('vegetarian')
        if tags.get('diet:vegan') == 'yes':
            dietary_options.append('vegan')
        if tags.get('diet:halal') == 'yes':
            dietary_options.append('halal')
        if tags.get('diet:kosher') == 'yes':
            dietary_options.append('kosher')
        if tags.get('diet:gluten_free') == 'yes':
            dietary_options.append('gluten_free')
        
        return dietary_options
    
    def save_location(
        self,
        user_id: str,
        location_data: Dict
    ) -> Dict:
        """Save a location to user's saved locations"""
        location_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        try:
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_SAVED_LOCATION}#{location_id}",
                    'locationId': location_id,
                    'name': location_data['name'],
                    'address': location_data['address'],
                    'latitude': str(location_data['latitude']),
                    'longitude': str(location_data['longitude']),
                    'type': location_data['type'],
                    'hours': location_data.get('hours', ''),
                    'phone': location_data.get('phone', ''),
                    'savedAt': timestamp
                }
            )
            
            return {
                'locationId': location_id,
                'message': 'Location saved successfully'
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save location: {str(e)}"
            )
    
    def get_saved_locations(self, user_id: str) -> List[Dict]:
        """Get all saved locations for a user"""
        try:
            response = self.table.query(
                KeyConditionExpression='userId = :userId AND begins_with(dataType, :dataType)',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':dataType': DATA_TYPE_SAVED_LOCATION
                }
            )
            
            return response.get('Items', [])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve saved locations: {str(e)}"
            )
    
    def delete_saved_location(self, user_id: str, location_id: str) -> Dict:
        """Delete a saved location"""
        try:
            self.table.delete_item(
                Key={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_SAVED_LOCATION}#{location_id}"
                }
            )
            
            return {'message': 'Location deleted successfully'}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete location: {str(e)}"
            )
