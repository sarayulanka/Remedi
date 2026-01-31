import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

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
    """GET /refvalue — List reference values, optionally filtered by type and active status."""
    try:
        table_name = os.environ.get('REFERENCE_VALUES_TABLE', 'remedi-reference-values')
        table = dynamodb.Table(table_name)

        # Parse optional query parameters
        query_params = event.get('queryStringParameters') or {}
        ref_type = query_params.get('type')
        active_only = query_params.get('active_only', 'false').lower() == 'true'

        items = []

        if ref_type:
            # Query by reference_type (PK)
            query_kwargs = {
                'KeyConditionExpression': Key('reference_type').eq(ref_type)
            }

            if active_only:
                query_kwargs['FilterExpression'] = Attr('is_active').eq(True)

            response = table.query(**query_kwargs)
            items = response.get('Items', [])

            # Paginate through all results
            while 'LastEvaluatedKey' in response:
                query_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.query(**query_kwargs)
                items.extend(response.get('Items', []))

        else:
            # Scan entire table
            scan_kwargs = {}

            if active_only:
                scan_kwargs['FilterExpression'] = Attr('is_active').eq(True)

            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])

            # Paginate through all results
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))

        # Sort by sort_order if available, then by reference_id
        items.sort(key=lambda x: (x.get('sort_order', 999999), x.get('reference_id', '')))

        return respond(200, {
            'reference_values': items,
            'count': len(items)
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
