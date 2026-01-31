import json
import os
import hashlib
import boto3
import jwt
from datetime import datetime, timezone, timedelta

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

        # Extract userid (email) from path parameters
        path_params = event.get('pathParameters') or {}
        userid = path_params.get('userid')

        if not userid:
            return respond(400, {'error': 'userid path parameter is required'})

        email = userid.strip().lower()

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        password = body.get('password')
        if not password:
            return respond(400, {'error': 'password is required'})

        # Retrieve user profile
        response = table.get_item(
            Key={
                'email': email,
                'record_type': 'PROFILE'
            }
        )

        item = response.get('Item')

        # User not found
        if not item:
            return respond(401, {'error': 'Invalid credentials'})

        # User is deactivated
        if not item.get('is_active', False):
            return respond(401, {'error': 'Account is deactivated'})

        # Verify password
        provided_hash = hash_password(password)
        stored_hash = item.get('password_hash', '')

        if provided_hash != stored_hash:
            return respond(401, {'error': 'Invalid credentials'})

        # Generate JWT token
        jwt_secret = os.environ['JWT_SECRET']
        now = datetime.now(timezone.utc)

        payload = {
            'email': email,
            'username': item.get('username', ''),
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(hours=24)).timestamp())
        }

        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        return respond(200, {
            'message': 'Login successful',
            'token': token,
            'email': email,
            'username': item.get('username', '')
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
