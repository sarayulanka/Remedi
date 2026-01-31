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

# DynamoDB BatchWriteItem supports max 25 items per batch
BATCH_SIZE = 25


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def delete_existing_preferences(email):
    """Query and delete all existing PREF# items for this user."""
    key_condition = Key('email').eq(email) & Key('record_type').begins_with('PREF#')

    # Collect all existing preference keys
    items_to_delete = []
    query_kwargs = {
        'KeyConditionExpression': key_condition,
        'ProjectionExpression': 'email, record_type'
    }

    while True:
        response = table.query(**query_kwargs)
        items_to_delete.extend(response.get('Items', []))

        last_key = response.get('LastEvaluatedKey')
        if not last_key:
            break
        query_kwargs['ExclusiveStartKey'] = last_key

    if not items_to_delete:
        return 0

    # Delete in batches of 25 (DynamoDB BatchWriteItem limit)
    deleted_count = 0
    for i in range(0, len(items_to_delete), BATCH_SIZE):
        batch = items_to_delete[i:i + BATCH_SIZE]
        delete_requests = [
            {
                'DeleteRequest': {
                    'Key': {
                        'email': item['email'],
                        'record_type': item['record_type']
                    }
                }
            }
            for item in batch
        ]

        # Use the underlying DynamoDB client for BatchWriteItem
        table_name = os.environ['USERS_TABLE']
        response = dynamodb.meta.client.batch_write_item(
            RequestItems={
                table_name: delete_requests
            }
        )

        # Handle unprocessed items with retry
        unprocessed = response.get('UnprocessedItems', {})
        retry_count = 0
        while unprocessed.get(table_name) and retry_count < 3:
            retry_count += 1
            response = dynamodb.meta.client.batch_write_item(
                RequestItems=unprocessed
            )
            unprocessed = response.get('UnprocessedItems', {})

        deleted_count += len(batch)

    return deleted_count


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
        if not isinstance(preferences, list):
            return respond(400, {'error': 'Body must contain a "preferences" array'})

        # Validate all preferences before making any changes
        for pref in preferences:
            pref_type = pref.get('type', '').upper()
            pref_value = pref.get('value', '').upper()

            if pref_type not in VALID_TYPES:
                return respond(400, {
                    'error': f'Invalid preference type: {pref_type}. Must be one of: {", ".join(sorted(VALID_TYPES))}'
                })

            if not pref_value:
                return respond(400, {'error': 'Each preference must have a "value" field'})

        # Step 1: Delete all existing preferences for this user
        deleted_count = delete_existing_preferences(email)

        # Step 2: Create new preference items
        now = datetime.now(timezone.utc).isoformat()
        created_items = []

        for pref in preferences:
            pref_type = pref.get('type', '').upper()
            pref_value = pref.get('value', '').upper()
            reference_value = pref.get('reference_value', '')

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

        return respond(200, {
            'message': f'Replaced preferences: {deleted_count} removed, {len(created_items)} created',
            'preferences': created_items
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
