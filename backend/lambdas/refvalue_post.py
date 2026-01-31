import json
import os
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
    """POST /refvalue — Create a reference value."""
    try:
        table_name = os.environ.get('REFERENCE_VALUES_TABLE', 'remedi-reference-values')
        table = dynamodb.Table(table_name)

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        # Validate required fields
        reference_type = body.get('reference_type')
        reference_id = body.get('reference_id')
        reference_value = body.get('reference_value')

        if not reference_type:
            return respond(400, {'error': 'reference_type is required'})
        if not reference_id:
            return respond(400, {'error': 'reference_id is required'})
        if not reference_value:
            return respond(400, {'error': 'reference_value is required'})

        # Check if item already exists
        existing = table.get_item(
            Key={
                'reference_type': reference_type,
                'reference_id': reference_id
            }
        )
        if 'Item' in existing:
            return respond(409, {
                'error': 'Reference value already exists',
                'reference_type': reference_type,
                'reference_id': reference_id
            })

        # Build item
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'reference_type': reference_type,
            'reference_id': reference_id,
            'reference_value': reference_value,
            'is_active': body.get('is_active', True),
            'created_at': now,
            'updated_at': now
        }

        # Optional fields
        description = body.get('description')
        if description is not None:
            item['description'] = description

        sort_order = body.get('sort_order')
        if sort_order is not None:
            try:
                item['sort_order'] = int(sort_order)
            except (ValueError, TypeError):
                return respond(400, {'error': 'sort_order must be an integer'})

        metadata = body.get('metadata')
        if metadata is not None:
            if not isinstance(metadata, dict):
                return respond(400, {'error': 'metadata must be a map/object'})
            item['metadata'] = metadata

        table.put_item(Item=item)

        return respond(201, {
            'message': 'Reference value created successfully',
            'reference_value': item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
