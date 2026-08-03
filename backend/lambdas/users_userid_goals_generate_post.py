import json
import os
import uuid
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import URLError

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ['USERS_TABLE'])
goals_table = dynamodb.Table(os.environ['GOALS_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

_secrets_cache = {}

def _get_secret(key):
    if not _secrets_cache:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId='remedi_api_keys')
        _secrets_cache.update(json.loads(resp['SecretString']))
    return _secrets_cache.get(key, '')


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _call_openai(messages, max_tokens=500, temperature=0.7):
    req = Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps({
            'model': 'gpt-4o-mini',
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature
        }).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {_get_secret("OPENAI_API_KEY")}'
        }
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _get_default_goals():
    return [
        {'title': 'Stay Hydrated', 'description': 'Drink at least 8 glasses of water throughout the day', 'targetDays': 7},
        {'title': 'Eat More Vegetables', 'description': 'Include at least 2 servings of vegetables in your meals', 'targetDays': 14},
        {'title': 'Mindful Eating', 'description': 'Eat one meal per day without screens, focusing on your food', 'targetDays': 21},
    ]


def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userid')
        if not user_id:
            return respond(400, {'error': 'userid is required'})

        # Get existing goals
        goals_resp = goals_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        existing_goals = goals_resp.get('Items', [])
        active_goals = [g for g in existing_goals if g.get('status') == 'ACTIVE']
        completed_goals = [g for g in existing_goals if g.get('status') == 'COMPLETED']

        if active_goals:
            return respond(200, {
                'generated': False,
                'message': 'You still have active goals to complete!',
                'activeGoals': len(active_goals),
                'completedGoals': len(completed_goals)
            })

        # Get user profile for personalization
        profile_resp = users_table.get_item(Key={'user_id': user_id, 'record_type': 'PROFILE'})
        profile = profile_resp.get('Item', {})

        nutrition_goals = profile.get('nutrition_goals', [])
        food_allergies = profile.get('food_allergies', [])
        diet_type = profile.get('diet_type', '')
        completed_titles = [g.get('title', '') for g in completed_goals[-10:]]

        # Generate AI goals
        prompt = f"""Generate 3 personalized nutrition goals for a user with the following profile:

Nutrition Goals: {', '.join(nutrition_goals) if nutrition_goals else 'General wellness'}
Allergies/Restrictions: {', '.join(food_allergies) if food_allergies else 'None'}
Diet Type: {diet_type if diet_type else 'No specific diet'}

Previously completed goals: {', '.join(completed_titles) if completed_titles else 'None yet'}

Generate 3 NEW goals that:
1. Are specific and actionable
2. Have clear daily actions
3. Range from easy (3-5 days) to moderate (7-14 days) to challenging (21-30 days)
4. Are appropriate for their dietary restrictions
5. Focus on nutrition, hydration, or healthy eating habits

Return ONLY a JSON array with exactly 3 goals:
[
  {{"title": "Short title (max 40 chars)", "description": "What to do daily", "targetDays": 5}},
  {{"title": "Medium goal", "description": "Description", "targetDays": 10}},
  {{"title": "Challenging goal", "description": "Description", "targetDays": 21}}
]

Return ONLY the JSON array, no other text."""

        try:
            ai_resp = _call_openai([
                {'role': 'system', 'content': 'You are a nutrition coach. Always return valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ])
            content = ai_resp['choices'][0]['message']['content'].strip()
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            goals = json.loads(content)
        except Exception:
            goals = _get_default_goals()

        # Validate and create goals
        created_goals = []
        now = datetime.now(timezone.utc)
        for goal in goals[:3]:
            goal_id = f"g-{uuid.uuid4()}"
            title = str(goal.get('title', 'Nutrition Goal'))[:50]
            description = str(goal.get('description', ''))[:200]
            target_days = min(max(int(goal.get('targetDays', 7)), 3), 30)

            item = {
                'user_id': user_id,
                'goal_id': goal_id,
                'title': title,
                'description': description,
                'target_days': target_days,
                'completed_days': 0,
                'status': 'ACTIVE',
                'status_created_at': f"ACTIVE#{now.isoformat()}",
                'start_date': now.strftime('%Y-%m-%d'),
                'end_date': (now + timedelta(days=target_days)).strftime('%Y-%m-%d'),
                'created_at': now.isoformat(),
                'updated_at': now.isoformat(),
                'last_progress_date': None
            }
            goals_table.put_item(Item=item)
            created_goals.append({
                'goalId': goal_id, 'title': title,
                'description': description, 'targetDays': target_days
            })

        return respond(200, {
            'generated': True,
            'message': f'Generated {len(created_goals)} new personalized goals!',
            'newGoals': created_goals,
            'completedGoals': len(completed_goals)
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
