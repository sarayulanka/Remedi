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
    """GET /users/{userid}/alerts — Get alerts for a user."""
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

        # Parse optional query parameters
        query_params = event.get('queryStringParameters') or {}
        condition = query_params.get('condition')
        date = query_params.get('date')
        limit = int(query_params.get('limit', 50))

        if condition:
            # Query GSI gsi-email-condition: PK=email, SK begins_with "{condition}#"
            response = table.query(
                IndexName='gsi-email-condition',
                KeyConditionExpression=Key('email').eq(email) & Key('condition_alert_date').begins_with(
                    f"{condition}#"
                ),
                ScanIndexForward=False,
                Limit=limit
            )
        elif date:
            # Query main table: PK=email, SK begins_with "{date}#"
            response = table.query(
                KeyConditionExpression=Key('email').eq(email) & Key('alert_date_id').begins_with(
                    f"{date}#"
                ),
                ScanIndexForward=False,
                Limit=limit
            )
        else:
            # No filter: query main table, newest first
            response = table.query(
                KeyConditionExpression=Key('email').eq(email),
                ScanIndexForward=False,
                Limit=limit
            )

        alerts = response.get('Items', [])

        return respond(200, {
            'alerts': alerts,
            'count': len(alerts)
        })

    except ValueError:
        return respond(400, {'error': 'Invalid limit parameter, must be an integer'})
    except Exception as e:
        return respond(500, {'error': str(e)})
