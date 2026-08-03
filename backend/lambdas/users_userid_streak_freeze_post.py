import json
import os
import boto3

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

        resp = table.get_item(Key={'user_id': user_id, 'record_type': 'STREAK'})
        if 'Item' not in resp:
            return respond(400, {'error': 'No streak data found'})

        streak = resp['Item']
        freezes = int(streak.get('streakFreezes', 0))
        if freezes <= 0:
            return respond(400, {'error': 'No streak freezes available'})

        return respond(200, {
            'success': True,
            'message': 'Freeze is available and will be auto-used if needed',
            'streakFreezes': freezes
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
