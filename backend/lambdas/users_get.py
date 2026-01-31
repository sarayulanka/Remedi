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


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    try:
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Parse query string parameters
        query_params = event.get('queryStringParameters') or {}

        # Parse limit (default 20, max 100)
        try:
            limit = int(query_params.get('limit', '20'))
            limit = max(1, min(limit, 100))
        except (ValueError, TypeError):
            limit = 20

        # Build scan kwargs
        scan_kwargs = {
            'FilterExpression': Attr('record_type').eq('PROFILE'),
            'Limit': limit
        }

        # Handle pagination with last_evaluated_key
        last_evaluated_key = query_params.get('last_evaluated_key')
        if last_evaluated_key:
            try:
                decoded_key = json.loads(last_evaluated_key)
                scan_kwargs['ExclusiveStartKey'] = decoded_key
            except (json.JSONDecodeError, TypeError):
                return respond(400, {'error': 'Invalid last_evaluated_key format'})

        # Perform scan
        # Note: Scan with FilterExpression may return fewer items than Limit
        # because Limit applies before filtering. We accumulate results.
        users = []
        last_key = None

        while len(users) < limit:
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])

            for item in items:
                # Exclude password_hash from each user
                user = {k: v for k, v in item.items() if k != 'password_hash'}
                users.append(user)

            last_key = response.get('LastEvaluatedKey')

            if not last_key:
                # No more items to scan
                break

            # Update ExclusiveStartKey for next iteration
            scan_kwargs['ExclusiveStartKey'] = last_key

        # Trim to requested limit
        if len(users) > limit:
            users = users[:limit]
            # Since we trimmed, there are still more results
            # We don't have a perfect pagination key here, so we keep last_key
        elif not last_key:
            last_key = None

        result = {
            'users': users,
            'count': len(users)
        }

        if last_key:
            result['last_evaluated_key'] = json.dumps(last_key, default=str)

        return respond(200, result)

    except Exception as e:
        return respond(500, {'error': str(e)})
