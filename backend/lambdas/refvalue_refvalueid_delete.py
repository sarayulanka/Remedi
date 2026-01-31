import json
import os
import boto3
from datetime import datetime, timezone

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
    """DELETE /refvalue/{refvalueid} — Delete a reference value."""
    try:
        table_name = os.environ.get('REFERENCE_VALUES_TABLE', 'remedi-reference-values')
        table = dynamodb.Table(table_name)

        # Extract refvalueid from path parameters
        path_params = event.get('pathParameters') or {}
        refvalueid = path_params.get('refvalueid')

        if not refvalueid:
            return respond(400, {'error': 'Missing refvalueid in path parameters'})

        # Parse refvalueid: format is "{reference_type}#{reference_id}"
        parts = refvalueid.split('#', 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return respond(400, {
                'error': 'Invalid refvalueid format. Expected format: reference_type#reference_id',
                'received': refvalueid
            })

        reference_type = parts[0]
        reference_id = parts[1]

        # DeleteItem
        table.delete_item(
            Key={
                'reference_type': reference_type,
                'reference_id': reference_id
            }
        )

        return respond(200, {
            'message': 'Reference value deleted successfully',
            'reference_type': reference_type,
            'reference_id': reference_id
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
