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
    """PUT /refvalue/{refvalueid} — Update a reference value."""
    try:
        table_name = os.environ.get('REFERENCE_VALUES_TABLE', 'remedi-reference-values')
        table = dynamodb.Table(table_name)

        # Extract refvalueid from path parameters
        path_params = event.get('pathParameters') or {}
        refvalueid = path_params.get('refvalueid')

        if not refvalueid:
            return respond(400, {'error': 'Missing refvalueid in path parameters'})

        # Parse refvalueid: format is "{reference_type}#{reference_id}"
        parts = refvalueid.split('#', 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return respond(400, {
                'error': 'Invalid refvalueid format. Expected format: reference_type#reference_id',
                'received': refvalueid
            })

        reference_type = parts[0]
        reference_id = parts[1]

        # Check if item exists
        existing = table.get_item(
            Key={
                'reference_type': reference_type,
                'reference_id': reference_id
            }
        )

        if 'Item' not in existing:
            return respond(404, {
                'error': 'Reference value not found',
                'reference_type': reference_type,
                'reference_id': reference_id
            })

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        # Build UpdateExpression dynamically
        update_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        # Updatable fields
        updatable_fields = {
            'reference_value': 'reference_value',
            'description': 'description',
            'is_active': 'is_active',
            'sort_order': 'sort_order',
            'metadata': 'metadata'
        }

        for field_key, attr_name in updatable_fields.items():
            if field_key in body:
                value = body[field_key]

                # Validate specific fields
                if field_key == 'sort_order' and value is not None:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        return respond(400, {'error': 'sort_order must be an integer'})

                if field_key == 'metadata' and value is not None and not isinstance(value, dict):
                    return respond(400, {'error': 'metadata must be a map/object'})

                if field_key == 'is_active' and not isinstance(value, bool):
                    return respond(400, {'error': 'is_active must be a boolean'})

                placeholder_name = f'#{field_key}'
                placeholder_value = f':{field_key}'
                expression_attribute_names[placeholder_name] = attr_name
                expression_attribute_values[placeholder_value] = value
                update_parts.append(f'{placeholder_name} = {placeholder_value}')

        if not update_parts:
            return respond(400, {'error': 'No updatable fields provided. Updatable fields: reference_value, description, is_active, sort_order, metadata'})

        # Always update updated_at
        update_parts.append('#updated_at = :updated_at')
        expression_attribute_names['#updated_at'] = 'updated_at'
        expression_attribute_values[':updated_at'] = datetime.now(timezone.utc).isoformat()

        update_expression = 'SET ' + ', '.join(update_parts)

        response = table.update_item(
            Key={
                'reference_type': reference_type,
                'reference_id': reference_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )

        updated_item = response.get('Attributes', {})

        return respond(200, {
            'message': 'Reference value updated successfully',
            'reference_value': updated_item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
