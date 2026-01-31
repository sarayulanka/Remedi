import json
import os
import boto3
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

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
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        userid = path_params.get('userid')

        if not userid:
            return respond(400, {'error': 'userid path parameter is required'})

        email = userid.strip().lower()

        # Get the user profile
        response = table.get_item(
            Key={
                'email': email,
                'record_type': 'PROFILE'
            }
        )

        item = response.get('Item')
        if not item:
            return respond(404, {'error': f"User not found: {email}"})

        # Exclude password_hash from response
        user = {k: v for k, v in item.items() if k != 'password_hash'}

        return respond(200, {'user': user})

    except Exception as e:
        return respond(500, {'error': str(e)})
