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

        resp = table.get_item(Key={'user_id': user_id, 'record_type': 'XP'})

        if 'Item' not in resp:
            return respond(200, {
                'history': [], 'totalLast7Days': 0,
                'averageDaily': 0.0, 'totalXP': 0, 'currentLevel': 1
            })

        xp = resp['Item']
        history = xp.get('xpHistory', [])
        if not isinstance(history, list):
            history = []

        history = sorted(history, key=lambda x: x.get('date', ''), reverse=True)
        clean_history = [{'date': h.get('date', ''), 'xp': int(h.get('xp', 0))} for h in history]
        total_7 = sum(h['xp'] for h in clean_history[:7])
        avg = round(total_7 / max(len(clean_history[:7]), 1), 1)

        return respond(200, {
            'history': clean_history,
            'totalLast7Days': total_7,
            'averageDaily': avg,
            'totalXP': int(xp.get('totalXP', 0)),
            'currentLevel': int(xp.get('currentLevel', 1))
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
