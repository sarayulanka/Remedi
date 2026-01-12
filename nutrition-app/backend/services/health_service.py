import base64
import os
from typing import Dict, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from services.fda_service import FDAService
from fastapi import HTTPException
import uuid
from datetime import datetime
from database import get_table, DATA_TYPE_SAVED_REMEDY

load_dotenv()

class HealthAnalysisService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.fda_service = FDAService()
        self.table = get_table()
    
    def analyze_health_concern(
        self,
        user_id: str,
        image_base64: Optional[str] = None,
        text_description: Optional[str] = None,
        user_concerns: Optional[str] = None
    ) -> Dict:
        """Analyze a health concern using image and/or text"""
        
        if not image_base64 and not text_description:
            raise HTTPException(
                status_code=400,
                detail="Either image or text description is required"
            )
        
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
        
        # Step 4: Create comprehensive response
        response = {
            'condition': {
                'name': condition_analysis['condition_name'],
                'type': condition_analysis['condition_type'],
                'explanation': condition_analysis['explanation'],
                'severity': condition_analysis.get('severity', 'mild')
            },
            'remedy': {
                'recommendedNutrients': nutrient_info['nutrients'],
                'foodCategories': nutrient_info['foods'],
                'specificFoods': [
                    {
                        'name': food['description'],
                        'fdcId': food['fdcId'],
                        'keyNutrients': food['nutrients'][:3],  # Top 3 nutrients
                        'beneficialFor': food.get('beneficial_for', [])
                    }
                    for food in recommended_foods[:8]
                ],
                'explanation': self._generate_remedy_explanation(
                    condition_analysis['condition_name'],
                    nutrient_info
                )
            },
            'disclaimer': 'This information is for educational purposes only and is based on nutritional data from the FDA FoodData Central database. It is not a substitute for professional medical advice. Please consult a healthcare provider for proper diagnosis and treatment.'
        }
        
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
                "content": """You are a health analysis assistant. Analyze the provided image and/or description of a health concern.
                
Your task is to:
1. Identify what the condition appears to be in simple, non-medical terms
2. Provide a clear, easy-to-understand explanation of what's happening
3. Categorize the condition (e.g., skin_inflammation, boil, sore, rash, acne, dry_skin, wound_healing)
4. Assess severity (mild, moderate, concerning)

Respond in JSON format:
{
    "condition_name": "Simple name for the condition",
    "condition_type": "category_name",
    "explanation": "Clear explanation in simple terms that anyone can understand",
    "severity": "mild|moderate|concerning"
}

Be empathetic, clear, and avoid medical jargon. Focus on what the person can understand."""
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
                model="gpt-4o-mini",  # Using vision-capable model
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse the response
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error analyzing condition: {str(e)}")
            # Fallback response
            return {
                "condition_name": "Skin concern",
                "condition_type": "general_inflammation",
                "explanation": "Based on your description, this appears to be a common skin concern. Proper nutrition can help support your body's natural healing process.",
                "severity": "mild"
            }
    
    def _generate_remedy_explanation(self, condition_name: str, nutrient_info: Dict) -> str:
        """Generate a clear explanation of why these nutrients help"""
        nutrients = ", ".join(nutrient_info['nutrients'])
        foods = ", ".join(nutrient_info['foods'])
        
        explanation = f"""For {condition_name}, your body benefits from nutrients like {nutrients}. 
        
These nutrients help because they:
- Support your immune system and natural healing
- Reduce inflammation in the body
- Promote healthy skin and tissue repair
- Provide antioxidants that protect cells

Good food sources include: {foods}. 

Try to incorporate these foods into your daily meals. The foods listed below are from the FDA's nutritional database and are rich in the beneficial nutrients your body needs."""
        
        return explanation
    
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
        timestamp = datetime.utcnow().isoformat()
        
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
