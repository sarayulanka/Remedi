import requests
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class RecipeService:
    """Service to fetch recipes from Spoonacular API"""

    def __init__(self):
        # Spoonacular API key - you can get a free one at spoonacular.com/food-api
        self.api_key = os.getenv('SPOONACULAR_API_KEY', '')
        self.base_url = "https://api.spoonacular.com"

    def search_recipes_by_ingredients(
        self,
        ingredients: List[str],
        number: int = 5,
        diet: str = None
    ) -> List[Dict]:
        """Search for recipes containing specific ingredients"""

        # If no API key, use fallback recipes
        if not self.api_key:
            return self._get_fallback_recipes(ingredients)

        try:
            params = {
                'apiKey': self.api_key,
                'ingredients': ','.join(ingredients),
                'number': number,
                'ranking': 2,  # Maximize used ingredients
                'ignorePantry': True
            }

            if diet:
                params['diet'] = diet

            response = requests.get(
                f"{self.base_url}/recipes/findByIngredients",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            recipes = response.json()

            # Get detailed info for each recipe
            detailed_recipes = []
            for recipe in recipes[:5]:
                details = self._get_recipe_details(recipe['id'])
                if details:
                    detailed_recipes.append(details)

            return detailed_recipes if detailed_recipes else self._get_fallback_recipes(ingredients)

        except Exception as e:
            print(f"Spoonacular API error: {str(e)}")
            return self._get_fallback_recipes(ingredients)

    def search_recipes_by_nutrients(
        self,
        nutrients: List[str],
        number: int = 5
    ) -> List[Dict]:
        """Search for recipes high in specific nutrients"""

        if not self.api_key:
            return self._get_nutrient_based_fallback_recipes(nutrients)

        try:
            # Map nutrient names to Spoonacular parameters
            nutrient_params = self._map_nutrients_to_params(nutrients)

            params = {
                'apiKey': self.api_key,
                'number': number,
                **nutrient_params
            }

            response = requests.get(
                f"{self.base_url}/recipes/findByNutrients",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            recipes = response.json()

            # Get detailed info
            detailed_recipes = []
            for recipe in recipes[:5]:
                details = self._get_recipe_details(recipe['id'])
                if details:
                    detailed_recipes.append(details)

            return detailed_recipes if detailed_recipes else self._get_nutrient_based_fallback_recipes(nutrients)

        except Exception as e:
            print(f"Spoonacular nutrient search error: {str(e)}")
            return self._get_nutrient_based_fallback_recipes(nutrients)

    def _get_recipe_details(self, recipe_id: int) -> Optional[Dict]:
        """Get detailed information about a recipe"""

        if not self.api_key:
            return None

        try:
            params = {
                'apiKey': self.api_key,
                'includeNutrition': True
            }

            response = requests.get(
                f"{self.base_url}/recipes/{recipe_id}/information",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            # Extract key nutrients
            nutrients = {}
            if 'nutrition' in data and 'nutrients' in data['nutrition']:
                for nutrient in data['nutrition']['nutrients']:
                    nutrients[nutrient['name']] = {
                        'amount': nutrient['amount'],
                        'unit': nutrient['unit'],
                        'percentOfDailyNeeds': nutrient.get('percentOfDailyNeeds', 0)
                    }

            return {
                'id': data['id'],
                'title': data['title'],
                'image': data.get('image', ''),
                'readyInMinutes': data.get('readyInMinutes', 30),
                'servings': data.get('servings', 4),
                'sourceUrl': data.get('sourceUrl', ''),
                'sourceName': data.get('sourceName', 'Spoonacular'),
                'summary': self._clean_html(data.get('summary', '')),
                'instructions': self._format_instructions(data.get('analyzedInstructions', [])),
                'ingredients': [
                    {
                        'name': ing['name'],
                        'amount': ing['amount'],
                        'unit': ing['unit']
                    }
                    for ing in data.get('extendedIngredients', [])
                ],
                'nutrition': {
                    'calories': nutrients.get('Calories', {}).get('amount', 0),
                    'protein': nutrients.get('Protein', {}).get('amount', 0),
                    'fat': nutrients.get('Fat', {}).get('amount', 0),
                    'carbs': nutrients.get('Carbohydrates', {}).get('amount', 0),
                    'fiber': nutrients.get('Fiber', {}).get('amount', 0),
                    'vitaminC': nutrients.get('Vitamin C', {}).get('amount', 0),
                    'vitaminA': nutrients.get('Vitamin A', {}).get('amount', 0),
                    'iron': nutrients.get('Iron', {}).get('amount', 0),
                    'zinc': nutrients.get('Zinc', {}).get('amount', 0),
                },
                'diets': data.get('diets', []),
                'cuisines': data.get('cuisines', []),
                'healthScore': data.get('healthScore', 0),
                'source': 'Spoonacular'
            }

        except Exception as e:
            print(f"Error getting recipe details: {str(e)}")
            return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        clean = re.sub('<[^<]+?>', '', text)
        return clean[:500] + '...' if len(clean) > 500 else clean

    def _format_instructions(self, analyzed_instructions: List) -> List[str]:
        """Format analyzed instructions into simple steps"""
        steps = []
        for instruction in analyzed_instructions:
            for step in instruction.get('steps', []):
                steps.append(step['step'])
        return steps if steps else ['See source for full instructions']

    def _map_nutrients_to_params(self, nutrients: List[str]) -> Dict:
        """Map nutrient names to Spoonacular API parameters"""
        params = {}

        nutrient_mapping = {
            'vitamin c': ('minVitaminC', 30),
            'vitamin a': ('minVitaminA', 500),
            'vitamin d': ('minVitaminD', 10),
            'vitamin e': ('minVitaminE', 5),
            'vitamin b12': ('minVitaminB12', 2),
            'iron': ('minIron', 5),
            'zinc': ('minZinc', 5),
            'magnesium': ('minMagnesium', 50),
            'potassium': ('minPotassium', 300),
            'calcium': ('minCalcium', 100),
            'fiber': ('minFiber', 5),
            'protein': ('minProtein', 15),
            'omega-3': ('minFat', 10),  # Closest proxy
            'omega 3': ('minFat', 10),
        }

        for nutrient in nutrients[:3]:  # Limit to 3 nutrients
            nutrient_lower = nutrient.lower()
            for key, (param, value) in nutrient_mapping.items():
                if key in nutrient_lower:
                    params[param] = value
                    break

        return params

    def _get_fallback_recipes(self, ingredients: List[str]) -> List[Dict]:
        """Comprehensive fallback recipes when API is unavailable"""

        # Large database of recipes organized by key ingredient
        recipe_database = {
            'salmon': [
                {
                    'id': 'fallback_salmon_1',
                    'title': 'Honey Garlic Glazed Salmon',
                    'image': 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=600',
                    'readyInMinutes': 25,
                    'servings': 4,
                    'summary': 'Delicious honey garlic salmon with a perfect glaze. Rich in omega-3 fatty acids and protein.',
                    'instructions': [
                        'Preheat oven to 400F (200C)',
                        'Mix 3 tbsp honey, 2 tbsp soy sauce, 3 minced garlic cloves, and 1 tbsp olive oil',
                        'Place salmon fillets on a lined baking sheet',
                        'Brush generously with the honey garlic mixture',
                        'Bake for 12-15 minutes until salmon flakes easily',
                        'Garnish with sesame seeds and green onions'
                    ],
                    'ingredients': [
                        {'name': 'salmon fillets', 'amount': 4, 'unit': 'pieces'},
                        {'name': 'honey', 'amount': 3, 'unit': 'tbsp'},
                        {'name': 'soy sauce', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'garlic cloves', 'amount': 3, 'unit': 'cloves'},
                        {'name': 'olive oil', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 320, 'protein': 34, 'fat': 14, 'carbs': 12, 'omega3': 2.5},
                    'healthScore': 92,
                    'source': 'Remedi Recipes'
                },
                {
                    'id': 'fallback_salmon_2',
                    'title': 'Lemon Herb Baked Salmon',
                    'image': 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=600',
                    'readyInMinutes': 20,
                    'servings': 4,
                    'summary': 'Light and refreshing lemon herb salmon, perfect for a healthy dinner.',
                    'instructions': [
                        'Preheat oven to 375F (190C)',
                        'Season salmon with salt, pepper, and dried herbs',
                        'Top with lemon slices and fresh dill',
                        'Drizzle with olive oil',
                        'Bake for 15-18 minutes',
                        'Serve with a squeeze of fresh lemon'
                    ],
                    'ingredients': [
                        {'name': 'salmon fillets', 'amount': 4, 'unit': 'pieces'},
                        {'name': 'lemon', 'amount': 2, 'unit': 'whole'},
                        {'name': 'fresh dill', 'amount': 0.25, 'unit': 'cup'},
                        {'name': 'olive oil', 'amount': 2, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 280, 'protein': 33, 'fat': 15, 'carbs': 2, 'omega3': 2.8},
                    'healthScore': 95,
                    'source': 'Remedi Recipes'
                }
            ],
            'spinach': [
                {
                    'id': 'fallback_spinach_1',
                    'title': 'Garlic Sauteed Spinach',
                    'image': 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600',
                    'readyInMinutes': 10,
                    'servings': 4,
                    'summary': 'Quick and healthy sauteed spinach loaded with iron and vitamins.',
                    'instructions': [
                        'Heat olive oil in a large pan over medium heat',
                        'Add minced garlic and cook for 30 seconds',
                        'Add spinach in batches, stirring until wilted',
                        'Season with salt, pepper, and a pinch of red pepper flakes',
                        'Finish with a squeeze of lemon juice',
                        'Serve immediately as a side dish'
                    ],
                    'ingredients': [
                        {'name': 'fresh spinach', 'amount': 1, 'unit': 'lb'},
                        {'name': 'garlic cloves', 'amount': 4, 'unit': 'cloves'},
                        {'name': 'olive oil', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'lemon juice', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 80, 'protein': 4, 'fat': 5, 'carbs': 6, 'iron': 4.5},
                    'healthScore': 98,
                    'source': 'Remedi Recipes'
                },
                {
                    'id': 'fallback_spinach_2',
                    'title': 'Spinach and Feta Stuffed Chicken',
                    'image': 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=600',
                    'readyInMinutes': 35,
                    'servings': 4,
                    'summary': 'Juicy chicken breast stuffed with spinach and feta cheese.',
                    'instructions': [
                        'Preheat oven to 375F (190C)',
                        'Mix chopped spinach with crumbled feta and garlic',
                        'Cut a pocket in each chicken breast',
                        'Stuff with spinach mixture and secure with toothpicks',
                        'Season and bake for 25-30 minutes',
                        'Let rest 5 minutes before serving'
                    ],
                    'ingredients': [
                        {'name': 'chicken breasts', 'amount': 4, 'unit': 'pieces'},
                        {'name': 'spinach', 'amount': 2, 'unit': 'cups'},
                        {'name': 'feta cheese', 'amount': 0.5, 'unit': 'cup'},
                        {'name': 'garlic', 'amount': 2, 'unit': 'cloves'}
                    ],
                    'nutrition': {'calories': 320, 'protein': 42, 'fat': 12, 'carbs': 4, 'iron': 3.2},
                    'healthScore': 88,
                    'source': 'Remedi Recipes'
                }
            ],
            'sweet potato': [
                {
                    'id': 'fallback_sweetpotato_1',
                    'title': 'Roasted Sweet Potato with Cinnamon',
                    'image': 'https://images.unsplash.com/photo-1596097635121-14b63a7b0c56?w=600',
                    'readyInMinutes': 45,
                    'servings': 4,
                    'summary': 'Naturally sweet roasted potatoes with warming cinnamon. High in vitamin A and fiber.',
                    'instructions': [
                        'Preheat oven to 400F (200C)',
                        'Cut sweet potatoes into 1-inch cubes',
                        'Toss with olive oil, cinnamon, and a pinch of salt',
                        'Spread on baking sheet in single layer',
                        'Roast 35-40 minutes, flipping halfway',
                        'Drizzle with honey before serving'
                    ],
                    'ingredients': [
                        {'name': 'sweet potatoes', 'amount': 4, 'unit': 'medium'},
                        {'name': 'olive oil', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'cinnamon', 'amount': 1, 'unit': 'tsp'},
                        {'name': 'honey', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 180, 'protein': 3, 'fat': 5, 'carbs': 32, 'vitaminA': 400},
                    'healthScore': 90,
                    'source': 'Remedi Recipes'
                }
            ],
            'yogurt': [
                {
                    'id': 'fallback_yogurt_1',
                    'title': 'Greek Yogurt Parfait with Berries',
                    'image': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=600',
                    'readyInMinutes': 5,
                    'servings': 2,
                    'summary': 'Probiotic-rich breakfast parfait with antioxidant berries and crunchy granola.',
                    'instructions': [
                        'In a glass or bowl, add a layer of Greek yogurt',
                        'Add a layer of mixed berries',
                        'Sprinkle with granola',
                        'Repeat layers',
                        'Top with a drizzle of honey',
                        'Serve immediately'
                    ],
                    'ingredients': [
                        {'name': 'Greek yogurt', 'amount': 2, 'unit': 'cups'},
                        {'name': 'mixed berries', 'amount': 1, 'unit': 'cup'},
                        {'name': 'granola', 'amount': 0.5, 'unit': 'cup'},
                        {'name': 'honey', 'amount': 2, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 280, 'protein': 18, 'fat': 6, 'carbs': 40, 'probiotics': True},
                    'healthScore': 85,
                    'source': 'Remedi Recipes'
                },
                {
                    'id': 'fallback_yogurt_2',
                    'title': 'Creamy Yogurt Dill Sauce',
                    'image': 'https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=600',
                    'readyInMinutes': 5,
                    'servings': 8,
                    'summary': 'Versatile probiotic sauce perfect for fish, vegetables, or as a dip.',
                    'instructions': [
                        'Combine yogurt with chopped fresh dill',
                        'Add minced garlic and lemon juice',
                        'Season with salt and pepper',
                        'Mix well until smooth',
                        'Refrigerate for 30 minutes to let flavors meld',
                        'Serve with fish, veggies, or pita'
                    ],
                    'ingredients': [
                        {'name': 'Greek yogurt', 'amount': 1, 'unit': 'cup'},
                        {'name': 'fresh dill', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'garlic', 'amount': 1, 'unit': 'clove'},
                        {'name': 'lemon juice', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 25, 'protein': 3, 'fat': 0, 'carbs': 2, 'probiotics': True},
                    'healthScore': 92,
                    'source': 'Remedi Recipes'
                }
            ],
            'avocado': [
                {
                    'id': 'fallback_avocado_1',
                    'title': 'Classic Guacamole',
                    'image': 'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=600',
                    'readyInMinutes': 10,
                    'servings': 6,
                    'summary': 'Fresh homemade guacamole rich in healthy fats and vitamin E.',
                    'instructions': [
                        'Cut avocados in half and remove pit',
                        'Scoop flesh into bowl and mash with fork',
                        'Add diced onion, tomato, and jalapeno',
                        'Mix in lime juice and cilantro',
                        'Season with salt and cumin',
                        'Serve with tortilla chips or veggies'
                    ],
                    'ingredients': [
                        {'name': 'ripe avocados', 'amount': 3, 'unit': 'whole'},
                        {'name': 'lime juice', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'red onion', 'amount': 0.25, 'unit': 'cup'},
                        {'name': 'cilantro', 'amount': 0.25, 'unit': 'cup'},
                        {'name': 'tomato', 'amount': 1, 'unit': 'medium'}
                    ],
                    'nutrition': {'calories': 160, 'protein': 2, 'fat': 14, 'carbs': 9, 'vitaminE': 2.5},
                    'healthScore': 88,
                    'source': 'Remedi Recipes'
                },
                {
                    'id': 'fallback_avocado_2',
                    'title': 'Avocado Toast with Poached Egg',
                    'image': 'https://images.unsplash.com/photo-1525351484163-7529414344d8?w=600',
                    'readyInMinutes': 15,
                    'servings': 2,
                    'summary': 'Trendy and nutritious breakfast with healthy fats and protein.',
                    'instructions': [
                        'Toast bread until golden brown',
                        'Mash avocado with lemon juice, salt, and pepper',
                        'Spread avocado mixture on toast',
                        'Poach eggs in simmering water for 3-4 minutes',
                        'Place poached egg on top of avocado',
                        'Garnish with red pepper flakes and microgreens'
                    ],
                    'ingredients': [
                        {'name': 'whole grain bread', 'amount': 2, 'unit': 'slices'},
                        {'name': 'avocado', 'amount': 1, 'unit': 'whole'},
                        {'name': 'eggs', 'amount': 2, 'unit': 'whole'},
                        {'name': 'lemon juice', 'amount': 1, 'unit': 'tsp'}
                    ],
                    'nutrition': {'calories': 350, 'protein': 14, 'fat': 22, 'carbs': 26, 'vitaminE': 3.0},
                    'healthScore': 90,
                    'source': 'Remedi Recipes'
                }
            ],
            'berries': [
                {
                    'id': 'fallback_berries_1',
                    'title': 'Antioxidant Berry Smoothie Bowl',
                    'image': 'https://images.unsplash.com/photo-1590301157890-4810ed352733?w=600',
                    'readyInMinutes': 10,
                    'servings': 2,
                    'summary': 'Vibrant smoothie bowl packed with antioxidants and vitamins.',
                    'instructions': [
                        'Blend frozen berries with banana and a splash of almond milk',
                        'Blend until thick and creamy',
                        'Pour into bowls',
                        'Top with fresh berries, granola, and chia seeds',
                        'Drizzle with honey',
                        'Serve immediately'
                    ],
                    'ingredients': [
                        {'name': 'frozen mixed berries', 'amount': 2, 'unit': 'cups'},
                        {'name': 'banana', 'amount': 1, 'unit': 'whole'},
                        {'name': 'almond milk', 'amount': 0.5, 'unit': 'cup'},
                        {'name': 'chia seeds', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 220, 'protein': 4, 'fat': 3, 'carbs': 48, 'vitaminC': 45},
                    'healthScore': 95,
                    'source': 'Remedi Recipes'
                }
            ],
            'eggs': [
                {
                    'id': 'fallback_eggs_1',
                    'title': 'Vegetable Frittata',
                    'image': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600',
                    'readyInMinutes': 25,
                    'servings': 6,
                    'summary': 'Protein-packed frittata loaded with colorful vegetables.',
                    'instructions': [
                        'Preheat oven to 375F (190C)',
                        'Saute onions, peppers, and spinach in oven-safe pan',
                        'Whisk eggs with milk, salt, and pepper',
                        'Pour egg mixture over vegetables',
                        'Cook on stovetop until edges set, about 5 minutes',
                        'Transfer to oven and bake 10-15 minutes until set'
                    ],
                    'ingredients': [
                        {'name': 'eggs', 'amount': 8, 'unit': 'whole'},
                        {'name': 'bell peppers', 'amount': 1, 'unit': 'cup'},
                        {'name': 'spinach', 'amount': 1, 'unit': 'cup'},
                        {'name': 'onion', 'amount': 0.5, 'unit': 'cup'},
                        {'name': 'milk', 'amount': 0.25, 'unit': 'cup'}
                    ],
                    'nutrition': {'calories': 180, 'protein': 12, 'fat': 12, 'carbs': 4, 'vitaminB12': 1.5},
                    'healthScore': 88,
                    'source': 'Remedi Recipes'
                }
            ],
            'oats': [
                {
                    'id': 'fallback_oats_1',
                    'title': 'Overnight Oats with Berries',
                    'image': 'https://images.unsplash.com/photo-1517673400267-0251440c45dc?w=600',
                    'readyInMinutes': 5,
                    'servings': 2,
                    'summary': 'Fiber-rich make-ahead breakfast that supports heart health.',
                    'instructions': [
                        'Combine oats, milk, and yogurt in a jar',
                        'Add chia seeds and a touch of honey',
                        'Stir well and refrigerate overnight',
                        'In the morning, top with fresh berries',
                        'Add a sprinkle of nuts if desired',
                        'Eat cold or heat for 2 minutes'
                    ],
                    'ingredients': [
                        {'name': 'rolled oats', 'amount': 1, 'unit': 'cup'},
                        {'name': 'almond milk', 'amount': 1, 'unit': 'cup'},
                        {'name': 'Greek yogurt', 'amount': 0.5, 'unit': 'cup'},
                        {'name': 'chia seeds', 'amount': 1, 'unit': 'tbsp'},
                        {'name': 'mixed berries', 'amount': 0.5, 'unit': 'cup'}
                    ],
                    'nutrition': {'calories': 280, 'protein': 12, 'fat': 8, 'carbs': 42, 'fiber': 8},
                    'healthScore': 92,
                    'source': 'Remedi Recipes'
                }
            ],
            'turmeric': [
                {
                    'id': 'fallback_turmeric_1',
                    'title': 'Golden Turmeric Milk (Golden Latte)',
                    'image': 'https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=600',
                    'readyInMinutes': 10,
                    'servings': 2,
                    'summary': 'Anti-inflammatory beverage with powerful curcumin from turmeric.',
                    'instructions': [
                        'Heat milk in a saucepan over medium heat',
                        'Whisk in turmeric, ginger, and cinnamon',
                        'Add a pinch of black pepper (helps absorption)',
                        'Simmer for 5 minutes, stirring occasionally',
                        'Sweeten with honey to taste',
                        'Strain if desired and serve warm'
                    ],
                    'ingredients': [
                        {'name': 'milk (dairy or plant-based)', 'amount': 2, 'unit': 'cups'},
                        {'name': 'turmeric powder', 'amount': 1, 'unit': 'tsp'},
                        {'name': 'ginger', 'amount': 0.5, 'unit': 'tsp'},
                        {'name': 'cinnamon', 'amount': 0.25, 'unit': 'tsp'},
                        {'name': 'honey', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 120, 'protein': 4, 'fat': 3, 'carbs': 18, 'curcumin': True},
                    'healthScore': 90,
                    'source': 'Remedi Recipes'
                }
            ],
            'ginger': [
                {
                    'id': 'fallback_ginger_1',
                    'title': 'Fresh Ginger Tea with Lemon',
                    'image': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=600',
                    'readyInMinutes': 10,
                    'servings': 2,
                    'summary': 'Soothing digestive tea with anti-inflammatory ginger.',
                    'instructions': [
                        'Slice fresh ginger into thin pieces',
                        'Bring water to a boil',
                        'Add ginger and simmer for 5-10 minutes',
                        'Remove from heat and add lemon juice',
                        'Strain into cups',
                        'Add honey to taste and serve warm'
                    ],
                    'ingredients': [
                        {'name': 'fresh ginger', 'amount': 2, 'unit': 'inches'},
                        {'name': 'water', 'amount': 2, 'unit': 'cups'},
                        {'name': 'lemon juice', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'honey', 'amount': 1, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 35, 'protein': 0, 'fat': 0, 'carbs': 9, 'gingerols': True},
                    'healthScore': 95,
                    'source': 'Remedi Recipes'
                }
            ],
            'nuts': [
                {
                    'id': 'fallback_nuts_1',
                    'title': 'Honey Roasted Mixed Nuts',
                    'image': 'https://images.unsplash.com/photo-1526346698789-22fd84314424?w=600',
                    'readyInMinutes': 20,
                    'servings': 8,
                    'summary': 'Heart-healthy snack rich in omega-3s and vitamin E.',
                    'instructions': [
                        'Preheat oven to 325F (165C)',
                        'Mix nuts with honey, cinnamon, and a pinch of salt',
                        'Spread on lined baking sheet',
                        'Bake 15-18 minutes, stirring halfway',
                        'Let cool completely (they crisp as they cool)',
                        'Store in airtight container'
                    ],
                    'ingredients': [
                        {'name': 'mixed nuts', 'amount': 2, 'unit': 'cups'},
                        {'name': 'honey', 'amount': 2, 'unit': 'tbsp'},
                        {'name': 'cinnamon', 'amount': 0.5, 'unit': 'tsp'},
                        {'name': 'sea salt', 'amount': 0.25, 'unit': 'tsp'}
                    ],
                    'nutrition': {'calories': 200, 'protein': 5, 'fat': 18, 'carbs': 8, 'vitaminE': 4},
                    'healthScore': 82,
                    'source': 'Remedi Recipes'
                }
            ],
            'citrus': [
                {
                    'id': 'fallback_citrus_1',
                    'title': 'Citrus Immunity Booster Juice',
                    'image': 'https://images.unsplash.com/photo-1622597467836-f3285f2131b8?w=600',
                    'readyInMinutes': 5,
                    'servings': 2,
                    'summary': 'Vitamin C powerhouse to support immune function.',
                    'instructions': [
                        'Juice oranges, grapefruit, and lemon',
                        'Add a small piece of fresh ginger to juicer',
                        'Mix all juices together',
                        'Add a pinch of turmeric if desired',
                        'Serve immediately over ice',
                        'Best consumed fresh for maximum vitamins'
                    ],
                    'ingredients': [
                        {'name': 'oranges', 'amount': 3, 'unit': 'whole'},
                        {'name': 'grapefruit', 'amount': 1, 'unit': 'whole'},
                        {'name': 'lemon', 'amount': 1, 'unit': 'whole'},
                        {'name': 'fresh ginger', 'amount': 0.5, 'unit': 'inch'}
                    ],
                    'nutrition': {'calories': 140, 'protein': 2, 'fat': 0, 'carbs': 34, 'vitaminC': 180},
                    'healthScore': 96,
                    'source': 'Remedi Recipes'
                }
            ],
            'leafy greens': [
                {
                    'id': 'fallback_greens_1',
                    'title': 'Green Detox Salad',
                    'image': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600',
                    'readyInMinutes': 15,
                    'servings': 4,
                    'summary': 'Nutrient-dense salad with multiple leafy greens for maximum health benefits.',
                    'instructions': [
                        'Wash and dry all greens thoroughly',
                        'Tear or chop into bite-sized pieces',
                        'Add sliced cucumber and avocado',
                        'Whisk together olive oil, lemon, and honey for dressing',
                        'Toss salad with dressing just before serving',
                        'Top with seeds or nuts for crunch'
                    ],
                    'ingredients': [
                        {'name': 'mixed greens', 'amount': 6, 'unit': 'cups'},
                        {'name': 'kale', 'amount': 2, 'unit': 'cups'},
                        {'name': 'cucumber', 'amount': 1, 'unit': 'whole'},
                        {'name': 'avocado', 'amount': 1, 'unit': 'whole'},
                        {'name': 'olive oil', 'amount': 3, 'unit': 'tbsp'}
                    ],
                    'nutrition': {'calories': 180, 'protein': 4, 'fat': 14, 'carbs': 12, 'vitaminK': 200},
                    'healthScore': 98,
                    'source': 'Remedi Recipes'
                }
            ]
        }

        # Find matching recipes
        matched_recipes = []
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            for key, recipes in recipe_database.items():
                if key in ingredient_lower or ingredient_lower in key:
                    for recipe in recipes:
                        if recipe not in matched_recipes:
                            matched_recipes.append(recipe)

        # If no matches, return a selection of healthy recipes
        if not matched_recipes:
            all_recipes = []
            for recipes in recipe_database.values():
                all_recipes.extend(recipes)
            matched_recipes = all_recipes[:5]

        return matched_recipes[:5]

    def _get_nutrient_based_fallback_recipes(self, nutrients: List[str]) -> List[Dict]:
        """Get recipes based on desired nutrients"""

        # Map nutrients to ingredients
        nutrient_to_ingredients = {
            'vitamin c': ['citrus', 'berries', 'bell peppers'],
            'vitamin a': ['sweet potato', 'carrots', 'spinach'],
            'vitamin e': ['nuts', 'avocado', 'spinach'],
            'vitamin d': ['salmon', 'eggs', 'mushrooms'],
            'vitamin b12': ['salmon', 'eggs', 'dairy'],
            'iron': ['spinach', 'red meat', 'legumes'],
            'zinc': ['oysters', 'pumpkin seeds', 'beef'],
            'magnesium': ['dark chocolate', 'avocado', 'nuts'],
            'omega-3': ['salmon', 'walnuts', 'chia seeds'],
            'omega 3': ['salmon', 'walnuts', 'chia seeds'],
            'protein': ['eggs', 'chicken', 'legumes'],
            'fiber': ['oats', 'berries', 'legumes'],
            'probiotics': ['yogurt', 'kefir', 'sauerkraut'],
            'antioxidants': ['berries', 'dark chocolate', 'leafy greens'],
            'curcumin': ['turmeric'],
            'potassium': ['banana', 'sweet potato', 'spinach'],
            'calcium': ['dairy', 'leafy greens', 'fortified foods']
        }

        # Collect relevant ingredients
        relevant_ingredients = []
        for nutrient in nutrients:
            nutrient_lower = nutrient.lower()
            for key, ingredients in nutrient_to_ingredients.items():
                if key in nutrient_lower or nutrient_lower in key:
                    relevant_ingredients.extend(ingredients)

        # Remove duplicates while preserving order
        seen = set()
        unique_ingredients = []
        for ing in relevant_ingredients:
            if ing not in seen:
                seen.add(ing)
                unique_ingredients.append(ing)

        return self._get_fallback_recipes(unique_ingredients[:5])


# Create singleton instance
recipe_service = RecipeService()
