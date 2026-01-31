import json
import os
import uuid
import time
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

VALID_SEVERITIES = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}
TTL_DAYS = 180


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    """POST /users/{userid}/alerts — Create an alert for a user."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        table_name = os.environ.get('ALERTS_TABLE', 'remedi-alerts')
        table = dynamodb.Table(table_name)

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

        # Validate required fields
        condition = body.get('condition')
        severity = body.get('severity')
        title = body.get('title')
        message = body.get('message')

        missing_fields = []
        if not condition:
            missing_fields.append('condition')
        if not severity:
            missing_fields.append('severity')
        if not title:
            missing_fields.append('title')
        if not message:
            missing_fields.append('message')

        if missing_fields:
            return respond(400, {
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            })

        # Validate severity
        severity = severity.upper()
        if severity not in VALID_SEVERITIES:
            return respond(400, {
                'error': f"Invalid severity '{severity}'. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}"
            })

        # Generate identifiers
        alert_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc)
        alert_date = now.strftime('%Y-%m-%d')
        alert_date_id = f"{alert_date}#{alert_id}"
        condition_alert_date = f"{condition}#{alert_date}#{alert_id}"
        created_at = now.isoformat()

        # TTL: 180 days from now as Unix epoch integer
        ttl_expiry = int(time.time()) + (TTL_DAYS * 24 * 60 * 60)

        # Build item
        item = {
            'email': email,
            'alert_date_id': alert_date_id,
            'alert_id': alert_id,
            'condition': condition,
            'condition_alert_date': condition_alert_date,
            'severity': severity,
            'title': title,
            'message': message,
            'is_acknowledged': False,
            'created_at': created_at,
            'ttl_expiry': ttl_expiry
        }

        # Write to DynamoDB
        table.put_item(Item=item)

        return respond(201, {
            'message': 'Alert created successfully',
            'alert': item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
