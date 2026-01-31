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
        # Extract userid (email) from path parameters
        userid = event['pathParameters']['userid']

        # Query all goals for this user
        all_goals = []
        response = table.query(
            KeyConditionExpression=Key('email').eq(userid)
        )
        all_goals = response.get('Items', [])

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=Key('email').eq(userid),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            all_goals.extend(response.get('Items', []))

        if not all_goals:
            return respond(200, {
                'message': 'No goals found for this user',
                'deleted_count': 0
            })

        # BatchWriteItem to delete all goals (handle batches of 25)
        deleted_count = 0
        batch_size = 25

        for i in range(0, len(all_goals), batch_size):
            batch = all_goals[i:i + batch_size]
            delete_requests = [
                {
                    'DeleteRequest': {
                        'Key': {
                            'email': goal['email'],
                            'goal_id': goal['goal_id']
                        }
                    }
                }
                for goal in batch
            ]

            # Execute batch write
            response = dynamodb.meta.client.batch_write_item(
                RequestItems={
                    os.environ['GOALS_TABLE']: delete_requests
                }
            )

            # Handle unprocessed items with retry
            unprocessed = response.get('UnprocessedItems', {})
            retry_count = 0
            max_retries = 3

            while unprocessed.get(os.environ['GOALS_TABLE']) and retry_count < max_retries:
                retry_count += 1
                response = dynamodb.meta.client.batch_write_item(
                    RequestItems=unprocessed
                )
                unprocessed = response.get('UnprocessedItems', {})

            deleted_count += len(batch)

        return respond(200, {
            'message': f'Successfully deleted all goals for user {userid}',
            'deleted_count': deleted_count
        })

    except KeyError as e:
        return respond(400, {'error': f'Missing required parameter: {str(e)}'})
    except Exception as e:
        return respond(500, {'error': str(e)})
