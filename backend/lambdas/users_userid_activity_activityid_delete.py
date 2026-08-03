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
        user_id = path_params.get('userid')
        activity_id = path_params.get('activityid')

        if not user_id:
            return respond(400, {'error': 'Missing userid in path parameters'})
        if not activity_id:
            return respond(400, {'error': 'Missing activityid in path parameters'})

        # First check if the item exists
        get_response = table.get_item(
            Key={
                'user_id': user_id,
                'timestamp': activity_id
            }
        )

        if not get_response.get('Item'):
            return respond(404, {
                'error': 'Activity not found',
                'user_id': user_id,
                'activityid': activity_id
            })

        # Delete the item
        table.delete_item(
            Key={
                'user_id': user_id,
                'timestamp': activity_id
            }
        )

        return respond(200, {
            'message': 'Activity deleted successfully',
            'user_id': user_id,
            'activityid': activity_id
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
