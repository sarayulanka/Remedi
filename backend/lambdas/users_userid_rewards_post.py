import json
import os
import uuid
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    """POST /users/{userid}/rewards — Award a reward to a user."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        table_name = os.environ.get('REWARDS_TABLE', 'remedi-rewards')
        table = dynamodb.Table(table_name)

        # Extract user_id from path parameters
        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userid')
        if not user_id:
            return respond(400, {'error': 'Missing userid in path parameters'})

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Missing request body'})

        if isinstance(body, str):
            body = json.loads(body)

        # Determine type: badge reward or saved remedy
        badge_id = body.get('badge_id')
        condition = body.get('condition')

        if not badge_id and not condition:
            return respond(400, {'error': 'Either badge_id or condition is required'})

        # Generate identifiers
        reward_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        date_earned = now.strftime('%Y-%m-%d')
        date_reward_id = f"{date_earned}#{reward_id}"
        created_at = now.isoformat()

        # Build item
        item = {
            'user_id': user_id,
            'date_reward_id': date_reward_id,
            'reward_id': reward_id,
            'date_earned': date_earned,
            'created_at': created_at
        }

        if badge_id:
            item['reward_type'] = 'badge'
            item['badge_id'] = badge_id
            if body.get('goal_id'):
                item['goal_id'] = body['goal_id']
            if body.get('notes'):
                item['notes'] = body['notes']
        else:
            item['reward_type'] = 'remedy'
            item['condition'] = condition
            if body.get('conditionExplanation'):
                item['condition_explanation'] = body['conditionExplanation']
            if body.get('remedy'):
                item['remedy'] = body['remedy']
            if body.get('imageUrl'):
                item['image_url'] = body['imageUrl']

        # Write to DynamoDB
        table.put_item(Item=item)

        return respond(201, {
            'message': 'Reward created successfully',
            'reward': item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
