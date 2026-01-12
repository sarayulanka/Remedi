import requests
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class FDAService:
    def __init__(self):
        self.api_key = os.getenv('FDA_API_KEY')
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
    
    def search_foods_by_nutrient(self, nutrient_name: str, limit: int = 10) -> List[Dict]:
        """Search for foods rich in a specific nutrient"""
        try:
            # Search for foods
            search_url = f"{self.base_url}/foods/search"
            params = {
                'api_key': self.api_key,
                'query': nutrient_name,
                'pageSize': limit,
                'dataType': ['Foundation', 'SR Legacy']  # Most reliable data types
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            foods = []
            
            if 'foods' in data:
                for food in data['foods']:
                    foods.append({
                        'fdcId': food.get('fdcId'),
                        'description': food.get('description'),
                        'dataType': food.get('dataType'),
                        'nutrients': self._extract_nutrients(food.get('foodNutrients', []))
                    })
            
            return foods
        except Exception as e:
            print(f"Error searching FDA database: {str(e)}")
            return []
    
    def get_food_details(self, fdc_id: int) -> Optional[Dict]:
        """Get detailed information about a specific food"""
        try:
            url = f"{self.base_url}/food/{fdc_id}"
            params = {'api_key': self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
        except Exception as e:
            print(f"Error getting food details: {str(e)}")
            return None
    
    def find_foods_for_condition(self, condition: str, beneficial_nutrients: List[str]) -> List[Dict]:
        """Find foods that contain beneficial nutrients for a condition"""
        all_foods = {}
        
        # Search for each beneficial nutrient
        for nutrient in beneficial_nutrients:
            foods = self.search_foods_by_nutrient(nutrient, limit=5)
            for food in foods:
                fdc_id = food['fdcId']
                if fdc_id not in all_foods:
                    all_foods[fdc_id] = food
                    all_foods[fdc_id]['beneficial_for'] = [nutrient]
                else:
                    all_foods[fdc_id]['beneficial_for'].append(nutrient)
        
        # Sort by number of beneficial nutrients
        sorted_foods = sorted(
            all_foods.values(),
            key=lambda x: len(x.get('beneficial_for', [])),
            reverse=True
        )
        
        return sorted_foods[:10]
    
    def _extract_nutrients(self, food_nutrients: List[Dict]) -> List[Dict]:
        """Extract key nutrients from food nutrient data"""
        nutrients = []
        for nutrient in food_nutrients[:10]:  # Top 10 nutrients
            nutrients.append({
                'name': nutrient.get('nutrientName'),
                'amount': nutrient.get('value'),
                'unit': nutrient.get('unitName')
            })
        return nutrients
    
    def get_nutrient_recommendations(self, condition: str) -> Dict[str, List[str]]:
        """Get nutrient recommendations for common conditions"""
        # This is a knowledge base of condition -> beneficial nutrients
        # In production, this could be expanded or pulled from a database
        recommendations = {
            'skin_inflammation': {
                'nutrients': ['Vitamin E', 'Vitamin C', 'Omega-3', 'Zinc'],
                'foods': ['almonds', 'citrus fruits', 'fish', 'seeds']
            },
            'boil': {
                'nutrients': ['Vitamin C', 'Vitamin A', 'Zinc', 'Iron'],
                'foods': ['citrus fruits', 'carrots', 'spinach', 'beans']
            },
            'sore': {
                'nutrients': ['Vitamin C', 'Vitamin B12', 'Iron', 'Folate'],
                'foods': ['oranges', 'leafy greens', 'fortified cereals', 'legumes']
            },
            'dry_skin': {
                'nutrients': ['Vitamin E', 'Omega-3', 'Vitamin A', 'Biotin'],
                'foods': ['avocado', 'nuts', 'sweet potato', 'eggs']
            },
            'acne': {
                'nutrients': ['Zinc', 'Vitamin A', 'Omega-3', 'Vitamin E'],
                'foods': ['pumpkin seeds', 'carrots', 'salmon', 'almonds']
            },
            'rash': {
                'nutrients': ['Vitamin C', 'Vitamin E', 'Quercetin', 'Omega-3'],
                'foods': ['berries', 'nuts', 'onions', 'fish']
            },
            'wound_healing': {
                'nutrients': ['Vitamin C', 'Zinc', 'Protein', 'Vitamin A'],
                'foods': ['citrus fruits', 'meat', 'eggs', 'carrots']
            },
            'general_inflammation': {
                'nutrients': ['Omega-3', 'Vitamin C', 'Vitamin E', 'Curcumin'],
                'foods': ['fish', 'berries', 'nuts', 'turmeric']
            }
        }
        
        # Try to match the condition
        condition_lower = condition.lower().replace(' ', '_')
        for key in recommendations:
            if key in condition_lower or condition_lower in key:
                return recommendations[key]
        
        # Default to general inflammation
        return recommendations['general_inflammation']
