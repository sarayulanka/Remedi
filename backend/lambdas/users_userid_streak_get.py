import json
import os
import boto3
from datetime import datetime, timezone, timedelta
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
        if 'Item' not in resp:
            return respond(200, {
                'currentStreak': 0, 'longestStreak': 0, 'lastCheckIn': None,
                'totalCheckIns': 0, 'streakActive': False, 'checkedInToday': False,
                'streakAtRisk': False, 'streakFreezes': 0, 'hasFreezeProtection': False,
                'weeklyCheckIns': 0, 'achievedMilestones': [],
                'nextMilestone': {'days': 3, 'name': 'Getting Started', 'xp': 25},
                'daysToNextMilestone': 3, 'daysUntilFreeze': 7
            })

        streak = resp['Item']
        current_streak = int(streak.get('currentStreak', 0))
        longest_streak = int(streak.get('longestStreak', 0))
        total_check_ins = int(streak.get('totalCheckIns', 0))
        streak_freezes = int(streak.get('streakFreezes', 0))
        weekly_check_ins = int(streak.get('weeklyCheckIns', 0))
        last_ci_str = streak.get('lastCheckIn')
        milestones = streak.get('streakMilestones', [])

        streak_active = False
        checked_in_today = False
        streak_at_risk = False
        has_freeze = streak_freezes > 0

        if last_ci_str:
            try:
                if '+' in str(last_ci_str) or 'Z' in str(last_ci_str):
                    last_ci = datetime.fromisoformat(str(last_ci_str).replace('Z', '+00:00'))
                else:
                    last_ci = datetime.fromisoformat(str(last_ci_str)).replace(tzinfo=timezone.utc)
                days_diff = (datetime.now(timezone.utc).date() - last_ci.date()).days
                if days_diff == 0:
                    streak_active = True
                    checked_in_today = True
                elif days_diff == 1:
                    streak_active = True
                    streak_at_risk = True
                elif days_diff == 2 and has_freeze:
                    streak_active = True
                    streak_at_risk = True
                else:
                    current_streak = 0
            except Exception:
                current_streak = 0

        next_milestone = None
        days_to_next = None
        for m in STREAK_MILESTONES:
            if current_streak < m:
                next_milestone = {'days': m, 'name': MILESTONE_INFO[m]['name'], 'xp': MILESTONE_INFO[m]['xp']}
                days_to_next = m - current_streak
                break

        days_until_freeze = 7 - (current_streak % 7) if current_streak % 7 != 0 else 7

        return respond(200, {
            'currentStreak': current_streak,
            'longestStreak': longest_streak,
            'lastCheckIn': last_ci_str,
            'totalCheckIns': total_check_ins,
            'streakActive': streak_active,
            'checkedInToday': checked_in_today,
            'streakAtRisk': streak_at_risk,
            'streakFreezes': streak_freezes,
            'hasFreezeProtection': has_freeze,
            'weeklyCheckIns': weekly_check_ins,
            'achievedMilestones': [int(m) for m in milestones] if milestones else [],
            'nextMilestone': next_milestone,
            'daysToNextMilestone': days_to_next,
            'daysUntilFreeze': days_until_freeze
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
