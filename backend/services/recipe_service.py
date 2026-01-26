import requests
from typing import List, Dict, Optional

class RecipeService:
    """Service to fetch recipes from TheMealDB API (completely free, no API key needed)"""

    def __init__(self):
        # TheMealDB is free and requires no API key
        self.base_url = "https://www.themealdb.com/api/json/v1/1"

    def search_recipes_by_ingredients(
        self,
        ingredients: List[str],
        number: int = 5,
        diet: str = None
    ) -> List[Dict]:
        """Search for recipes containing specific ingredients - ensures at least 2 recipes"""

        all_recipes = []
        seen_ids = set()

        # Search for each ingredient
        for ingredient in ingredients[:5]:  # Try up to 5 ingredients
            try:
                response = requests.get(
                    f"{self.base_url}/filter.php",
                    params={'i': ingredient},
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                if data.get('meals'):
                    for meal in data['meals'][:4]:
                        meal_id = meal['idMeal']
                        if meal_id not in seen_ids:
                            seen_ids.add(meal_id)
                            details = self._get_recipe_details(meal_id)
                            if details:
                                all_recipes.append(details)

                # Stop if we have enough
                if len(all_recipes) >= number:
                    break

            except Exception as e:
                print(f"TheMealDB search error for '{ingredient}': {str(e)}")
                continue

        # If we don't have at least 2 recipes, try categories or random
        if len(all_recipes) < 2:
            additional = self._get_fallback_recipes(ingredients)
            for recipe in additional:
                if recipe['id'] not in seen_ids:
                    all_recipes.append(recipe)
                    if len(all_recipes) >= number:
                        break

        return all_recipes[:number]

    def search_recipes_by_nutrients(
        self,
        nutrients: List[str],
        number: int = 5
    ) -> List[Dict]:
        """Search for recipes based on nutrients - ensures at least 2 recipes"""

        # Map nutrients to ingredients that are high in those nutrients
        nutrient_to_ingredients = {
            'vitamin c': ['orange', 'lemon', 'lime', 'strawberry', 'pepper', 'broccoli'],
            'vitamin a': ['carrot', 'sweet potato', 'spinach', 'kale', 'mango'],
            'vitamin e': ['almond', 'spinach', 'avocado', 'sunflower'],
            'vitamin d': ['salmon', 'egg', 'mushroom', 'tuna'],
            'vitamin b12': ['salmon', 'beef', 'egg', 'chicken'],
            'vitamin b6': ['chicken', 'salmon', 'potato', 'banana'],
            'iron': ['spinach', 'beef', 'lentil', 'chicken', 'bean'],
            'zinc': ['beef', 'chicken', 'lamb', 'pork'],
            'magnesium': ['spinach', 'almond', 'avocado', 'banana'],
            'omega-3': ['salmon', 'tuna', 'sardine', 'mackerel'],
            'omega 3': ['salmon', 'tuna', 'sardine', 'mackerel'],
            'protein': ['chicken', 'beef', 'egg', 'salmon', 'tofu'],
            'fiber': ['oat', 'bean', 'lentil', 'apple', 'broccoli'],
            'potassium': ['banana', 'potato', 'spinach', 'avocado'],
            'calcium': ['milk', 'cheese', 'yogurt', 'spinach'],
            'antioxidants': ['blueberry', 'strawberry', 'spinach', 'tomato'],
            'folate': ['spinach', 'lentil', 'asparagus', 'avocado'],
            'collagen': ['chicken', 'beef', 'bone', 'fish'],
        }

        # Find relevant ingredients based on nutrients
        relevant_ingredients = []
        for nutrient in nutrients:
            nutrient_lower = nutrient.lower()
            for key, ingredients in nutrient_to_ingredients.items():
                if key in nutrient_lower or nutrient_lower in key:
                    relevant_ingredients.extend(ingredients)

        # Remove duplicates while preserving order
        unique_ingredients = list(dict.fromkeys(relevant_ingredients))

        if unique_ingredients:
            recipes = self.search_recipes_by_ingredients(unique_ingredients[:6], max(number, 5))
            if len(recipes) >= 2:
                return recipes[:number]

        # Ensure we always have at least 2 recipes
        fallback = self._get_fallback_recipes(['chicken', 'salmon', 'vegetable'])
        return fallback[:max(number, 2)]

    def _get_recipe_details(self, meal_id: str) -> Optional[Dict]:
        """Get detailed information about a recipe from TheMealDB"""

        try:
            response = requests.get(
                f"{self.base_url}/lookup.php",
                params={'i': meal_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data.get('meals') or not data['meals'][0]:
                return None

            meal = data['meals'][0]

            # Extract ingredients and measurements
            ingredients = []
            for i in range(1, 21):
                ingredient = meal.get(f'strIngredient{i}', '').strip()
                measure = meal.get(f'strMeasure{i}', '').strip()
                if ingredient:
                    ingredients.append({
                        'name': ingredient,
                        'amount': measure,
                        'unit': ''
                    })

            # Parse instructions into steps
            instructions_text = meal.get('strInstructions', '')
            instructions = self._parse_instructions(instructions_text)

            return {
                'id': meal['idMeal'],
                'title': meal['strMeal'],
                'image': meal.get('strMealThumb', ''),
                'readyInMinutes': 30,  # TheMealDB doesn't provide this
                'servings': 4,  # Default serving size
                'sourceUrl': meal.get('strSource', ''),
                'sourceName': 'TheMealDB',
                'summary': f"{meal['strMeal']} - A delicious {meal.get('strCategory', 'meal')} dish from {meal.get('strArea', 'international')} cuisine.",
                'instructions': instructions,
                'ingredients': ingredients,
                'nutrition': self._estimate_nutrition(ingredients),
                'diets': self._infer_diets(ingredients, meal.get('strCategory', '')),
                'cuisines': [meal.get('strArea', 'International')],
                'healthScore': 75,
                'source': 'TheMealDB',
                'category': meal.get('strCategory', ''),
                'youtubeUrl': meal.get('strYoutube', '')
            }

        except Exception as e:
            print(f"Error getting recipe details: {str(e)}")
            return None

    def _parse_instructions(self, instructions_text: str) -> List[str]:
        """Parse instruction text into individual steps and clean formatting"""
        if not instructions_text:
            return ['See source for full instructions']

        import re

        # Split by common delimiters (numbered steps, double newlines)
        steps = re.split(r'\d+\.\s*|\n\n|\r\n\r\n', instructions_text)
        steps = [s.strip() for s in steps if s.strip()]

        # If only one step, try splitting by periods followed by capital letters
        if len(steps) <= 1:
            steps = re.split(r'\.\s+(?=[A-Z])', instructions_text)
            steps = [s.strip() + '.' if not s.endswith('.') else s.strip() for s in steps if s.strip()]

        # Clean each step to remove redundant prefixes
        cleaned_steps = []
        for step in steps:
            cleaned = self._clean_step_text(step)
            if cleaned and len(cleaned) > 3:  # Skip very short fragments
                cleaned_steps.append(cleaned)

        return cleaned_steps[:10] if cleaned_steps else ['See source for full instructions']

    def _clean_step_text(self, step: str) -> str:
        """Remove redundant step prefixes and clean up formatting"""
        import re

        # Remove common step prefixes
        # Patterns: "Step 1:", "STEP 1:", "Step 1.", "Step 1)", "1:", "1)", "1.", "1 -", etc.
        step = re.sub(r'^(?:step\s*)?\d+[\s]*[:.)\-]\s*', '', step, flags=re.IGNORECASE)

        # Remove bullet points and dashes at start
        step = re.sub(r'^[\-•*]\s*', '', step)

        # Clean up extra whitespace
        step = ' '.join(step.split())

        # Ensure first letter is capitalized
        if step:
            step = step[0].upper() + step[1:] if len(step) > 1 else step.upper()

        # Ensure step ends with proper punctuation
        if step and not step[-1] in '.!?':
            step = step + '.'

        return step

    def _estimate_nutrition(self, ingredients: List[Dict]) -> Dict:
        """Estimate basic nutrition based on ingredients"""
        # Basic estimation - in reality you'd use a nutrition API
        has_protein = any(
            ing['name'].lower() in ['chicken', 'beef', 'salmon', 'egg', 'tofu', 'pork', 'lamb', 'fish', 'shrimp']
            for ing in ingredients
        )
        has_carbs = any(
            ing['name'].lower() in ['rice', 'pasta', 'bread', 'potato', 'noodle', 'flour']
            for ing in ingredients
        )

        return {
            'calories': 350 if has_protein else 250,
            'protein': 25 if has_protein else 10,
            'fat': 12,
            'carbs': 30 if has_carbs else 15,
            'fiber': 4,
        }

    def _infer_diets(self, ingredients: List[Dict], category: str) -> List[str]:
        """Infer dietary restrictions based on ingredients"""
        diets = []

        ingredient_names = [ing['name'].lower() for ing in ingredients]
        all_ingredients_text = ' '.join(ingredient_names)

        # Check for meat/fish
        meat_keywords = ['chicken', 'beef', 'pork', 'lamb', 'bacon', 'ham', 'sausage', 'meat']
        fish_keywords = ['salmon', 'tuna', 'fish', 'shrimp', 'prawn', 'crab', 'lobster', 'seafood']

        has_meat = any(kw in all_ingredients_text for kw in meat_keywords)
        has_fish = any(kw in all_ingredients_text for kw in fish_keywords)
        has_dairy = any(kw in all_ingredients_text for kw in ['milk', 'cheese', 'cream', 'butter', 'yogurt'])
        has_eggs = 'egg' in all_ingredients_text

        if not has_meat and not has_fish:
            diets.append('vegetarian')
            if not has_dairy and not has_eggs:
                diets.append('vegan')

        if not has_meat and has_fish:
            diets.append('pescatarian')

        # Check category
        if category and 'vegetarian' in category.lower():
            if 'vegetarian' not in diets:
                diets.append('vegetarian')

        return diets

    def search_by_category(self, category: str, number: int = 5) -> List[Dict]:
        """Search recipes by category (Seafood, Vegetarian, etc.)"""
        try:
            response = requests.get(
                f"{self.base_url}/filter.php",
                params={'c': category},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            recipes = []
            if data.get('meals'):
                for meal in data['meals'][:number]:
                    details = self._get_recipe_details(meal['idMeal'])
                    if details:
                        recipes.append(details)

            return recipes

        except Exception as e:
            print(f"Category search error: {str(e)}")
            return []

    def get_random_recipes(self, number: int = 5) -> List[Dict]:
        """Get random recipes"""
        recipes = []

        for _ in range(number):
            try:
                response = requests.get(
                    f"{self.base_url}/random.php",
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                if data.get('meals') and data['meals'][0]:
                    meal = data['meals'][0]
                    details = self._get_recipe_details(meal['idMeal'])
                    if details and details not in recipes:
                        recipes.append(details)

            except Exception as e:
                print(f"Random recipe error: {str(e)}")
                continue

        return recipes

    def _get_fallback_recipes(self, ingredients: List[str]) -> List[Dict]:
        """Get recipes when search fails - ensures at least 2 recipes"""

        all_recipes = []
        seen_ids = set()

        # Try to find by common categories based on ingredients
        category_map = {
            'chicken': 'Chicken',
            'beef': 'Beef',
            'lamb': 'Lamb',
            'pork': 'Pork',
            'fish': 'Seafood',
            'salmon': 'Seafood',
            'tuna': 'Seafood',
            'seafood': 'Seafood',
            'pasta': 'Pasta',
            'vegetable': 'Vegetarian',
            'spinach': 'Vegetarian',
            'vegan': 'Vegan',
            'dessert': 'Dessert',
        }

        # Try category-based search
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            for key, category in category_map.items():
                if key in ingredient_lower:
                    recipes = self.search_by_category(category, 5)
                    for recipe in recipes:
                        if recipe['id'] not in seen_ids:
                            seen_ids.add(recipe['id'])
                            all_recipes.append(recipe)
                    if len(all_recipes) >= 5:
                        return all_recipes[:5]

        # If still not enough, add random recipes
        if len(all_recipes) < 2:
            random_recipes = self.get_random_recipes(5 - len(all_recipes))
            for recipe in random_recipes:
                if recipe['id'] not in seen_ids:
                    all_recipes.append(recipe)

        return all_recipes[:5] if all_recipes else self.get_random_recipes(5)


# Create singleton instance
recipe_service = RecipeService()
