import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

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

        # Check for optional status query parameter
        query_params = event.get('queryStringParameters') or {}
        status_filter = query_params.get('status')

        # Validate status if provided
        valid_statuses = ('ACTIVE', 'COMPLETED', 'ABANDONED')
        if status_filter and status_filter not in valid_statuses:
            return respond(400, {
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            })

        goals = []

        if status_filter:
            # Query GSI gsi-user-status with begins_with on sort key
            response = table.query(
                IndexName='gsi-user-status',
                KeyConditionExpression=(
                    Key('user_id').eq(user_id) &
                    Key('status_created_at').begins_with(f"{status_filter}#")
                )
            )
            goals = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    IndexName='gsi-user-status',
                    KeyConditionExpression=(
                        Key('user_id').eq(user_id) &
                        Key('status_created_at').begins_with(f"{status_filter}#")
                    ),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                goals.extend(response.get('Items', []))
        else:
            # Query base table with just partition key
            response = table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            goals = response.get('Items', [])

            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    KeyConditionExpression=Key('user_id').eq(user_id),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                goals.extend(response.get('Items', []))

        return respond(200, {'goals': goals, 'count': len(goals)})

    except KeyError as e:
        return respond(400, {'error': f'Missing required parameter: {str(e)}'})
    except Exception as e:
        return respond(500, {'error': str(e)})
