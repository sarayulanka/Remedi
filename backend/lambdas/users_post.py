import json
import os
import hashlib
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


def hash_password(password):
    salt = os.environ['PASSWORD_SALT']
    return hashlib.sha256(f"{salt}{password}".encode('utf-8')).hexdigest()


def lambda_handler(event, context):
    try:
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        # Validate required fields
        required_fields = ['email', 'username', 'password', 'first_name', 'last_name']
        missing_fields = [f for f in required_fields if not body.get(f)]
        if missing_fields:
            return respond(400, {
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            })

        email = body['email'].strip().lower()
        username = body['username'].strip()
        password = body['password']
        first_name = body['first_name'].strip()
        last_name = body['last_name'].strip()
        phone = body.get('phone', '').strip()

        # Validate email format (basic check)
        if '@' not in email or '.' not in email:
            return respond(400, {'error': 'Invalid email format'})

        # Validate password length
        if len(password) < 6:
            return respond(400, {'error': 'Password must be at least 6 characters'})

        # Check if email already exists
        existing_user = table.get_item(
            Key={'email': email, 'record_type': 'PROFILE'}
        )
        if 'Item' in existing_user:
            return respond(409, {'error': 'An account with this email already exists'})

        # Check if username already exists via GSI
        username_query = table.query(
            IndexName='gsi-username',
            KeyConditionExpression=Key('username').eq(username),
            Limit=1
        )
        if username_query.get('Count', 0) > 0:
            return respond(409, {'error': 'Username is already taken'})

        # Hash the password
        password_hash = hash_password(password)

        # Build the profile item
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'email': email,
            'record_type': 'PROFILE',
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'password_hash': password_hash,
            'phone': phone,
            'created_at': now,
            'updated_at': now,
            'is_active': True
        }

        # Store the item
        table.put_item(Item=item)

        # Build response (exclude password_hash)
        response_item = {k: v for k, v in item.items() if k != 'password_hash'}

        return respond(201, {
            'message': 'User created successfully',
            'user': response_item
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
