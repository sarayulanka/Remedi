import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

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
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        userid = path_params.get('userid')

        if not userid:
            return respond(400, {'error': 'userid path parameter is required'})

        email = userid.strip().lower()

        # Query ALL items for this partition key (profile + all preferences)
        items_to_delete = []
        query_kwargs = {
            'KeyConditionExpression': Key('email').eq(email)
        }

        while True:
            response = table.query(**query_kwargs)
            items = response.get('Items', [])
            items_to_delete.extend(items)

            last_key = response.get('LastEvaluatedKey')
            if not last_key:
                break
            query_kwargs['ExclusiveStartKey'] = last_key

        if not items_to_delete:
            return respond(404, {'error': f"User not found: {email}"})

        # BatchWriteItem to delete all items for this user
        # DynamoDB BatchWriteItem supports max 25 items per batch
        deleted_count = 0
        batch_size = 25

        for i in range(0, len(items_to_delete), batch_size):
            batch = items_to_delete[i:i + batch_size]
            delete_requests = [
                {
                    'DeleteRequest': {
                        'Key': {
                            'email': item['email'],
                            'record_type': item['record_type']
                        }
                    }
                }
                for item in batch
            ]

            # Execute batch write
            table_name = os.environ['USERS_TABLE']
            request_items = {table_name: delete_requests}

            while request_items:
                batch_response = dynamodb.meta.client.batch_write_item(
                    RequestItems=request_items
                )
                # Handle unprocessed items (retry)
                request_items = batch_response.get('UnprocessedItems', {})

            deleted_count += len(batch)

        return respond(200, {
            'message': f"User '{email}' and all associated data deleted successfully",
            'items_deleted': deleted_count
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
