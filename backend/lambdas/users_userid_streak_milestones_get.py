import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

STREAK_MILESTONES = [3, 7, 14, 30, 50, 100, 365]
MILESTONE_INFO = {
    3: {'name': 'Getting Started', 'xp': 25},
    7: {'name': 'Week Warrior', 'xp': 50},
    14: {'name': 'Two Weeks Strong', 'xp': 100},
    30: {'name': 'Month Master', 'xp': 200},
    50: {'name': '50-Day Legend', 'xp': 300},
    100: {'name': 'Century Club', 'xp': 500},
    365: {'name': 'Year of Wellness', 'xp': 1000}
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
        streak = resp.get('Item', {})
        current_streak = int(streak.get('currentStreak', 0))
        achieved = streak.get('streakMilestones', [])

        milestones = []
        for days in STREAK_MILESTONES:
            info = MILESTONE_INFO[days]
            is_achieved = days in [int(m) for m in achieved]
            progress = min(100, round((current_streak / days) * 100, 1))
            milestones.append({
                'days': days,
                'name': info['name'],
                'xp': info['xp'],
                'achieved': is_achieved,
                'progress': 100.0 if is_achieved else float(progress),
                'daysRemaining': max(0, days - current_streak)
            })

        return respond(200, {
            'currentStreak': current_streak,
            'milestones': milestones
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
