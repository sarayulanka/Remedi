import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['ACTIVITY_TABLE'])

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
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Extract path parameters
        path_params = event.get('pathParameters') or {}
        email = path_params.get('userid')
        activity_id = path_params.get('activityid')

        if not email:
            return respond(400, {'error': 'Missing userid in path parameters'})
        if not activity_id:
            return respond(400, {'error': 'Missing activityid in path parameters'})

        # GetItem from DynamoDB
        response = table.get_item(
            Key={
                'email': email,
                'timestamp': activity_id
            }
        )

        item = response.get('Item')

        if not item:
            return respond(404, {
                'error': 'Activity not found',
                'email': email,
                'activityid': activity_id
            })

        return respond(200, {
            'activity': item
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
