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
    """DELETE /users/{userid}/alerts/{alertid} — Delete an alert."""
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

        # Delete the item from DynamoDB
        # Use ConditionExpression to ensure the item exists before deleting
        table.delete_item(
            Key={
                'email': email,
                'alert_date_id': alert_date_id
            },
            ConditionExpression=Attr('email').exists()
        )

        return respond(200, {
            'message': f"Alert '{alert_date_id}' deleted successfully for user '{email}'"
        })

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        return respond(404, {
            'error': f"Alert not found for user '{email}' with id '{alert_date_id}'"
        })
    except Exception as e:
        return respond(500, {'error': str(e)})
