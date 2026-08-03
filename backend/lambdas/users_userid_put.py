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

UPDATABLE_FIELDS = {'first_name', 'last_name', 'phone', 'username', 'nutrition_goals', 'food_allergies', 'diet_type'}


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

        # Extract user_id from path parameters
        path_params = event.get('pathParameters') or {}
        user_id = path_params.get('userid')

        if not user_id:
            return respond(400, {'error': 'userid path parameter is required'})

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        # Filter to only updatable fields that are present in the body
        updates = {}
        for k, v in body.items():
            if k not in UPDATABLE_FIELDS or v is None:
                continue
            if isinstance(v, str):
                updates[k] = v.strip()
            else:
                updates[k] = v

        if not updates:
            return respond(400, {
                'error': f"No valid fields to update. Updatable fields: {', '.join(sorted(UPDATABLE_FIELDS))}"
            })

        # Verify the user exists
        existing = table.get_item(
            Key={'user_id': user_id, 'record_type': 'PROFILE'}
        )
        if 'Item' not in existing:
            return respond(404, {'error': f"User not found: {user_id}"})

        current_item = existing['Item']

        # If username is being changed, check uniqueness
        if 'username' in updates and updates['username'] != current_item.get('username'):
            new_username = updates['username']

            if not new_username:
                return respond(400, {'error': 'Username cannot be empty'})

            username_query = table.query(
                IndexName='gsi-username',
                KeyConditionExpression=Key('username').eq(new_username),
                Limit=1
            )
            if username_query.get('Count', 0) > 0:
                return respond(409, {'error': 'Username is already taken'})

        # Add updated_at timestamp
        now = datetime.now(timezone.utc).isoformat()
        updates['updated_at'] = now

        # Build UpdateExpression dynamically
        update_parts = []
        expression_attr_names = {}
        expression_attr_values = {}

        for i, (field, value) in enumerate(updates.items()):
            placeholder_name = f"#f{i}"
            placeholder_value = f":v{i}"
            update_parts.append(f"{placeholder_name} = {placeholder_value}")
            expression_attr_names[placeholder_name] = field
            expression_attr_values[placeholder_value] = value

        update_expression = "SET " + ", ".join(update_parts)

        # Perform the update
        response = table.update_item(
            Key={
                'user_id': user_id,
                'record_type': 'PROFILE'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attr_names,
            ExpressionAttributeValues=expression_attr_values,
            ReturnValues='ALL_NEW'
        )

        # Exclude password_hash from response
        updated_item = response.get('Attributes', {})
        user = {k: v for k, v in updated_item.items() if k != 'password_hash'}

        return respond(200, {
            'message': 'User updated successfully',
            'user': user
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
