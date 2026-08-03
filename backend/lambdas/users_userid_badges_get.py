import json
import os
import boto3
from boto3.dynamodb.conditions import Key

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
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userid')
        if not user_id:
            return respond(400, {'error': 'userid is required'})

        resp = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id) & Key('record_type').begins_with('BADGE#')
        )

        badges = []
        for item in resp.get('Items', []):
            badges.append({
                'badgeId': item.get('badgeId', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'icon': item.get('icon', ''),
                'earnedAt': item.get('earnedAt', ''),
            })

        return respond(200, badges)

    except Exception as e:
        return respond(500, {'error': str(e)})
