import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

VALID_TYPES = {'REASON', 'ALLERGY', 'DIET'}


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        email = path_params.get('userid')
        if not email:
            return respond(400, {'error': 'Missing userid in path parameters'})

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Missing request body'})

        if isinstance(body, str):
            body = json.loads(body)

        preferences = body.get('preferences')
        if not preferences or not isinstance(preferences, list):
            return respond(400, {'error': 'Body must contain a "preferences" array'})

        now = datetime.now(timezone.utc).isoformat()
        created_items = []

        for pref in preferences:
            pref_type = pref.get('type', '').upper()
            pref_value = pref.get('value', '').upper()
            reference_value = pref.get('reference_value', '')

            # Validate type
            if pref_type not in VALID_TYPES:
                return respond(400, {
                    'error': f'Invalid preference type: {pref_type}. Must be one of: {", ".join(sorted(VALID_TYPES))}'
                })

            if not pref_value:
                return respond(400, {'error': 'Each preference must have a "value" field'})

            sort_key = f"PREF#{pref_type}#{pref_value}"

            item = {
                'email': email,
                'record_type': sort_key,
                'reference_value': reference_value,
                'created_at': now,
                'updated_at': now
            }

            table.put_item(Item=item)

            created_items.append({
                'type': pref_type,
                'value': pref_value,
                'reference_value': reference_value,
                'created_at': now,
                'updated_at': now
            })

        return respond(201, {
            'message': f'Created {len(created_items)} preference(s)',
            'preferences': created_items
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
