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

VALID_SEVERITIES = {'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    """PUT /users/{userid}/alerts/{alertid} — Update an alert."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        table_name = os.environ.get('ALERTS_TABLE', 'remedi-alerts')
        table = dynamodb.Table(table_name)

        # Extract path parameters
        path_params = event.get('pathParameters') or {}
        email = path_params.get('userid')
        alert_date_id = path_params.get('alertid')

        if not email:
            return respond(400, {'error': 'Missing userid in path parameters'})
        if not alert_date_id:
            return respond(400, {'error': 'Missing alertid in path parameters'})

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Missing request body'})

        if isinstance(body, str):
            body = json.loads(body)

        # Confirm the alert exists
        existing = table.get_item(
            Key={
                'email': email,
                'alert_date_id': alert_date_id
            }
        )

        if 'Item' not in existing:
            return respond(404, {
                'error': f"Alert not found for user '{email}' with id '{alert_date_id}'"
            })

        # Build UpdateExpression dynamically
        update_parts = []
        expression_attr_names = {}
        expression_attr_values = {}

        # Handle is_acknowledged
        if 'is_acknowledged' in body:
            is_acknowledged = body['is_acknowledged']
            if not isinstance(is_acknowledged, bool):
                return respond(400, {'error': 'is_acknowledged must be a boolean'})

            update_parts.append('#is_ack = :is_ack')
            expression_attr_names['#is_ack'] = 'is_acknowledged'
            expression_attr_values[':is_ack'] = is_acknowledged

            # If acknowledging, set acknowledged_at timestamp
            if is_acknowledged:
                now = datetime.now(timezone.utc).isoformat()
                update_parts.append('#ack_at = :ack_at')
                expression_attr_names['#ack_at'] = 'acknowledged_at'
                expression_attr_values[':ack_at'] = now

        # Handle severity
        if 'severity' in body:
            severity = body['severity'].upper()
            if severity not in VALID_SEVERITIES:
                return respond(400, {
                    'error': f"Invalid severity '{severity}'. Must be one of: {', '.join(sorted(VALID_SEVERITIES))}"
                })
            update_parts.append('#sev = :sev')
            expression_attr_names['#sev'] = 'severity'
            expression_attr_values[':sev'] = severity

        if not update_parts:
            return respond(400, {'error': 'No valid fields to update. Supported fields: is_acknowledged, severity'})

        update_expression = 'SET ' + ', '.join(update_parts)

        # Execute update
        response = table.update_item(
            Key={
                'email': email,
                'alert_date_id': alert_date_id
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attr_names,
            ExpressionAttributeValues=expression_attr_values,
            ReturnValues='ALL_NEW'
        )

        updated_item = response.get('Attributes', {})

        return respond(200, {
            'message': 'Alert updated successfully',
            'alert': updated_item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
