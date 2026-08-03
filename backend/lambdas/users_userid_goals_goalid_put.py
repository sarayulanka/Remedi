import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['GOALS_TABLE'])
users_table = dynamodb.Table(os.environ['USERS_TABLE'])

# XP system constants
XP_VALUES = {'goal_progress': 15, 'goal_completed': 50}
COMBO_MULTIPLIERS = {1: 1.0, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0}

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

VALID_STATUSES = ('ACTIVE', 'COMPLETED', 'ABANDONED')
UPDATABLE_FIELDS = ('title', 'description', 'target_days', 'completed_days', 'status', 'last_progress_date')


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _clean(item):
    """Clean floats to Decimal for DynamoDB."""
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


def _award_xp(user_id, action, base_amount=None):
    """Award XP to user for goal-related actions."""
    if base_amount is None:
        base_amount = XP_VALUES.get(action, 10)
    resp = users_table.get_item(Key={'user_id': user_id, 'record_type': 'XP'})
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
    users_table.put_item(Item=_clean(xp))
    return {'xpAwarded': final_xp, 'totalXP': new_total, 'levelUp': new_level > old_level,
            'newLevel': new_level if new_level > old_level else None}


def lambda_handler(event, context):
    try:
        # Extract user_id and goalid from path parameters
        user_id = event['pathParameters']['userid']
        goalid = event['pathParameters']['goalid']

        # Parse request body
        body = json.loads(event.get('body', '{}') or '{}')

        # First, verify the goal exists
        existing_response = table.get_item(
            Key={
                'user_id': user_id,
                'goal_id': goalid
            }
        )

        existing_item = existing_response.get('Item')
        if not existing_item:
            return respond(404, {
                'error': f'Goal {goalid} not found for user {user_id}'
            })

        # Collect fields to update
        updates = {}
        for field in UPDATABLE_FIELDS:
            if field in body:
                updates[field] = body[field]

        if not updates:
            return respond(400, {'error': 'No updatable fields provided. Updatable fields: ' + ', '.join(UPDATABLE_FIELDS)})

        # Validate specific fields
        if 'target_days' in updates:
            try:
                updates['target_days'] = int(updates['target_days'])
                if updates['target_days'] <= 0:
                    return respond(400, {'error': 'target_days must be a positive integer'})
            except (ValueError, TypeError):
                return respond(400, {'error': 'target_days must be a valid integer'})

        if 'completed_days' in updates:
            try:
                updates['completed_days'] = int(updates['completed_days'])
                if updates['completed_days'] < 0:
                    return respond(400, {'error': 'completed_days must be a non-negative integer'})
            except (ValueError, TypeError):
                return respond(400, {'error': 'completed_days must be a valid integer'})

        if 'status' in updates:
            if updates['status'] not in VALID_STATUSES:
                return respond(400, {
                    'error': f'Invalid status. Must be one of: {", ".join(VALID_STATUSES)}'
                })

        if 'last_progress_date' in updates:
            if updates['last_progress_date'] is not None:
                try:
                    datetime.strptime(updates['last_progress_date'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    return respond(400, {'error': 'last_progress_date must be in YYYY-MM-DD format or null'})

        # Determine the effective target_days and completed_days for auto-completion check
        effective_target_days = updates.get('target_days', existing_item.get('target_days', 0))
        effective_completed_days = updates.get('completed_days', existing_item.get('completed_days', 0))

        # Convert Decimal types from DynamoDB to int for comparison
        effective_target_days = int(effective_target_days)
        effective_completed_days = int(effective_completed_days)

        # Auto-complete: if completed_days >= target_days, set status to COMPLETED
        if effective_completed_days >= effective_target_days:
            updates['status'] = 'COMPLETED'

        # If status changed, update status_created_at using the original created_at
        original_created_at = existing_item.get('created_at', '')
        effective_status = updates.get('status', existing_item.get('status', 'ACTIVE'))

        if effective_status != existing_item.get('status'):
            updates['status_created_at'] = f"{effective_status}#{original_created_at}"

        # If target_days changed, recalculate end_date from start_date
        if 'target_days' in updates:
            start_date_str = existing_item.get('start_date', '')
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                new_end_date = (start_date + timedelta(days=int(updates['target_days']))).strftime('%Y-%m-%d')
                updates['end_date'] = new_end_date
            except (ValueError, TypeError):
                pass  # Keep existing end_date if start_date is invalid

        # Always update updated_at
        now = datetime.now(timezone.utc)
        updates['updated_at'] = now.isoformat()

        # Build UpdateExpression dynamically
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        for idx, (field, value) in enumerate(updates.items()):
            attr_name = f"#attr{idx}"
            attr_value = f":val{idx}"
            update_expression_parts.append(f"{attr_name} = {attr_value}")
            expression_attribute_names[attr_name] = field
            expression_attribute_values[attr_value] = value

        update_expression = "SET " + ", ".join(update_expression_parts)

        # Execute update
        response = table.update_item(
            Key={
                'user_id': user_id,
                'goal_id': goalid
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )

        updated_item = response.get('Attributes', {})

        # Award XP for goal progress
        xp_result = None
        old_completed_days = int(existing_item.get('completed_days', 0))
        new_completed_days = int(updated_item.get('completed_days', 0))
        old_status = existing_item.get('status', 'ACTIVE')
        new_status = updated_item.get('status', 'ACTIVE')

        if new_completed_days > old_completed_days:
            # Award XP for making progress
            xp_result = _award_xp(user_id, 'goal_progress')

            # Award bonus XP if goal was just completed
            if new_status == 'COMPLETED' and old_status != 'COMPLETED':
                completion_xp = _award_xp(user_id, 'goal_completed')
                xp_result['xpAwarded'] += completion_xp['xpAwarded']
                xp_result['totalXP'] = completion_xp['totalXP']
                xp_result['levelUp'] = xp_result.get('levelUp') or completion_xp.get('levelUp')
                if completion_xp.get('newLevel'):
                    xp_result['newLevel'] = completion_xp['newLevel']

        # Include XP info in response
        response_data = dict(updated_item)
        if xp_result:
            response_data['xp'] = xp_result

        return respond(200, response_data)

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except KeyError as e:
        return respond(400, {'error': f'Missing required parameter: {str(e)}'})
    except Exception as e:
        return respond(500, {'error': str(e)})
