import json

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

AVAILABLE_BADGES = [
    {'badgeId': 'first_day', 'name': 'First Step', 'description': 'Started your nutrition journey', 'icon': '🌱', 'requirement': 1},
    {'badgeId': 'week_warrior', 'name': 'Week Warrior', 'description': 'Maintained a 7-day streak', 'icon': '⭐', 'requirement': 7},
    {'badgeId': 'ten_day_champion', 'name': '10-Day Champion', 'description': 'Achieved a 10-day streak', 'icon': '🏆', 'requirement': 10},
    {'badgeId': 'month_master', 'name': 'Month Master', 'description': 'Maintained a 30-day streak', 'icon': '👑', 'requirement': 30},
    {'badgeId': 'fifty_day_legend', 'name': '50-Day Legend', 'description': 'Achieved an incredible 50-day streak', 'icon': '💎', 'requirement': 50},
    {'badgeId': 'century_club', 'name': 'Century Club', 'description': 'Reached 100 days of consistent nutrition', 'icon': '🌟', 'requirement': 100},
    {'badgeId': 'health_explorer', 'name': 'Health Explorer', 'description': 'Analyzed your first health concern', 'icon': '🔍', 'requirement': 'first_analysis'},
    {'badgeId': 'goal_setter', 'name': 'Goal Setter', 'description': 'Created your first nutrition goal', 'icon': '🎯', 'requirement': 'first_goal'},
    {'badgeId': 'goal_achiever', 'name': 'Goal Achiever', 'description': 'Completed your first goal', 'icon': '✅', 'requirement': 'first_goal_complete'},
]


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return respond(200, {'message': 'OK'})
    return respond(200, AVAILABLE_BADGES)
