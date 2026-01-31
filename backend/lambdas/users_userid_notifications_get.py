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
    """GET /users/{userid}/notifications — List notifications for a user."""
    try:
        table_name = os.environ.get('NOTIFICATIONS_TABLE', 'remedi-notifications')
        table = dynamodb.Table(table_name)

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        userid = path_params.get('userid')
        if not userid:
            return respond(400, {'error': 'Missing userid in path parameters'})

        # Parse optional query parameters
        query_params = event.get('queryStringParameters') or {}
        unread_only = query_params.get('unread_only', 'false').lower() == 'true'

        try:
            limit = int(query_params.get('limit', '50'))
            if limit < 1:
                limit = 50
            if limit > 200:
                limit = 200
        except (ValueError, TypeError):
            limit = 50

        if unread_only:
            # Query GSI gsi-email-read-status for unread notifications
            response = table.query(
                IndexName='gsi-email-read-status',
                KeyConditionExpression=Key('email').eq(userid) & Key('read_status_created_at').begins_with('UNREAD#'),
                Limit=limit,
                ScanIndexForward=False
            )
        else:
            # Query primary key: PK=email, newest first
            response = table.query(
                KeyConditionExpression=Key('email').eq(userid),
                Limit=limit,
                ScanIndexForward=False
            )

        notifications = response.get('Items', [])

        return respond(200, {
            'notifications': notifications,
            'count': len(notifications)
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
