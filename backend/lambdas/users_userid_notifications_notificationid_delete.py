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
    """DELETE /users/{userid}/notifications/{notificationid} — Delete a notification."""
    try:
        table_name = os.environ.get('NOTIFICATIONS_TABLE', 'remedi-notifications')
        table = dynamodb.Table(table_name)

        # Extract path parameters
        path_params = event.get('pathParameters') or {}
        userid = path_params.get('userid')
        notificationid = path_params.get('notificationid')

        if not userid:
            return respond(400, {'error': 'Missing userid in path parameters'})
        if not notificationid:
            return respond(400, {'error': 'Missing notificationid in path parameters'})

        # DeleteItem: PK=email, SK=created_at (notificationid is the created_at timestamp)
        table.delete_item(
            Key={
                'email': userid,
                'created_at': notificationid
            }
        )

        return respond(200, {
            'message': 'Notification deleted successfully',
            'email': userid,
            'created_at': notificationid
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
