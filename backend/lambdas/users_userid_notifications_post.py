import json
import os
import uuid
import time
import boto3
from datetime import datetime, timezone

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
    """POST /users/{userid}/notifications — Create a notification for a user."""
    try:
        table_name = os.environ.get('NOTIFICATIONS_TABLE', 'remedi-notifications')
        table = dynamodb.Table(table_name)

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        userid = path_params.get('userid')
        if not userid:
            return respond(400, {'error': 'Missing userid in path parameters'})

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        # Validate required fields
        notification_type = body.get('type')
        title = body.get('title')
        message_text = body.get('message_text')

        if not notification_type:
            return respond(400, {'error': 'type is required'})
        if not title:
            return respond(400, {'error': 'title is required'})
        if not message_text:
            return respond(400, {'error': 'message_text is required'})

        # Build notification item
        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        notification_id = str(uuid.uuid4())
        is_read = False
        read_status_created_at = f"UNREAD#{created_at}"

        # TTL: 90 days from now (unix epoch seconds)
        ttl_expiry = int(time.time()) + (90 * 24 * 60 * 60)

        item = {
            'email': userid,
            'created_at': created_at,
            'notification_id': notification_id,
            'type': notification_type,
            'title': title,
            'message_text': message_text,
            'is_read': is_read,
            'read_status_created_at': read_status_created_at,
            'ttl_expiry': ttl_expiry
        }

        # Optional field
        related_entity_id = body.get('related_entity_id')
        if related_entity_id:
            item['related_entity_id'] = related_entity_id

        table.put_item(Item=item)

        return respond(201, {
            'message': 'Notification created successfully',
            'notification': item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
