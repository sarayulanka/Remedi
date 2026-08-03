import json
import os
import hashlib
import uuid
import boto3
import jwt
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['USERS_TABLE'])

_secrets_cache = {}

def _get_secret(key):
    if not _secrets_cache:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId='remedi_api_keys')
        _secrets_cache.update(json.loads(resp['SecretString']))
    return _secrets_cache.get(key, '')

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


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    return salt.hex() + '$' + dk.hex()


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
        required_fields = ['email', 'username', 'password']
        missing_fields = [f for f in required_fields if not body.get(f)]
        if missing_fields:
            return respond(400, {
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            })

        email = body['email'].strip().lower()
        username = body['username'].strip()
        password = body['password']
        first_name = body.get('first_name', '').strip()
        last_name = body.get('last_name', '').strip()
        phone = body.get('phone', '').strip()

        # Validate email format (basic check)
        if '@' not in email or '.' not in email:
            return respond(400, {'error': 'Invalid email format'})

        # Validate password length
        if len(password) < 6:
            return respond(400, {'error': 'Password must be at least 6 characters'})

        # Check if email already exists via GSI
        email_query = table.query(
            IndexName='gsi-email',
            KeyConditionExpression=Key('email').eq(email),
            Limit=1
        )
        if email_query.get('Count', 0) > 0:
            return respond(409, {'error': 'An account with this email already exists'})

        # Check if username already exists via GSI
        username_query = table.query(
            IndexName='gsi-username',
            KeyConditionExpression=Key('username').eq(username),
            Limit=1
        )
        if username_query.get('Count', 0) > 0:
            return respond(409, {'error': 'Username is already taken'})

        # Generate user_id
        user_id = f"u-{uuid.uuid4()}"

        # Hash the password
        password_hash = hash_password(password)

        # Extract optional dietary preference fields
        nutrition_goals = body.get('nutrition_goals', [])
        food_allergies = body.get('food_allergies', [])
        diet_type = body.get('diet_type', None)

        # Build the profile item
        now = datetime.now(timezone.utc).isoformat()
        item = {
            'user_id': user_id,
            'record_type': 'PROFILE',
            'email': email,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'password_hash': password_hash,
            'phone': phone,
            'nutrition_goals': nutrition_goals if isinstance(nutrition_goals, list) else [],
            'food_allergies': food_allergies if isinstance(food_allergies, list) else [],
            'diet_type': diet_type if isinstance(diet_type, str) else '',
            'created_at': now,
            'updated_at': now,
            'is_active': True
        }

        # Store the item
        table.put_item(Item=item)

        # Generate JWT token so client doesn't need a separate login call
        jwt_secret = _get_secret('JWT_SECRET_KEY')
        now_dt = datetime.now(timezone.utc)
        payload = {
            'user_id': user_id,
            'email': email,
            'username': username,
            'iat': int(now_dt.timestamp()),
            'exp': int((now_dt + timedelta(hours=24)).timestamp())
        }
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')

        return respond(201, {
            'message': 'User created successfully',
            'token': token,
            'user_id': user_id,
            'email': email,
            'username': username
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
