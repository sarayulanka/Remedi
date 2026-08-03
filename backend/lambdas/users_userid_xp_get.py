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

COMBO_MULTIPLIERS = {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0}


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _xp_for_level(level):
    if level <= 1: return 0
    if level <= 10: return (level - 1) * 100
    if level <= 25: return 900 + (level - 10) * 200
    if level <= 50: return 3900 + (level - 25) * 350
    return 12650 + (level - 50) * 500


def _level_from_xp(total_xp):
    level = 1
    while _xp_for_level(level + 1) <= total_xp:
        level += 1
    return level


def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userid')
        if not user_id:
            return respond(400, {'error': 'userid is required'})

        resp = table.get_item(Key={'user_id': user_id, 'record_type': 'XP'})
        today = datetime.now(timezone.utc).date().isoformat()

        if 'Item' not in resp:
            return respond(200, {
                'totalXP': 0, 'currentLevel': 1, 'xpProgress': 0,
                'xpToNextLevel': 100, 'progressPercent': 0.0,
                'weeklyXP': 0, 'todayXP': 0,
                'comboMultiplier': 1.0, 'comboActions': 0,
                'nextComboMultiplier': 1.0
            })

        xp = resp['Item']
        if xp.get('lastXPDate') != today:
            xp['todayXP'] = 0
            xp['comboActions'] = 0
            xp['comboMultiplier'] = 1.0

        total_xp = int(xp.get('totalXP', 0))
        level = _level_from_xp(total_xp)
        xp_cur = _xp_for_level(level)
        xp_next = _xp_for_level(level + 1)
        progress = total_xp - xp_cur
        to_next = xp_next - xp_cur
        combo_actions = int(xp.get('comboActions', 0))

        return respond(200, {
            'totalXP': total_xp,
            'currentLevel': level,
            'xpProgress': progress,
            'xpToNextLevel': to_next,
            'progressPercent': round((progress / max(to_next, 1)) * 100, 1),
            'weeklyXP': int(xp.get('weeklyXP', 0)),
            'todayXP': int(xp.get('todayXP', 0)),
            'comboMultiplier': float(xp.get('comboMultiplier', 1.0)),
            'comboActions': combo_actions,
            'nextComboMultiplier': float(COMBO_MULTIPLIERS.get(min(combo_actions + 1, 5), 2.0))
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
