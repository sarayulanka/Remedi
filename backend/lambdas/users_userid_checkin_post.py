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

BADGE_DEFINITIONS = {
    'first_day': {'name': 'First Step', 'description': 'Started your nutrition journey', 'icon': '🌱', 'requirement': 1},
    'week_warrior': {'name': 'Week Warrior', 'description': 'Maintained a 7-day streak', 'icon': '⭐', 'requirement': 7},
    'ten_day_champion': {'name': '10-Day Champion', 'description': 'Achieved a 10-day streak', 'icon': '🏆', 'requirement': 10},
    'month_master': {'name': 'Month Master', 'description': 'Maintained a 30-day streak', 'icon': '👑', 'requirement': 30},
    'fifty_day_legend': {'name': '50-Day Legend', 'description': 'Achieved an incredible 50-day streak', 'icon': '💎', 'requirement': 50},
    'century_club': {'name': 'Century Club', 'description': 'Reached 100 days of consistent nutrition', 'icon': '🌟', 'requirement': 100},
}

XP_VALUES = {'daily_check_in': 10, 'streak_milestone': 100}
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


def _ensure_streak(user_id):
    resp = table.get_item(Key={'user_id': user_id, 'record_type': 'STREAK'})
    if 'Item' in resp:
        item = resp['Item']
        defaults = {'totalCheckIns': 0, 'streakFreezes': 0, 'freezesUsed': 0,
                    'lastFreezeEarned': None, 'streakMilestones': [],
                    'weeklyCheckIns': 0, 'weekStartDate': None}
        for k, d in defaults.items():
            if k not in item:
                item[k] = d
        return item
    data = {
        'user_id': user_id, 'record_type': 'STREAK',
        'currentStreak': 0, 'longestStreak': 0, 'lastCheckIn': None,
        'totalCheckIns': 0, 'streakFreezes': 0, 'freezesUsed': 0,
        'lastFreezeEarned': None, 'streakMilestones': [],
        'weeklyCheckIns': 0, 'weekStartDate': None
    }
    table.put_item(Item=_clean(data))
    return data


def _get_week_start(date):
    monday = date - timedelta(days=date.weekday())
    return monday.isoformat()


def _award_xp(user_id, action, base_amount=None):
    if base_amount is None:
        base_amount = XP_VALUES.get(action, 10)
    resp = table.get_item(Key={'user_id': user_id, 'record_type': 'XP'})
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
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
    xp_for_cur = _xp_for_level(new_level)
    xp_for_next = _xp_for_level(new_level + 1)
    xp['xpProgress'] = new_total - xp_for_cur
    xp['xpToNextLevel'] = xp_for_next - xp_for_cur
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
    return {'xpAwarded': final_xp, 'totalXP': new_total, 'levelUp': new_level > old_level,
            'newLevel': new_level if new_level > old_level else None}


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


def _check_streak_badges(user_id, current_streak):
    new_badges = []
    for badge_id, info in BADGE_DEFINITIONS.items():
        req = info['requirement']
        if isinstance(req, int) and current_streak >= req:
            resp = table.get_item(Key={'user_id': user_id, 'record_type': f'BADGE#{badge_id}'})
            if 'Item' not in resp:
                table.put_item(Item=_clean({
                    'user_id': user_id, 'record_type': f'BADGE#{badge_id}',
                    'badgeId': badge_id, 'name': info['name'],
                    'description': info['description'], 'icon': info['icon'],
                    'earnedAt': datetime.now(timezone.utc).isoformat()
                }))
                new_badges.append({'badgeId': badge_id, **info})
    return new_badges


def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userid')
        if not user_id:
            return respond(400, {'error': 'userid is required'})

        streak = _ensure_streak(user_id)
        now = datetime.now(timezone.utc)
        today = now.date()

        last_ci_str = streak.get('lastCheckIn')
        freeze_used = False
        milestone_reached = None
        freeze_earned = False

        current_week_start = _get_week_start(today)
        if streak.get('weekStartDate') != current_week_start:
            streak['weeklyCheckIns'] = 0
            streak['weekStartDate'] = current_week_start

        if last_ci_str:
            try:
                if '+' in str(last_ci_str) or 'Z' in str(last_ci_str):
                    last_ci = datetime.fromisoformat(str(last_ci_str).replace('Z', '+00:00'))
                else:
                    last_ci = datetime.fromisoformat(str(last_ci_str)).replace(tzinfo=timezone.utc)
                days_diff = (today - last_ci.date()).days

                if days_diff == 0:
                    return respond(200, {
                        'success': True, 'message': 'Already checked in today!',
                        'currentStreak': int(streak.get('currentStreak', 0)),
                        'longestStreak': int(streak.get('longestStreak', 0)),
                        'totalCheckIns': int(streak.get('totalCheckIns', 0)),
                        'streakFreezes': int(streak.get('streakFreezes', 0)),
                        'weeklyCheckIns': int(streak.get('weeklyCheckIns', 0)),
                        'newBadges': [], 'alreadyCheckedIn': True,
                        'freezeUsed': False, 'milestoneReached': None,
                        'freezeEarned': False, 'xp': {'xpAwarded': 0}
                    })
                elif days_diff == 1:
                    streak['currentStreak'] = int(streak.get('currentStreak', 0)) + 1
                elif days_diff == 2:
                    cur_freezes = int(streak.get('streakFreezes', 0))
                    cur_streak = int(streak.get('currentStreak', 0))
                    if cur_freezes > 0 and cur_streak > 0:
                        streak['streakFreezes'] = cur_freezes - 1
                        streak['freezesUsed'] = int(streak.get('freezesUsed', 0)) + 1
                        streak['currentStreak'] = cur_streak + 1
                        freeze_used = True
                    else:
                        streak['currentStreak'] = 1
                else:
                    streak['currentStreak'] = 1
            except Exception:
                streak['currentStreak'] = 1
        else:
            streak['currentStreak'] = 1

        streak['currentStreak'] = int(streak.get('currentStreak', 1))
        streak['longestStreak'] = int(streak.get('longestStreak', 0))
        if streak['currentStreak'] > streak['longestStreak']:
            streak['longestStreak'] = streak['currentStreak']

        streak['totalCheckIns'] = int(streak.get('totalCheckIns', 0)) + 1
        streak['weeklyCheckIns'] = int(streak.get('weeklyCheckIns', 0)) + 1
        streak['lastCheckIn'] = now.isoformat()

        milestones = streak.get('streakMilestones', [])
        if not isinstance(milestones, list):
            milestones = []
        for m in STREAK_MILESTONES:
            if streak['currentStreak'] >= m and m not in milestones:
                milestones.append(m)
                milestone_reached = {'days': m, 'name': MILESTONE_INFO[m]['name'], 'xp': MILESTONE_INFO[m]['xp']}
        streak['streakMilestones'] = milestones

        last_freeze = streak.get('lastFreezeEarned')
        can_earn = True
        if last_freeze:
            try:
                lfd = datetime.fromisoformat(str(last_freeze)).date()
                if (today - lfd).days < 7:
                    can_earn = False
            except (ValueError, TypeError):
                pass
        if streak['currentStreak'] > 0 and streak['currentStreak'] % 7 == 0 and can_earn:
            streak['streakFreezes'] = int(streak.get('streakFreezes', 0)) + 1
            streak['lastFreezeEarned'] = today.isoformat()
            freeze_earned = True

        table.put_item(Item=_clean({
            'user_id': user_id, 'record_type': 'STREAK',
            'currentStreak': streak['currentStreak'], 'longestStreak': streak['longestStreak'],
            'lastCheckIn': streak['lastCheckIn'], 'totalCheckIns': streak['totalCheckIns'],
            'streakFreezes': streak.get('streakFreezes', 0), 'freezesUsed': streak.get('freezesUsed', 0),
            'lastFreezeEarned': streak.get('lastFreezeEarned'),
            'streakMilestones': streak.get('streakMilestones', []),
            'weeklyCheckIns': streak.get('weeklyCheckIns', 0),
            'weekStartDate': streak.get('weekStartDate')
        }))

        new_badges = _check_streak_badges(user_id, streak['currentStreak'])
        xp_result = _award_xp(user_id, 'daily_check_in')
        if milestone_reached:
            ms_xp = _award_xp(user_id, 'streak_milestone', milestone_reached.get('xp', 100))
            xp_result['xpAwarded'] = xp_result.get('xpAwarded', 0) + ms_xp.get('xpAwarded', 0)

        msg = f'Check-in successful! {streak["currentStreak"]}-day streak!'
        if freeze_used:
            msg = f'Streak saved with freeze! {streak["currentStreak"]}-day streak!'
        if freeze_earned:
            msg += ' You earned a streak freeze!'

        return respond(200, {
            'success': True, 'message': msg,
            'currentStreak': int(streak['currentStreak']),
            'longestStreak': int(streak['longestStreak']),
            'totalCheckIns': int(streak['totalCheckIns']),
            'streakFreezes': int(streak.get('streakFreezes', 0)),
            'weeklyCheckIns': int(streak.get('weeklyCheckIns', 0)),
            'newBadges': new_badges, 'alreadyCheckedIn': False,
            'freezeUsed': freeze_used, 'milestoneReached': milestone_reached,
            'freezeEarned': freeze_earned, 'xp': xp_result
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
