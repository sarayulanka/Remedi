import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ACTIVITY_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

TTL_DAYS = 365


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

        # Required fields
        api_endpoint = body.get('api_endpoint')
        http_method = body.get('http_method')

        if not api_endpoint:
            return respond(400, {'error': 'Missing required field: api_endpoint'})
        if not http_method:
            return respond(400, {'error': 'Missing required field: http_method'})

        # Optional fields
        response_status = body.get('response_status')
        session_id = body.get('session_id')
        request_metadata = body.get('request_metadata')

        # Generate timestamps
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        activity_date = now.strftime('%Y-%m-%d')
        ttl_expiry = int((now + timedelta(days=TTL_DAYS)).timestamp())

        # Build item
        item = {
            'email': email,
            'timestamp': timestamp,
            'activity_date': activity_date,
            'api_endpoint': api_endpoint,
            'http_method': http_method.upper(),
            'ttl_expiry': ttl_expiry
        }

        # Add optional fields only if provided
        if response_status is not None:
            item['response_status'] = response_status
        if session_id:
            item['session_id'] = session_id
        if request_metadata:
            item['request_metadata'] = request_metadata

        table.put_item(Item=item)

        return respond(201, {
            'message': 'Activity recorded successfully',
            'activity': item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
