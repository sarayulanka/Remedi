import requests
from typing import List, Dict, Optional
from fastapi import HTTPException
import uuid
from datetime import datetime
from database import get_table, DATA_TYPE_SAVED_LOCATION
import math

class LocationService:
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        self.table = get_table()
        # Required User-Agent header for OpenStreetMap API
        self.headers = {
            'User-Agent': 'Remedi-NutritionApp/1.0 (contact@remediapp.com)'
        }

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

        print(f"[Location Search] Coordinates: ({latitude}, {longitude})")
        print(f"[Location Search] Radius: {radius}m, Types: {location_types}")

        # Try multiple strategies to find locations
        locations = []

        # Strategy 1: Try Overpass API with simplified query
        try:
            locations = self._search_overpass_simple(latitude, longitude, radius, location_types)
            print(f"[Overpass Simple] Found {len(locations)} locations")
        except Exception as e:
            print(f"[Overpass Simple] Error: {str(e)}")

        # Strategy 2: If no results, try broader search
        if not locations:
            try:
                locations = self._search_overpass_broad(latitude, longitude, radius * 2, location_types)
                print(f"[Overpass Broad] Found {len(locations)} locations")
            except Exception as e:
                print(f"[Overpass Broad] Error: {str(e)}")

        # Strategy 3: If still no results, try Nominatim search
        if not locations:
            try:
                locations = self._search_nominatim(latitude, longitude, radius, location_types)
                print(f"[Nominatim] Found {len(locations)} locations")
            except Exception as e:
                print(f"[Nominatim] Error: {str(e)}")

        # If no results from any API, provide helpful fallback
        if not locations:
            print("[Location Search] No API results, returning fallback locations")
            return self._get_fallback_locations(latitude, longitude, location_types)

        # Sort by distance and filter by dietary restrictions
        locations = self._sort_by_distance(locations, latitude, longitude)

        if dietary_restrictions and len(dietary_restrictions) > 0:
            locations = self._filter_by_dietary(locations, dietary_restrictions)

        return locations[:15]  # Return top 15 results

    def _search_overpass_simple(
        self,
        lat: float,
        lon: float,
        radius: int,
        location_types: List[str]
    ) -> List[Dict]:
        """Simple Overpass query focusing on most common tags"""

        # Build simple query parts
        query_parts = []

        if 'food_bank' in location_types:
            query_parts.extend([
                f'node["social_facility"="food_bank"](around:{radius},{lat},{lon});',
                f'way["social_facility"="food_bank"](around:{radius},{lat},{lon});',
                f'node["amenity"="social_facility"]["social_facility:for"="hungry"](around:{radius},{lat},{lon});',
            ])

        if 'soup_kitchen' in location_types:
            query_parts.extend([
                f'node["social_facility"="soup_kitchen"](around:{radius},{lat},{lon});',
                f'way["social_facility"="soup_kitchen"](around:{radius},{lat},{lon});',
            ])

        if 'shelter' in location_types:
            query_parts.extend([
                f'node["social_facility"="shelter"](around:{radius},{lat},{lon});',
                f'way["social_facility"="shelter"](around:{radius},{lat},{lon});',
                f'node["amenity"="shelter"](around:{radius},{lat},{lon});',
                f'way["amenity"="shelter"](around:{radius},{lat},{lon});',
            ])

        # Always include charities and community centers
        query_parts.extend([
            f'node["office"="charity"](around:{radius},{lat},{lon});',
            f'way["office"="charity"](around:{radius},{lat},{lon});',
            f'node["amenity"="community_centre"](around:{radius},{lat},{lon});',
            f'way["amenity"="community_centre"](around:{radius},{lat},{lon});',
        ])

        query = f"""
        [out:json][timeout:30];
        (
            {''.join(query_parts)}
        );
        out body center;
        """

        response = requests.post(
            self.overpass_url,
            data={"data": query},
            headers=self.headers,
            timeout=35
        )
        response.raise_for_status()
        data = response.json()

        return self._parse_overpass_results(data, location_types)

    def _search_overpass_broad(
        self,
        lat: float,
        lon: float,
        radius: int,
        location_types: List[str]
    ) -> List[Dict]:
        """Broader Overpass query with more tag variations"""

        query = f"""
        [out:json][timeout:45];
        (
            node["social_facility"](around:{radius},{lat},{lon});
            way["social_facility"](around:{radius},{lat},{lon});
            node["amenity"="social_facility"](around:{radius},{lat},{lon});
            way["amenity"="social_facility"](around:{radius},{lat},{lon});
            node["office"="charity"](around:{radius},{lat},{lon});
            way["office"="charity"](around:{radius},{lat},{lon});
            node["office"="ngo"](around:{radius},{lat},{lon});
            way["office"="ngo"](around:{radius},{lat},{lon});
            node["amenity"="community_centre"](around:{radius},{lat},{lon});
            way["amenity"="community_centre"](around:{radius},{lat},{lon});
            node["amenity"="place_of_worship"]["community_centre"="yes"](around:{radius},{lat},{lon});
            way["amenity"="place_of_worship"]["community_centre"="yes"](around:{radius},{lat},{lon});
        );
        out body center;
        """

        response = requests.post(
            self.overpass_url,
            data={"data": query},
            headers=self.headers,
            timeout=50
        )
        response.raise_for_status()
        data = response.json()

        return self._parse_overpass_results(data, location_types)

    def _search_nominatim(
        self,
        lat: float,
        lon: float,
        radius: int,
        location_types: List[str]
    ) -> List[Dict]:
        """Search using Nominatim as backup"""
        locations = []

        search_terms = ['food bank', 'soup kitchen', 'homeless shelter', 'food pantry', 'community center']

        for term in search_terms:
            try:
                # Calculate bounding box
                lat_delta = radius / 111000  # degrees per meter latitude
                lon_delta = radius / (111000 * math.cos(math.radians(lat)))

                params = {
                    'q': term,
                    'format': 'json',
                    'viewbox': f'{lon-lon_delta},{lat+lat_delta},{lon+lon_delta},{lat-lat_delta}',
                    'bounded': 1,
                    'limit': 5,
                    'addressdetails': 1
                }

                response = requests.get(
                    f"{self.nominatim_url}/search",
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                results = response.json()

                for result in results:
                    location = {
                        'id': f"nom_{result.get('place_id', '')}",
                        'name': result.get('display_name', '').split(',')[0],
                        'type': self._classify_nominatim_result(result, term),
                        'latitude': float(result.get('lat', 0)),
                        'longitude': float(result.get('lon', 0)),
                        'address': result.get('display_name', 'Address not available'),
                        'phone': '',
                        'website': '',
                        'hours': 'Call for hours',
                        'description': f'Found via search: {term}',
                        'wheelchair_accessible': True,
                        'dietary_options': []
                    }

                    # Avoid duplicates
                    if not any(loc['name'] == location['name'] for loc in locations):
                        locations.append(location)

            except Exception as e:
                print(f"[Nominatim] Error searching '{term}': {str(e)}")
                continue

        return locations

    def _classify_nominatim_result(self, result: Dict, search_term: str) -> str:
        """Classify Nominatim result into our location types"""
        term_lower = search_term.lower()

        if 'food bank' in term_lower or 'pantry' in term_lower:
            return 'food_bank'
        elif 'soup' in term_lower or 'kitchen' in term_lower:
            return 'soup_kitchen'
        elif 'shelter' in term_lower or 'homeless' in term_lower:
            return 'shelter'
        else:
            return 'community_center'

    def _get_fallback_locations(
        self,
        latitude: float,
        longitude: float,
        location_types: List[str]
    ) -> List[Dict]:
        """Provide helpful fallback locations and resources when APIs fail"""

        fallback_locations = []

        # Slight coordinate offsets to simulate nearby locations
        offsets = [
            (0.008, 0.005),
            (-0.012, 0.008),
            (0.004, -0.010),
            (-0.006, -0.007),
            (0.015, 0.003),
            (-0.009, 0.012),
        ]

        if 'food_bank' in location_types:
            names = [
                ("Community Food Bank", "Food distribution center serving families in need"),
                ("Local Food Pantry", "Non-profit providing free groceries"),
                ("Neighborhood Food Assistance", "Weekly food distributions available"),
            ]
            for i, (name, desc) in enumerate(names[:2]):
                offset = offsets[i % len(offsets)]
                fallback_locations.append({
                    'id': f'fallback_fb_{i}',
                    'name': name,
                    'type': 'food_bank',
                    'latitude': latitude + offset[0],
                    'longitude': longitude + offset[1],
                    'address': 'Call 211 for exact address',
                    'phone': '211',
                    'website': 'https://www.211.org',
                    'hours': 'Varies - call for hours',
                    'description': desc,
                    'wheelchair_accessible': True,
                    'dietary_options': [],
                    'is_fallback': True
                })

        if 'soup_kitchen' in location_types:
            names = [
                ("Community Meal Program", "Free hot meals served daily"),
                ("Neighborhood Kitchen", "Nutritious meals for those in need"),
            ]
            for i, (name, desc) in enumerate(names):
                offset = offsets[(i + 2) % len(offsets)]
                fallback_locations.append({
                    'id': f'fallback_sk_{i}',
                    'name': name,
                    'type': 'soup_kitchen',
                    'latitude': latitude + offset[0],
                    'longitude': longitude + offset[1],
                    'address': 'Call 211 for exact address',
                    'phone': '211',
                    'website': 'https://www.211.org',
                    'hours': 'Typically lunch & dinner hours',
                    'description': desc,
                    'wheelchair_accessible': True,
                    'dietary_options': [],
                    'is_fallback': True
                })

        if 'shelter' in location_types:
            names = [
                ("Emergency Shelter Services", "Safe overnight accommodations"),
                ("Community Shelter", "Temporary housing assistance available"),
            ]
            for i, (name, desc) in enumerate(names):
                offset = offsets[(i + 4) % len(offsets)]
                fallback_locations.append({
                    'id': f'fallback_sh_{i}',
                    'name': name,
                    'type': 'shelter',
                    'latitude': latitude + offset[0],
                    'longitude': longitude + offset[1],
                    'address': 'Call 211 for exact address',
                    'phone': '211',
                    'website': 'https://www.211.org',
                    'hours': '24/7 or evening hours',
                    'description': desc,
                    'wheelchair_accessible': True,
                    'dietary_options': [],
                    'is_fallback': True
                })

        # Always add 211 resource as the primary contact
        fallback_locations.append({
            'id': 'fallback_211',
            'name': '211 - Community Resources Hotline',
            'type': 'food_assistance',
            'latitude': latitude,
            'longitude': longitude,
            'address': 'Dial 2-1-1 from any phone',
            'phone': '211',
            'website': 'https://www.211.org',
            'hours': '24/7',
            'description': 'Free, confidential helpline connecting you to local food, shelter, and social services. Available 24/7 in most areas.',
            'wheelchair_accessible': True,
            'dietary_options': [],
            'is_fallback': True,
            'is_primary_resource': True
        })

        # Add Feeding America as a resource
        fallback_locations.append({
            'id': 'fallback_feedingamerica',
            'name': 'Feeding America Food Bank Locator',
            'type': 'food_bank',
            'latitude': latitude + 0.002,
            'longitude': longitude + 0.002,
            'address': 'Visit website to find nearest location',
            'phone': '1-800-771-2303',
            'website': 'https://www.feedingamerica.org/find-your-local-foodbank',
            'hours': 'See website for local hours',
            'description': 'Nationwide network of 200 food banks and 60,000 food pantries and meal programs.',
            'wheelchair_accessible': True,
            'dietary_options': [],
            'is_fallback': True
        })

        return fallback_locations

    def _parse_overpass_results(
        self,
        data: Dict,
        location_types: List[str]
    ) -> List[Dict]:
        """Parse Overpass API results into our format"""
        locations = []
        seen_ids = set()  # Prevent duplicates

        for element in data.get('elements', []):
            # Skip duplicates
            element_id = str(element.get('id', ''))
            if element_id in seen_ids:
                continue
            seen_ids.add(element_id)

            tags = element.get('tags', {})

            # Skip if no useful information
            if not tags.get('name') and not tags.get('amenity') and not tags.get('social_facility') and not tags.get('office'):
                continue

            # Determine location type
            location_type = self._determine_location_type(tags)

            # Get coordinates
            if element['type'] == 'node':
                lat = element.get('lat')
                lon = element.get('lon')
            elif 'center' in element:
                lat = element['center'].get('lat')
                lon = element['center'].get('lon')
            else:
                continue

            if lat is None or lon is None:
                continue

            # Extract location info
            location = {
                'id': f"osm_{element_id}",
                'name': tags.get('name', self._generate_name(tags, location_type)),
                'type': location_type,
                'latitude': lat,
                'longitude': lon,
                'address': self._format_address(tags),
                'phone': tags.get('phone', tags.get('contact:phone', '')),
                'website': tags.get('website', tags.get('contact:website', '')),
                'hours': self._format_hours(tags.get('opening_hours', '')),
                'description': tags.get('description', ''),
                'wheelchair_accessible': tags.get('wheelchair') == 'yes',
                'dietary_options': self._extract_dietary_info(tags),
                'is_fallback': False
            }

            locations.append(location)

        return locations

    def _determine_location_type(self, tags: Dict) -> str:
        """Determine the type of food location"""
        social_facility = tags.get('social_facility', '')
        amenity = tags.get('amenity', '')
        office = tags.get('office', '')
        name = tags.get('name', '').lower()

        if social_facility == 'food_bank' or 'food bank' in name or 'pantry' in name:
            return 'food_bank'
        elif social_facility == 'soup_kitchen' or 'soup' in name or 'meal' in name or 'kitchen' in name:
            return 'soup_kitchen'
        elif social_facility in ['shelter', 'homeless_shelter'] or amenity == 'shelter' or 'shelter' in name:
            return 'shelter'
        elif amenity == 'community_centre' or 'community' in name:
            return 'community_center'
        elif office in ['charity', 'ngo']:
            return 'food_assistance'
        else:
            return 'food_assistance'

    def _generate_name(self, tags: Dict, location_type: str) -> str:
        """Generate a name when none is provided"""
        type_names = {
            'food_bank': 'Food Bank',
            'soup_kitchen': 'Soup Kitchen',
            'shelter': 'Shelter',
            'community_center': 'Community Center',
            'food_assistance': 'Food Assistance Center'
        }
        base_name = type_names.get(location_type, 'Food Location')

        # Try to add more context from tags
        if tags.get('operator'):
            return f"{tags['operator']} {base_name}"

        return base_name

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

    def _format_hours(self, hours_str: str) -> str:
        """Format opening hours for display"""
        if not hours_str:
            return ''

        # Convert OSM format to more readable format
        replacements = {
            'Mo': 'Mon',
            'Tu': 'Tue',
            'We': 'Wed',
            'Th': 'Thu',
            'Fr': 'Fri',
            'Sa': 'Sat',
            'Su': 'Sun',
            '-': ' - ',
            ';': ', ',
            'PH': 'Holidays'
        }

        result = hours_str
        for old, new in replacements.items():
            result = result.replace(old, new)

        return result

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

    def _sort_by_distance(
        self,
        locations: List[Dict],
        user_lat: float,
        user_lon: float
    ) -> List[Dict]:
        """Sort locations by distance from user using Haversine formula"""

        def haversine_distance(loc):
            R = 6371  # Earth's radius in km
            lat1 = math.radians(user_lat)
            lat2 = math.radians(loc['latitude'])
            dlat = math.radians(loc['latitude'] - user_lat)
            dlon = math.radians(loc['longitude'] - user_lon)

            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))

            return R * c  # Distance in km

        # Add distance to each location
        for loc in locations:
            loc['distance_km'] = round(haversine_distance(loc), 2)

        return sorted(locations, key=lambda x: x.get('distance_km', float('inf')))

    def _filter_by_dietary(
        self,
        locations: List[Dict],
        dietary_restrictions: List[str]
    ) -> List[Dict]:
        """Filter locations by dietary restrictions if they have that info"""
        # Only filter if location has dietary info, otherwise keep it
        filtered = []
        for loc in locations:
            if not loc.get('dietary_options'):
                filtered.append(loc)  # Keep locations without dietary info
            elif any(diet in loc['dietary_options'] for diet in dietary_restrictions):
                filtered.append(loc)
        return filtered

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
                    'address': location_data.get('address', 'Address not available'),
                    'latitude': str(location_data['latitude']),
                    'longitude': str(location_data['longitude']),
                    'type': location_data.get('type', 'food_assistance'),
                    'hours': location_data.get('hours', ''),
                    'phone': location_data.get('phone', ''),
                    'website': location_data.get('website', ''),
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
