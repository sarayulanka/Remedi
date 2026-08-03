import json
import os
import uuid
import boto3
from datetime import datetime, timezone, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['GOALS_TABLE'])

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
        # Extract user_id from path parameters
        user_id = event['pathParameters']['userid']

        # Parse request body
        body = json.loads(event.get('body', '{}') or '{}')

        # Validate required fields
        title = body.get('title')
        target_days = body.get('target_days')

        if not title:
            return respond(400, {'error': 'title is required'})

        if target_days is None:
            return respond(400, {'error': 'target_days is required'})

        try:
            target_days = int(target_days)
            if target_days <= 0:
                return respond(400, {'error': 'target_days must be a positive integer'})
        except (ValueError, TypeError):
            return respond(400, {'error': 'target_days must be a valid integer'})

        # Generate goal_id and timestamps
        goal_id = f"g-{uuid.uuid4()}"
        now = datetime.now(timezone.utc)
        created_at = now.isoformat()
        updated_at = created_at
        start_date = now.strftime('%Y-%m-%d')
        end_date = (now + timedelta(days=target_days)).strftime('%Y-%m-%d')

        # Build the goal item
        item = {
            'user_id': user_id,
            'goal_id': goal_id,
            'title': title,
            'description': body.get('description', ''),
            'target_days': target_days,
            'completed_days': 0,
            'status': 'ACTIVE',
            'status_created_at': f"ACTIVE#{created_at}",
            'start_date': start_date,
            'end_date': end_date,
            'created_at': created_at,
            'updated_at': updated_at,
            'last_progress_date': ''
        }

        # Write to DynamoDB
        table.put_item(Item=item)

        return respond(201, item)

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except KeyError as e:
        return respond(400, {'error': f'Missing required parameter: {str(e)}'})
    except Exception as e:
        return respond(500, {'error': str(e)})
