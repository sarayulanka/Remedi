import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from services.fda_service import FDAService
from services.recipe_service import RecipeService
from fastapi import HTTPException
from database import get_table, DATA_TYPE_SAVED_REMEDY
from services.gamification_service import GamificationService

load_dotenv()

class HealthAnalysisService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.fda_service = FDAService()
        self.recipe_service = RecipeService()
        self.table = get_table()
        self.gamification_service = GamificationService()

    def analyze_health_concern(
        self,
        user_id: str,
        image_base64: Optional[str] = None,
        text_description: Optional[str] = None,
        user_concerns: Optional[str] = None,
        allergies: Optional[List[str]] = None,
        diet_type: Optional[str] = None
    ) -> Dict:
        """Analyze a health concern using image and/or text"""

        if not image_base64 and not text_description:
            raise HTTPException(
                status_code=400,
                detail="Either image or text description is required"
            )

        # Normalize allergies and diet type
        allergies = [a.lower().strip() for a in (allergies or [])]
        diet_type = (diet_type or '').lower().strip()

        # Step 1: Analyze the condition using OpenAI
        condition_analysis = self._analyze_condition(image_base64, text_description, user_concerns)

        # Step 2: Get nutrient recommendations based on the condition
        nutrient_info = self.fda_service.get_nutrient_recommendations(
            condition_analysis['condition_type']
        )

        # Step 3: Search FDA database for specific foods
        recommended_foods = self.fda_service.find_foods_for_condition(
            condition_analysis['condition_type'],
            nutrient_info['nutrients']
        )

        # Step 3.5: Filter foods based on allergies and diet type
        recommended_foods = self._filter_foods_by_preferences(
            recommended_foods, allergies, diet_type
        )

        # Step 3.6: Clean up food names and add info using AI
        cleaned_foods = self._cleanup_foods_with_ai(
            recommended_foods[:8],
            condition_analysis['condition_name']
        )

        # Step 4: Get recipes - try by nutrients first, then by ingredients
        recipes = self.recipe_service.search_recipes_by_nutrients(
            nutrient_info['nutrients'],
            number=10
        )

        # If no recipes from nutrients, try by food ingredients
        if not recipes:
            recipes = self.recipe_service.search_recipes_by_ingredients(
                nutrient_info['foods'][:5],
                number=10
            )

        # Step 4.5: Filter recipes based on allergies and diet type
        recipes = self._filter_recipes_by_preferences(recipes, allergies, diet_type)

        # Step 5: Create comprehensive response with sources
        response = {
            'condition': {
                'name': condition_analysis['condition_name'],
                'type': condition_analysis['condition_type'],
                'explanation': condition_analysis['explanation'],
                'severity': condition_analysis.get('severity', 'mild')
            },
            'remedy': {
                'recommendedNutrients': nutrient_info['nutrients'],
                'nutrientExplanations': nutrient_info.get('nutrient_explanations', {}),
                'foodCategories': nutrient_info['foods'],
                'specificFoods': cleaned_foods,
                'recipes': [
                    {
                        'id': recipe.get('id', ''),
                        'title': recipe.get('title', ''),
                        'image': recipe.get('image', ''),
                        'readyInMinutes': recipe.get('readyInMinutes', 30),
                        'servings': recipe.get('servings', 4),
                        'summary': recipe.get('summary', ''),
                        'instructions': recipe.get('instructions', []),
                        'ingredients': recipe.get('ingredients', []),
                        'nutrition': recipe.get('nutrition', {}),
                        'healthScore': recipe.get('healthScore', 0),
                        'source': recipe.get('source', 'Remedi Recipes'),
                        'sourceUrl': recipe.get('sourceUrl', '')
                    }
                    for recipe in recipes[:5]
                ],
                'explanation': self._generate_remedy_explanation(
                    condition_analysis['condition_name'],
                    nutrient_info
                )
            },
            'sources': {
                'nutritionData': nutrient_info.get('sources', [
                    'FDA FoodData Central',
                    'NIH Office of Dietary Supplements'
                ]),
                'recipeData': 'Spoonacular Recipe Database' if any(r.get('source') == 'Spoonacular' for r in recipes) else 'Remedi Kitchen',
                'citations': [
                    {
                        'name': 'FDA FoodData Central',
                        'url': 'https://fdc.nal.usda.gov/',
                        'description': 'U.S. Department of Agriculture food composition database'
                    },
                    {
                        'name': 'NIH Office of Dietary Supplements',
                        'url': 'https://ods.od.nih.gov/',
                        'description': 'National Institutes of Health dietary supplement fact sheets'
                    },
                    {
                        'name': 'PubMed / National Library of Medicine',
                        'url': 'https://pubmed.ncbi.nlm.nih.gov/',
                        'description': 'Peer-reviewed nutrition and health research'
                    }
                ]
            },
            'disclaimer': 'This information is for educational purposes only and is based on nutritional data from the FDA FoodData Central database and peer-reviewed research from the NIH. It is not a substitute for professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment.'
        }

        # Award the health_explorer badge on first analysis
        try:
            self.gamification_service.award_activity_badge(user_id, 'first_analysis')
        except Exception:
            pass  # Don't let badge failure break the analysis

        return response

    def _analyze_condition(
        self,
        image_base64: Optional[str],
        text_description: Optional[str],
        user_concerns: Optional[str]
    ) -> Dict:
        """Use OpenAI to analyze the health condition"""

        messages = [
            {
                "role": "system",
                "content": """You are a health analysis assistant specializing in nutritional healing. Your role is to carefully analyze the user's specific health concern and provide personalized, condition-specific nutritional guidance based on FDA and NIH research.

CRITICAL: You MUST carefully read and analyze the user's SPECIFIC description. Different health problems require DIFFERENT nutritional approaches. Do NOT give generic responses.

Your task is to:
1. Identify what the condition appears to be in simple, non-medical terms - BE SPECIFIC to what the user describes
2. Provide a clear, condition-specific explanation of:
   - What is likely happening in their body
   - How this particular condition affects their health
   - Why nutritional intervention can help THIS specific issue
3. Categorize the condition using the MOST SPECIFIC matching category:

   SKIN CONDITIONS (each requires different nutrients):
   - acne: Sebum/bacteria related - prioritize Zinc, Vitamin A
   - dry_skin: Barrier dysfunction - prioritize Omega-3, Vitamin E
   - eczema: Immune-mediated - prioritize Omega-3, Vitamin D, Probiotics
   - psoriasis: Autoimmune/cell turnover - prioritize Omega-3, Vitamin D, Selenium
   - rash: Allergic/inflammatory - prioritize Quercetin, Vitamin C
   - skin_inflammation: General - prioritize antioxidants
   - boil: Bacterial infection - prioritize Vitamin C, Zinc for immune support
   - sore: Tissue damage - prioritize healing nutrients
   - wound_healing: Tissue repair - prioritize Vitamin C, Zinc, Protein

   DIGESTIVE CONDITIONS (each has unique nutritional needs):
   - bloating: Gas/fluid - Probiotics, Ginger, Peppermint
   - constipation: Motility - Fiber, Magnesium, Probiotics
   - acid_reflux: Stomach acid - Alkaline foods, Ginger
   - nausea: Stomach upset - Ginger, Vitamin B6
   - digestive_issues: General gut health

   ENERGY/FATIGUE (different root causes):
   - fatigue: Often Iron/B12 deficiency
   - low_energy: Blood sugar/nutrient depletion
   - brain_fog: Cognitive/neurological - Omega-3, B vitamins

   IMMUNE SYSTEM:
   - weak_immunity: Chronic - Vitamin C, D, Zinc
   - cold_symptoms: Acute viral - Vitamin C, Zinc, Elderberry
   - flu_symptoms: Acute viral with fever - similar plus hydration focus

   INFLAMMATION/PAIN:
   - joint_pain: Joint-specific - Omega-3, Glucosamine
   - arthritis: Autoimmune/degenerative - anti-inflammatory focus
   - muscle_pain: Muscle recovery - Magnesium, Potassium
   - general_inflammation: Systemic - broad anti-inflammatory approach

   MENTAL HEALTH:
   - anxiety: Nervous system - Magnesium, L-Theanine
   - stress: Adrenal support - Adaptogens, B vitamins
   - depression: Neurotransmitter support - Omega-3, Vitamin D
   - insomnia: Sleep - Magnesium, Melatonin foods

   CARDIOVASCULAR:
   - high_blood_pressure: - Potassium, Magnesium
   - high_cholesterol: - Fiber, Omega-3, Plant Sterols
   - heart_health: General cardiovascular

   METABOLIC:
   - blood_sugar: Glucose regulation
   - diabetes_support: Comprehensive metabolic
   - weight_loss: Fat metabolism
   - metabolism_boost: Energy expenditure

   OTHER SPECIFIC CONDITIONS:
   - hair_loss, brittle_nails: Keratin nutrients (Biotin, Iron, Zinc)
   - eye_health, dry_eyes: Eye-specific (Vitamin A, Lutein)
   - bone_health, osteoporosis: Bone minerals (Calcium, D, K)
   - allergies, seasonal_allergies: Antihistamine nutrients
   - hormonal_balance, pms_symptoms, menopause_symptoms: Hormone support
   - respiratory_health, asthma_support: Lung function
   - liver_health, detox: Liver support
   - headache, migraine: Magnesium, B2
   - dental_health: Calcium, Vitamin C for gums
   - pregnancy_nutrition: Folate, Iron, DHA

4. Assess severity (mild, moderate, concerning)

Respond in JSON format:
{
    "condition_name": "Specific descriptive name matching their exact concern",
    "condition_type": "most_specific_category_from_list",
    "explanation": "Personalized explanation addressing their SPECIFIC symptoms and why nutrition helps THIS particular issue. Mention what's likely happening in their body and how the right nutrients will help.",
    "severity": "mild|moderate|concerning"
}

IMPORTANT: Your explanation should be UNIQUE to their specific condition. A person with acne should get different information than someone with eczema. A person with anxiety needs different support than someone with fatigue. Be SPECIFIC."""
            }
        ]

        # Build user message
        user_message_parts = []

        if image_base64:
            user_message_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })

        text_content = ""
        if text_description:
            text_content += f"Description: {text_description}\n"
        if user_concerns:
            text_content += f"User concerns: {user_concerns}\n"

        if text_content:
            user_message_parts.append({
                "type": "text",
                "text": text_content
            })

        messages.append({
            "role": "user",
            "content": user_message_parts if image_base64 else text_content
        })

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            result_text = response.choices[0].message.content
            # Clean up potential markdown formatting
            if result_text.startswith('```'):
                result_text = result_text.strip('`').replace('json', '', 1).strip()
            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"Error analyzing condition: {str(e)}")
            # Smart fallback based on text description
            return self._fallback_analysis(text_description, user_concerns)

    def _fallback_analysis(
        self,
        text_description: Optional[str],
        user_concerns: Optional[str]
    ) -> Dict:
        """Provide intelligent fallback analysis when OpenAI fails"""

        combined_text = f"{text_description or ''} {user_concerns or ''}".lower()

        # Comprehensive keyword-based condition detection
        condition_keywords = {
            # Skin conditions
            'acne': (['acne', 'pimple', 'breakout', 'zit', 'blackhead', 'whitehead'], 'acne', 'Acne or breakout',
                     'Your skin may be experiencing excess oil production and bacterial buildup. The right nutrients can help regulate sebum and fight bacteria.'),
            'dry_skin': (['dry skin', 'flaky', 'rough skin', 'peeling', 'cracked skin'], 'dry_skin', 'Dry or flaky skin',
                        'Your skin barrier may be weakened, leading to moisture loss. Healthy fats and vitamins can help rebuild and hydrate from within.'),
            'rash': (['rash', 'red spots', 'itchy skin', 'hives', 'irritation'], 'rash', 'Skin rash or irritation',
                    'This appears to be an inflammatory skin reaction. Anti-inflammatory nutrients can help calm your immune response.'),
            'eczema': (['eczema', 'dermatitis', 'atopic'], 'eczema', 'Eczema',
                      'Eczema involves an overactive immune response affecting your skin barrier. Omega-3s and probiotics can help modulate this response.'),
            'psoriasis': (['psoriasis', 'scaly patches', 'plaques'], 'psoriasis', 'Psoriasis',
                         'Psoriasis causes rapid skin cell turnover. Vitamin D and anti-inflammatory nutrients can help normalize cell growth.'),

            # Digestive conditions
            'bloating': (['bloat', 'bloated', 'gas', 'gassy', 'puffy stomach'], 'bloating', 'Bloating and digestive discomfort',
                        'Your gut may have imbalanced bacteria or slow digestion. Probiotics and digestive aids can restore balance.'),
            'constipation': (['constipat', 'irregular', 'hard stool', 'cant go'], 'constipation', 'Constipation',
                            'Your digestive motility may be sluggish. Fiber, magnesium, and hydration can help restore regularity.'),
            'acid_reflux': (['acid reflux', 'heartburn', 'gerd', 'indigestion'], 'acid_reflux', 'Acid reflux or heartburn',
                           'Stomach acid may be backing up into your esophagus. Alkaline foods and ginger can help neutralize and soothe.'),
            'nausea': (['nausea', 'nauseous', 'queasy', 'sick to stomach'], 'nausea', 'Nausea',
                      'Your stomach lining may be irritated. Ginger and vitamin B6 are proven to help settle an upset stomach.'),

            # Energy and fatigue
            'fatigue': (['tired', 'fatigue', 'exhausted', 'no energy', 'low energy', 'drained'], 'fatigue', 'Fatigue or low energy',
                       'You may be low in key energy nutrients like iron or B12. The right foods can help restore your energy levels naturally.'),
            'brain_fog': (['brain fog', 'cant concentrate', 'fuzzy', 'mental fog', 'forgetful'], 'brain_fog', 'Brain fog and mental clarity issues',
                         'Your brain needs omega-3s and B vitamins for optimal function. These nutrients support neurotransmitter production.'),

            # Mental health
            'anxiety': (['anxiety', 'anxious', 'nervous', 'panic', 'worried', 'on edge'], 'anxiety', 'Anxiety symptoms',
                       'Your nervous system may be overactivated. Magnesium and calming nutrients can help regulate stress responses.'),
            'stress': (['stress', 'stressed', 'overwhelmed', 'burnout'], 'stress', 'Stress-related symptoms',
                      'Chronic stress depletes your B vitamins and magnesium. Replenishing these can help your body cope better.'),
            'depression': (['depression', 'depressed', 'sad', 'hopeless', 'low mood'], 'depression', 'Low mood',
                          'Your brain chemistry may benefit from omega-3s and vitamin D, which support serotonin production.'),
            'insomnia': (['sleep', 'insomnia', 'cant sleep', 'wake up', 'restless'], 'insomnia', 'Sleep difficulties',
                        'Your body may need help producing melatonin. Magnesium and tryptophan-rich foods can improve sleep quality.'),

            # Immune system
            'cold_symptoms': (['cold', 'flu', 'cough', 'sneeze', 'runny nose', 'sore throat', 'congestion'], 'cold_symptoms', 'Cold or flu symptoms',
                             'Your immune system is fighting off a viral infection. Vitamin C, zinc, and elderberry can boost your natural defenses.'),
            'weak_immunity': (['sick often', 'weak immune', 'catch everything', 'always sick'], 'weak_immunity', 'Weakened immunity',
                             'Your immune system may need nutritional support. Key vitamins and minerals can strengthen your natural defenses.'),

            # Pain and inflammation
            'headache': (['headache', 'head pain', 'migraine', 'head hurts'], 'headache', 'Headache',
                        'Headaches can be linked to magnesium deficiency. Proper hydration and magnesium-rich foods can help prevent them.'),
            'joint_pain': (['joint', 'arthritis', 'knee pain', 'back pain', 'stiff'], 'joint_pain', 'Joint discomfort',
                          'Inflammation in your joints may be causing pain. Omega-3s and anti-inflammatory foods can help reduce this.'),
            'muscle_pain': (['muscle pain', 'sore muscles', 'cramp', 'muscle ache'], 'muscle_pain', 'Muscle pain',
                           'Your muscles may be low in electrolytes or recovering from strain. Magnesium and potassium can help recovery.'),

            # Hair and appearance
            'hair_loss': (['hair loss', 'hair fall', 'thinning hair', 'bald', 'losing hair'], 'hair_loss', 'Hair concerns',
                         'Hair health depends on nutrients like biotin, iron, and zinc. Strengthening these can promote healthier hair growth.'),

            # Cardiovascular
            'high_blood_pressure': (['blood pressure', 'hypertension', 'high bp'], 'high_blood_pressure', 'Blood pressure concerns',
                                   'Your blood vessels may benefit from potassium and magnesium, which help regulate blood pressure naturally.'),
            'cholesterol': (['cholesterol', 'ldl', 'hdl'], 'high_cholesterol', 'Cholesterol concerns',
                           'Soluble fiber and omega-3s can help improve your cholesterol profile naturally.'),

            # Weight and metabolism
            'weight_loss': (['weight', 'diet', 'lose weight', 'overweight', 'fat', 'slim'], 'weight_loss', 'Weight management',
                           'Proper nutrition can support healthy metabolism. Fiber and protein help you feel full longer.'),

            # Allergies
            'allergies': (['allergy', 'allergic', 'histamine', 'allergies', 'seasonal'], 'allergies', 'Allergy symptoms',
                         'Your body may be overproducing histamine. Quercetin and vitamin C act as natural antihistamines.'),
        }

        for key, (keywords, condition_type, condition_name, explanation) in condition_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return {
                        "condition_name": condition_name,
                        "condition_type": condition_type,
                        "explanation": explanation,
                        "severity": "mild"
                    }

        # Default fallback
        return {
            "condition_name": "General health concern",
            "condition_type": "general_inflammation",
            "explanation": "Based on your description, this appears to be a general health concern. Anti-inflammatory foods and a nutrient-rich diet can help support your body's natural healing process and overall wellness.",
            "severity": "mild"
        }

    def _generate_remedy_explanation(self, condition_name: str, nutrient_info: Dict) -> str:
        """Generate a clear explanation of why these nutrients help"""
        nutrients = ", ".join(nutrient_info['nutrients'][:4])
        foods = ", ".join(nutrient_info['foods'][:4])

        # Get specific explanations for the top nutrients
        explanations = nutrient_info.get('nutrient_explanations', {})
        specific_reasons = []
        for nutrient in nutrient_info['nutrients'][:3]:
            if nutrient in explanations:
                specific_reasons.append(f"**{nutrient}**: {explanations[nutrient][:150]}...")

        explanation = f"""## Why These Nutrients Help {condition_name}

Based on research from the FDA and NIH, these nutrients are particularly beneficial:

{chr(10).join(specific_reasons) if specific_reasons else f"Key nutrients ({nutrients}) work together to support your body's healing process."}

### Top Food Sources
The best natural sources include: **{foods}**.

### How to Use This Information
Try to incorporate these foods into your daily meals. Start with 1-2 servings of these foods per day and gradually increase. The recipes below are designed to maximize these healing nutrients.

*Data sourced from FDA FoodData Central and NIH Office of Dietary Supplements*"""

        return explanation

    def _cleanup_foods_with_ai(self, foods: List[Dict], condition_name: str) -> List[Dict]:
        """Use AI to clean up food names and generate helpful info for each food."""
        if not foods:
            return []

        # Pre-filter: remove prepared/recipe-like foods from FDA data
        whole_foods = self._filter_whole_foods(foods)
        if not whole_foods:
            whole_foods = foods[:8]  # Fallback if all filtered out

        food_descriptions = [food.get('description', '') for food in whole_foods]

        prompt = f"""Clean up these FDA food database names into simple WHOLE FOOD names.
These should be single ingredients you could buy at a grocery store, NOT recipes or prepared dishes.

CRITICAL RULES:
- Keep names as simple whole foods (e.g., "Apple", "Spinach", "Salmon", "Almonds")
- Do NOT create recipe names (NO "Apple Sauce", "Spinach Dip", "Fried Carrots")
- Do NOT add cooking methods (NO "Grilled", "Fried", "Baked", "Steamed" in the name)
- The name should be what you'd see on a produce/meat/dairy label

Also provide a brief tip about each food for someone with {condition_name}.
Also provide a simple image search term for each food.

Foods to process:
{chr(10).join([f'{i+1}. {desc}' for i, desc in enumerate(food_descriptions)])}

Return a JSON array with objects containing:
- "displayName": Simple whole food name (e.g., "Spinach", "Orange", "Salmon", "Almonds")
- "imageSearchTerm": A simple 1-2 word term for image search (e.g., "spinach", "orange", "salmon fillet")
- "tip": One short sentence about why this food helps or how to enjoy it (max 80 chars)

Example output format:
[
  {{"displayName": "Spinach", "imageSearchTerm": "fresh spinach", "tip": "Rich in iron - add to smoothies or salads"}},
  {{"displayName": "Salmon", "imageSearchTerm": "salmon fillet", "tip": "Omega-3 powerhouse for brain health"}},
  {{"displayName": "Oranges", "imageSearchTerm": "orange fruit", "tip": "High in vitamin C to support immunity"}}
]

Return ONLY the JSON array, no other text."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a nutrition assistant that helps clean up food names and provide helpful tips. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )

            result_text = response.choices[0].message.content.strip()
            if result_text.startswith('```'):
                result_text = result_text.strip('`').replace('json', '', 1).strip()

            cleaned_data = json.loads(result_text)

            result = []
            for i, food in enumerate(whole_foods):
                ai_data = cleaned_data[i] if i < len(cleaned_data) else {}
                display_name = ai_data.get('displayName', self._simple_name_cleanup(food.get('description', '')))
                image_search = ai_data.get('imageSearchTerm', self._extract_simple_food_term(display_name))

                # Skip if AI returned a recipe-like name
                if self._is_recipe_name(display_name):
                    display_name = self._simple_name_cleanup(food.get('description', ''))
                    image_search = self._extract_simple_food_term(display_name)

                result.append({
                    'name': food.get('description', ''),
                    'displayName': display_name,
                    'imageSearchTerm': image_search,
                    'tip': ai_data.get('tip', ''),
                    'fdcId': food.get('fdcId', ''),
                    'keyNutrients': food.get('nutrients', [])[:3],
                    'beneficialFor': food.get('beneficial_for', [])
                })
            return result

        except Exception as e:
            print(f"Error cleaning food names with AI: {str(e)}")
            result = []
            for food in whole_foods:
                display_name = self._simple_name_cleanup(food.get('description', ''))
                result.append({
                    'name': food.get('description', ''),
                    'displayName': display_name,
                    'imageSearchTerm': self._extract_simple_food_term(display_name),
                    'tip': '',
                    'fdcId': food.get('fdcId', ''),
                    'keyNutrients': food.get('nutrients', [])[:3],
                    'beneficialFor': food.get('beneficial_for', [])
                })
            return result

    def _filter_whole_foods(self, foods: List[Dict]) -> List[Dict]:
        """Filter out prepared/recipe-like foods, keeping only whole foods."""
        # Words that indicate a prepared dish rather than a whole food
        recipe_indicators = [
            'sauce', 'soup', 'stew', 'casserole', 'pie', 'cake', 'bread',
            'fried', 'baked', 'grilled', 'roasted', 'steamed', 'boiled',
            'mashed', 'creamed', 'stuffed', 'glazed', 'candied', 'pickled',
            'salad', 'sandwich', 'wrap', 'burger', 'pizza', 'pasta',
            'noodle', 'curry', 'stir-fry', 'stir fry', 'casserole',
            'pudding', 'custard', 'mousse', 'parfait', 'smoothie',
            'juice', 'cocktail', 'shake', 'prepared', 'cooked',
            'dish', 'meal', 'recipe', 'homemade', 'restaurant',
            'fast food', 'takeout', 'frozen dinner', 'tv dinner',
            'chips', 'crackers', 'cookies', 'candy', 'chocolate bar',
            'cereal', 'granola bar', 'protein bar', 'snack'
        ]

        whole_foods = []
        for food in foods:
            desc = food.get('description', '').lower()
            is_recipe = any(indicator in desc for indicator in recipe_indicators)
            if not is_recipe:
                whole_foods.append(food)

        return whole_foods

    def _is_recipe_name(self, name: str) -> bool:
        """Check if a name sounds like a recipe rather than a whole food."""
        if not name:
            return False

        name_lower = name.lower()

        # Recipe indicators
        recipe_words = [
            'sauce', 'soup', 'stew', 'salad', 'fried', 'baked', 'grilled',
            'roasted', 'steamed', 'mashed', 'creamed', 'stuffed', 'glazed',
            'candied', 'pickled', 'sandwich', 'wrap', 'burger', 'pizza',
            'pasta', 'curry', 'stir-fry', 'pudding', 'smoothie', 'juice',
            'shake', 'casserole', 'pie', 'cake', 'bread', 'snack', 'bar',
            'chips', 'crackers', 'cookies', 'with', 'and', 'style'
        ]

        return any(word in name_lower for word in recipe_words)

    def _simple_name_cleanup(self, name: str) -> str:
        """Simple fallback cleanup for food names without AI."""
        if not name:
            return "Food"

        cleanups = [
            ', raw', ', fresh', ', cooked', ', boiled', ', steamed',
            ', frozen', ', canned', ', dried', ', NFS', ', NS as to form',
            ', mature seeds', ', dry', ', whole', ', fat free'
        ]

        result = name
        for cleanup in cleanups:
            result = result.replace(cleanup, '')

        result = result.strip().title()

        return result

    def _extract_simple_food_term(self, display_name: str) -> str:
        """Extract a simple, searchable food term from a display name."""
        if not display_name:
            return "food"

        food_keywords = [
            'spinach', 'salmon', 'orange', 'lemon', 'lime', 'grapefruit', 'citrus',
            'berry', 'berries', 'strawberry', 'blueberry', 'raspberry', 'blackberry',
            'apple', 'banana', 'mango', 'papaya', 'pineapple', 'kiwi', 'grape',
            'avocado', 'broccoli', 'kale', 'carrot', 'tomato', 'pepper', 'onion',
            'garlic', 'ginger', 'turmeric', 'nuts', 'almonds', 'walnuts', 'seeds',
            'chicken', 'beef', 'fish', 'tuna', 'sardine', 'mackerel', 'egg',
            'yogurt', 'milk', 'cheese', 'oats', 'quinoa', 'rice', 'beans',
            'lentils', 'chickpeas', 'tofu', 'tempeh', 'sweet potato', 'potato',
            'mushroom', 'celery', 'cucumber', 'lettuce', 'cabbage', 'cauliflower',
            'asparagus', 'zucchini', 'squash', 'pumpkin', 'watermelon', 'melon',
            'peach', 'plum', 'apricot', 'cherry', 'fig', 'date', 'prune',
            'coconut', 'olive', 'flaxseed', 'chia', 'hemp', 'sunflower'
        ]

        name_lower = display_name.lower()

        for keyword in food_keywords:
            if keyword in name_lower:
                return keyword

        words = display_name.split()
        if len(words) >= 2:
            skip_words = ['fresh', 'wild', 'organic', 'raw', 'natural', 'pure', 'high', 'rich', 'vitamin']
            result_words = [w for w in words[:3] if w.lower() not in skip_words]
            if result_words:
                return ' '.join(result_words[:2]).lower()

        return words[0].lower() if words else "food"

    def _filter_foods_by_preferences(
        self,
        foods: List[Dict],
        allergies: List[str],
        diet_type: str
    ) -> List[Dict]:
        """Filter foods based on user allergies and diet type"""
        if not allergies and not diet_type:
            return foods

        allergen_keywords = {
            'peanuts': ['peanut', 'groundnut'],
            'tree nuts': ['almond', 'walnut', 'cashew', 'pecan', 'pistachio', 'hazelnut', 'macadamia', 'brazil nut'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'lactose', 'whey', 'casein'],
            'eggs': ['egg', 'albumin', 'mayonnaise'],
            'soy': ['soy', 'soya', 'tofu', 'tempeh', 'edamame', 'miso'],
            'gluten': ['wheat', 'barley', 'rye', 'bread', 'pasta', 'flour', 'cereal', 'oat'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'tilapia', 'halibut', 'sardine', 'anchovy'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'clam', 'mussel', 'oyster', 'scallop', 'crawfish'],
        }

        diet_restrictions = {
            'vegetarian': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage', 'fish', 'seafood', 'salmon', 'tuna'],
            'vegan': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage', 'fish', 'seafood', 'salmon', 'tuna', 'milk', 'cheese', 'yogurt', 'butter', 'cream', 'egg', 'honey', 'dairy'],
            'pescatarian': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'ham', 'sausage'],
            'keto': ['bread', 'pasta', 'rice', 'potato', 'sugar', 'corn', 'cereal', 'oat', 'wheat'],
            'paleo': ['bread', 'pasta', 'rice', 'cereal', 'oat', 'wheat', 'dairy', 'milk', 'cheese', 'legume', 'bean', 'peanut', 'soy'],
            'halal': ['pork', 'bacon', 'ham', 'lard', 'gelatin'],
            'kosher': ['pork', 'bacon', 'ham', 'shellfish', 'shrimp', 'crab', 'lobster'],
        }

        exclude_keywords = set()

        for allergy in allergies:
            allergy_lower = allergy.lower()
            if allergy_lower in allergen_keywords:
                exclude_keywords.update(allergen_keywords[allergy_lower])
            else:
                exclude_keywords.add(allergy_lower)

        if diet_type and diet_type in diet_restrictions:
            exclude_keywords.update(diet_restrictions[diet_type])

        filtered_foods = []
        for food in foods:
            food_name = food.get('description', '').lower()
            should_exclude = any(keyword in food_name for keyword in exclude_keywords)
            if not should_exclude:
                filtered_foods.append(food)

        return filtered_foods

    def _filter_recipes_by_preferences(
        self,
        recipes: List[Dict],
        allergies: List[str],
        diet_type: str
    ) -> List[Dict]:
        """Filter recipes based on user allergies and diet type"""
        if not allergies and not diet_type:
            return recipes[:5]

        allergen_keywords = {
            'peanuts': ['peanut', 'groundnut'],
            'tree nuts': ['almond', 'walnut', 'cashew', 'pecan', 'pistachio', 'hazelnut', 'macadamia'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'lactose', 'whey'],
            'eggs': ['egg', 'albumin', 'mayonnaise'],
            'soy': ['soy', 'soya', 'tofu', 'tempeh', 'edamame'],
            'gluten': ['wheat', 'barley', 'rye', 'bread', 'pasta', 'flour'],
            'fish': ['fish', 'salmon', 'tuna', 'cod', 'tilapia', 'halibut'],
            'shellfish': ['shrimp', 'crab', 'lobster', 'clam', 'mussel', 'oyster', 'scallop'],
        }

        diet_restrictions = {
            'vegetarian': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'fish', 'seafood'],
            'vegan': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon', 'fish', 'milk', 'cheese', 'yogurt', 'butter', 'egg', 'honey'],
            'pescatarian': ['beef', 'pork', 'chicken', 'turkey', 'lamb', 'meat', 'bacon'],
            'keto': ['bread', 'pasta', 'rice', 'potato', 'sugar', 'corn'],
            'paleo': ['bread', 'pasta', 'rice', 'dairy', 'milk', 'cheese', 'bean', 'peanut'],
            'halal': ['pork', 'bacon', 'ham', 'lard'],
            'kosher': ['pork', 'bacon', 'ham', 'shellfish', 'shrimp', 'crab'],
        }

        exclude_keywords = set()

        for allergy in allergies:
            allergy_lower = allergy.lower()
            if allergy_lower in allergen_keywords:
                exclude_keywords.update(allergen_keywords[allergy_lower])
            else:
                exclude_keywords.add(allergy_lower)

        if diet_type and diet_type in diet_restrictions:
            exclude_keywords.update(diet_restrictions[diet_type])

        filtered_recipes = []
        for recipe in recipes:
            recipe_text = recipe.get('title', '').lower()
            ingredients = recipe.get('ingredients', [])
            if isinstance(ingredients, list):
                recipe_text += ' ' + ' '.join(str(i).lower() for i in ingredients)

            should_exclude = any(keyword in recipe_text for keyword in exclude_keywords)
            if not should_exclude:
                filtered_recipes.append(recipe)

        return filtered_recipes[:5]

    def save_remedy(
        self,
        user_id: str,
        condition: str,
        condition_explanation: str,
        remedy: Dict,
        image_url: Optional[str] = None
    ) -> Dict:
        """Save a remedy to user's saved remedies"""
        remedy_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': f"{DATA_TYPE_SAVED_REMEDY}#{remedy_id}",
                    'remedyId': remedy_id,
                    'condition': condition,
                    'conditionExplanation': condition_explanation,
                    'remedy': remedy,
                    'imageUrl': image_url or '',
                    'savedAt': timestamp
                }
            )

            return {
                'remedyId': remedy_id,
                'message': 'Remedy saved successfully'
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save remedy: {str(e)}"
            )

    def get_saved_remedies(self, user_id: str) -> List[Dict]:
        """Get all saved remedies for a user"""
        try:
            response = self.table.query(
                KeyConditionExpression='userId = :userId AND begins_with(dataType, :dataType)',
                ExpressionAttributeValues={
                    ':userId': user_id,
                    ':dataType': DATA_TYPE_SAVED_REMEDY
                }
            )

            return response.get('Items', [])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve saved remedies: {str(e)}"
            )
