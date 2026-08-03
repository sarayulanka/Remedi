import json
import os
import boto3
from datetime import datetime, timezone

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
        # Extract user_id and goalid from path parameters
        user_id = event['pathParameters']['userid']
        goalid = event['pathParameters']['goalid']

        # Delete the item from DynamoDB
        # Use ConditionExpression to confirm the item exists before deleting
        try:
            table.delete_item(
                Key={
                    'user_id': user_id,
                    'goal_id': goalid
                },
                ConditionExpression='attribute_exists(user_id) AND attribute_exists(goal_id)'
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return respond(404, {
                'error': f'Goal {goalid} not found for user {user_id}'
            })

        return respond(200, {
            'message': f'Goal {goalid} successfully deleted for user {user_id}'
        })

    except KeyError as e:
        return respond(400, {'error': f'Missing required parameter: {str(e)}'})
    except Exception as e:
        return respond(500, {'error': str(e)})
