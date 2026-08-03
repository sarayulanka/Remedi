import json
import os
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
    """GET /users/{userid}/rewards — Get rewards for a user."""
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

        # Parse optional query parameters
        query_params = event.get('queryStringParameters') or {}
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        limit = int(query_params.get('limit', 50))

        # Build query
        if start_date and end_date:
            # Date range query using sort key boundaries
            # Tilde (~) sorts after all UUID characters in ASCII
            response = table.query(
                KeyConditionExpression=Key('user_id').eq(user_id) & Key('date_reward_id').between(
                    f"{start_date}#",
                    f"{end_date}#~"
                ),
                ScanIndexForward=False,
                Limit=limit
            )
        elif start_date:
            # Only start_date: from start_date onwards
            response = table.query(
                KeyConditionExpression=Key('user_id').eq(user_id) & Key('date_reward_id').gte(
                    f"{start_date}#"
                ),
                ScanIndexForward=False,
                Limit=limit
            )
        elif end_date:
            # Only end_date: up to end_date
            response = table.query(
                KeyConditionExpression=Key('user_id').eq(user_id) & Key('date_reward_id').lte(
                    f"{end_date}#~"
                ),
                ScanIndexForward=False,
                Limit=limit
            )
        else:
            # No date filter: newest first
            response = table.query(
                KeyConditionExpression=Key('user_id').eq(user_id),
                ScanIndexForward=False,
                Limit=limit
            )

        rewards = response.get('Items', [])

        return respond(200, {
            'rewards': rewards,
            'count': len(rewards)
        })

    except ValueError:
        return respond(400, {'error': 'Invalid limit parameter, must be an integer'})
    except Exception as e:
        return respond(500, {'error': str(e)})
