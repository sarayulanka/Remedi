import json
import os
import hashlib
import boto3
import jwt
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}


_secrets_cache = {}

def _get_secret(key):
    if not _secrets_cache:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId='remedi_api_keys')
        _secrets_cache.update(json.loads(resp['SecretString']))
    return _secrets_cache.get(key, '')


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return salt.hex() + '$' + dk.hex()


def verify_password(password, stored_hash):
    salt_hex, hash_hex = stored_hash.split('$')
    salt = bytes.fromhex(salt_hex)
    return hash_password(password, salt) == stored_hash


def lambda_handler(event, context):
    try:
        # Handle OPTIONS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        # Extract email from path (userid parameter contains email for login)
        path_params = event.get('pathParameters') or {}
        email_param = path_params.get('userid')

        if not email_param:
            return respond(400, {'error': 'Email is required in path'})

        email = email_param.strip().lower()

        # Parse request body
        body = event.get('body')
        if not body:
            return respond(400, {'error': 'Request body is required'})

        if isinstance(body, str):
            body = json.loads(body)

        password = body.get('password')
        if not password:
            return respond(400, {'error': 'password is required'})

        # Look up user by email via GSI
        email_query = table.query(
            IndexName='gsi-email',
            KeyConditionExpression=Key('email').eq(email),
            Limit=1
        )

        if email_query.get('Count', 0) == 0:
            return respond(401, {'error': 'Invalid credentials'})

        # Get the user_id from GSI result, then fetch full profile
        gsi_item = email_query['Items'][0]
        user_id = gsi_item['user_id']

        # Fetch full profile with password hash
        response = table.get_item(
            Key={'user_id': user_id, 'record_type': 'PROFILE'},
            ConsistentRead=True
        )

        item = response.get('Item')
        if not item:
            return respond(401, {'error': 'Invalid credentials'})

        # User is deactivated
        if not item.get('is_active', False):
            return respond(401, {'error': 'Account is deactivated'})

        # Verify password
        stored_hash = item.get('password_hash', '')

        if not verify_password(password, stored_hash):
            return respond(401, {'error': 'Invalid credentials'})

        # Generate JWT token
        jwt_secret = _get_secret('JWT_SECRET_KEY')
        now = datetime.now(timezone.utc)

        payload = {
            'user_id': user_id,
            'email': email,
            'username': item.get('username', ''),
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(hours=24)).timestamp())
        }

        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        return respond(200, {
            'message': 'Login successful',
            'token': token,
            'user_id': user_id,
            'email': email,
            'username': item.get('username', '')
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
