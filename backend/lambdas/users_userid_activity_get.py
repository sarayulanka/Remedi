import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ACTIVITY_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

DEFAULT_LIMIT = 50
MAX_LIMIT = 500


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

        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')

        # Parse and validate limit
        try:
            limit = int(query_params.get('limit', DEFAULT_LIMIT))
            if limit < 1:
                limit = DEFAULT_LIMIT
            elif limit > MAX_LIMIT:
                limit = MAX_LIMIT
        except (ValueError, TypeError):
            limit = DEFAULT_LIMIT

        # Build the query
        query_kwargs = {
            'Limit': limit
        }

        if start_date and end_date:
            # Validate date formats
            try:
                # Ensure dates parse correctly; append time boundaries if only dates given
                if len(start_date) == 10:  # YYYY-MM-DD format
                    start_date = f"{start_date}T00:00:00+00:00"
                if len(end_date) == 10:  # YYYY-MM-DD format
                    end_date = f"{end_date}T23:59:59.999999+00:00"
            except (ValueError, IndexError):
                return respond(400, {'error': 'Invalid date format. Use ISO 8601 or YYYY-MM-DD'})

            query_kwargs['KeyConditionExpression'] = (
                Key('email').eq(email) &
                Key('timestamp').between(start_date, end_date)
            )
            # When filtering by date range, return in chronological order
            query_kwargs['ScanIndexForward'] = True
        elif start_date:
            # Only start_date provided: everything from start_date onwards
            if len(start_date) == 10:
                start_date = f"{start_date}T00:00:00+00:00"

            query_kwargs['KeyConditionExpression'] = (
                Key('email').eq(email) &
                Key('timestamp').gte(start_date)
            )
            query_kwargs['ScanIndexForward'] = True
        elif end_date:
            # Only end_date provided: everything up to end_date
            if len(end_date) == 10:
                end_date = f"{end_date}T23:59:59.999999+00:00"

            query_kwargs['KeyConditionExpression'] = (
                Key('email').eq(email) &
                Key('timestamp').lte(end_date)
            )
            query_kwargs['ScanIndexForward'] = False
        else:
            # No date filters: return newest first
            query_kwargs['KeyConditionExpression'] = Key('email').eq(email)
            query_kwargs['ScanIndexForward'] = False

        # Execute query
        response = table.query(**query_kwargs)
        items = response.get('Items', [])

        result = {
            'email': email,
            'count': len(items),
            'activities': items
        }

        # Include pagination token if more results exist
        if response.get('LastEvaluatedKey'):
            result['next_key'] = response['LastEvaluatedKey']

        return respond(200, result)

    except Exception as e:
        return respond(500, {'error': str(e)})
