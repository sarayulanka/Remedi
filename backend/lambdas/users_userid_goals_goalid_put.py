import json
import os
import boto3
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['GOALS_TABLE'])

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


def lambda_handler(event, context):
    try:
        # Extract userid (email) and goalid from path parameters
        userid = event['pathParameters']['userid']
        goalid = event['pathParameters']['goalid']

        # Parse request body
        body = json.loads(event.get('body', '{}') or '{}')

        # First, verify the goal exists
        existing_response = table.get_item(
            Key={
                'email': userid,
                'goal_id': goalid
            }
        )

        existing_item = existing_response.get('Item')
        if not existing_item:
            return respond(404, {
                'error': f'Goal {goalid} not found for user {userid}'
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
                'email': userid,
                'goal_id': goalid
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )

        updated_item = response.get('Attributes', {})

        return respond(200, updated_item)

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except KeyError as e:
        return respond(400, {'error': f'Missing required parameter: {str(e)}'})
    except Exception as e:
        return respond(500, {'error': str(e)})
