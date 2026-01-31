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


def parse_preference_sk(sort_key):
    """Parse a sort key like PREF#REASON#WEIGHT_LOSS into type and value."""
    parts = sort_key.split('#')
    if len(parts) >= 3:
        return {
            'type': parts[1],
            'value': '#'.join(parts[2:])  # Handle values that might contain #
        }
    return {'type': '', 'value': ''}


def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        email = path_params.get('userid')
        if not email:
            return respond(400, {'error': 'Missing userid in path parameters'})

        # Check for optional type query parameter
        query_params = event.get('queryStringParameters') or {}
        pref_type = query_params.get('type', '').upper() if query_params.get('type') else None

        # Validate type if provided
        if pref_type and pref_type not in VALID_TYPES:
            return respond(400, {
                'error': f'Invalid preference type: {pref_type}. Must be one of: {", ".join(sorted(VALID_TYPES))}'
            })

        # Build the query
        if pref_type:
            sk_prefix = f"PREF#{pref_type}#"
        else:
            sk_prefix = "PREF#"

        key_condition = Key('email').eq(email) & Key('record_type').begins_with(sk_prefix)

        # Execute query with pagination support
        items = []
        query_kwargs = {
            'KeyConditionExpression': key_condition
        }

        while True:
            response = table.query(**query_kwargs)
            items.extend(response.get('Items', []))

            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
            query_kwargs['ExclusiveStartKey'] = last_key

        # Transform items into response format
        preferences = []
        for item in items:
            parsed = parse_preference_sk(item['record_type'])
            preferences.append({
                'type': parsed['type'],
                'value': parsed['value'],
                'reference_value': item.get('reference_value', ''),
                'created_at': item.get('created_at', ''),
                'updated_at': item.get('updated_at', '')
            })

        return respond(200, {
            'email': email,
            'count': len(preferences),
            'preferences': preferences
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
