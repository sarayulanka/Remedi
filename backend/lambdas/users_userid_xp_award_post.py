import json
import os
import boto3
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

XP_VALUES = {
    'daily_check_in': 10, 'complete_goal_day': 25, 'complete_goal_fully': 100,
    'health_analysis': 15, 'earn_badge': 50, 'streak_milestone': 100,
}
COMBO_MULTIPLIERS = {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0}


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _clean(item):
    cleaned = {}
    for k, v in item.items():
        if v is None:
            continue
        if isinstance(v, float):
            cleaned[k] = Decimal(str(v))
        elif isinstance(v, dict):
            cleaned[k] = _clean(v)
        elif isinstance(v, list):
            cleaned[k] = [_clean(x) if isinstance(x, dict) else Decimal(str(x)) if isinstance(x, float) else x for x in v if x is not None]
        else:
            cleaned[k] = v
    return cleaned


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

        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})
        if isinstance(body, str):
            body = json.loads(body)

        action = body.get('action', 'custom')
        base_amount = body.get('amount')
        if base_amount is None:
            base_amount = XP_VALUES.get(action, 10)
        else:
            base_amount = int(base_amount)

        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        resp = table.get_item(Key={'user_id': user_id, 'record_type': 'XP'})
        if 'Item' in resp:
            xp = resp['Item']
        else:
            xp = {'user_id': user_id, 'record_type': 'XP', 'totalXP': 0, 'currentLevel': 1,
                  'todayXP': 0, 'weeklyXP': 0, 'comboActions': 0, 'comboMultiplier': Decimal('1.0'),
                  'lastXPDate': None, 'xpHistory': []}

        if xp.get('lastXPDate') != today:
            xp['todayXP'] = 0
            xp['comboActions'] = 0
            xp['comboMultiplier'] = Decimal('1.0')

        xp['comboActions'] = int(xp.get('comboActions', 0)) + 1
        mult = COMBO_MULTIPLIERS.get(min(int(xp['comboActions']), 5), 2.0)
        final_xp = int(base_amount * mult)

        old_total = int(xp.get('totalXP', 0))
        new_total = old_total + final_xp
        xp['totalXP'] = new_total
        xp['todayXP'] = int(xp.get('todayXP', 0)) + final_xp
        xp['weeklyXP'] = int(xp.get('weeklyXP', 0)) + final_xp
        xp['lastXPDate'] = today
        xp['comboMultiplier'] = Decimal(str(mult))

        old_level = _level_from_xp(old_total)
        new_level = _level_from_xp(new_total)
        xp['currentLevel'] = new_level
        xp_cur = _xp_for_level(new_level)
        xp_next = _xp_for_level(new_level + 1)
        xp['xpProgress'] = new_total - xp_cur
        xp['xpToNextLevel'] = xp_next - xp_cur

        history = xp.get('xpHistory', [])
        if not isinstance(history, list):
            history = []
        entry = next((h for h in history if h.get('date') == today), None)
        if entry:
            entry['xp'] = int(entry.get('xp', 0)) + final_xp
        else:
            history.append({'date': today, 'xp': final_xp})
        xp['xpHistory'] = sorted(history, key=lambda x: x['date'], reverse=True)[:7]

        table.put_item(Item=_clean(xp))

        return respond(200, {
            'success': True, 'xpAwarded': final_xp, 'baseXP': base_amount,
            'multiplier': float(mult), 'totalXP': new_total,
            'currentLevel': new_level,
            'xpProgress': int(xp['xpProgress']),
            'xpToNextLevel': int(xp['xpToNextLevel']),
            'levelUp': new_level > old_level,
            'newLevel': new_level if new_level > old_level else None,
            'comboActions': int(xp['comboActions']),
            'comboMultiplier': float(mult)
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
