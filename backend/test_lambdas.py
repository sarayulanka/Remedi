#!/usr/bin/env python3
"""Comprehensive integration tests for all 37 Remedi Lambda functions.
Covers every validation branch, error path, edge case, and boundary condition."""

import os, sys, json, importlib, traceback, time

# -- Environment variables (must be set BEFORE Lambda imports) ----------
os.environ.setdefault('USERS_TABLE', 'remedi-users')
os.environ.setdefault('ACTIVITY_TABLE', 'remedi-user-activity')
os.environ.setdefault('GOALS_TABLE', 'remedi-goals')
os.environ.setdefault('REWARDS_TABLE', 'remedi-rewards')
os.environ.setdefault('ALERTS_TABLE', 'remedi-alerts')
os.environ.setdefault('NOTIFICATIONS_TABLE', 'remedi-notifications')
os.environ.setdefault('RECIPES_TABLE', 'remedi-recipes')
os.environ.setdefault('REFERENCE_VALUES_TABLE', 'remedi-reference-values')
os.environ.setdefault('PASSWORD_SALT', 'test-salt-12345')
os.environ.setdefault('JWT_SECRET', 'test-jwt-secret-67890')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

import boto3
from moto import mock_aws

# -- Globals filled during test run -------------------------------------
PASS_COUNT = 0
FAIL_COUNT = 0
FAILURES = []

# Test data constants
TEST_EMAIL = 'test@example.com'
TEST_USERNAME = 'testuser'
TEST_PASSWORD = 'password123'


def create_all_tables(dynamodb):
    """Create all DynamoDB tables with correct schemas."""

    dynamodb.create_table(
        TableName='remedi-users',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
            {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'record_type', 'AttributeType': 'S'},
            {'AttributeName': 'username', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'gsi-username',
            'KeySchema': [{'AttributeName': 'username', 'KeyType': 'HASH'}],
            'Projection': {'ProjectionType': 'KEYS_ONLY'},
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        }],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-user-activity',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-goals',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
            {'AttributeName': 'goal_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'goal_id', 'AttributeType': 'S'},
            {'AttributeName': 'status_created_at', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'gsi-email-status',
            'KeySchema': [
                {'AttributeName': 'email', 'KeyType': 'HASH'},
                {'AttributeName': 'status_created_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        }],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-rewards',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
            {'AttributeName': 'date_reward_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'date_reward_id', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-alerts',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
            {'AttributeName': 'alert_date_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'alert_date_id', 'AttributeType': 'S'},
            {'AttributeName': 'condition_alert_date', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'gsi-email-condition',
            'KeySchema': [
                {'AttributeName': 'email', 'KeyType': 'HASH'},
                {'AttributeName': 'condition_alert_date', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        }],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-notifications',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},
            {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'read_status_created_at', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'gsi-email-read-status',
            'KeySchema': [
                {'AttributeName': 'email', 'KeyType': 'HASH'},
                {'AttributeName': 'read_status_created_at', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'},
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        }],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-recipes',
        KeySchema=[
            {'AttributeName': 'recipe_id', 'KeyType': 'HASH'},
            {'AttributeName': 'record_type', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'recipe_id', 'AttributeType': 'S'},
            {'AttributeName': 'record_type', 'AttributeType': 'S'},
            {'AttributeName': 'meal_type', 'AttributeType': 'S'},
            {'AttributeName': 'created_at', 'AttributeType': 'S'},
            {'AttributeName': 'cuisine_type', 'AttributeType': 'S'},
            {'AttributeName': 'gsi3_pk', 'AttributeType': 'S'},
            {'AttributeName': 'difficulty_level', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'gsi-meal-type',
                'KeySchema': [
                    {'AttributeName': 'meal_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            },
            {
                'IndexName': 'gsi-cuisine-type',
                'KeySchema': [
                    {'AttributeName': 'cuisine_type', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            },
            {
                'IndexName': 'gsi-diet-allergen-index',
                'KeySchema': [
                    {'AttributeName': 'gsi3_pk', 'KeyType': 'HASH'},
                    {'AttributeName': 'recipe_id', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            },
            {
                'IndexName': 'gsi-difficulty',
                'KeySchema': [
                    {'AttributeName': 'difficulty_level', 'KeyType': 'HASH'},
                    {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'},
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            }
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    dynamodb.create_table(
        TableName='remedi-reference-values',
        KeySchema=[
            {'AttributeName': 'reference_type', 'KeyType': 'HASH'},
            {'AttributeName': 'reference_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'reference_type', 'AttributeType': 'S'},
            {'AttributeName': 'reference_id', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )


def seed_recipes(dynamodb):
    """Insert test recipe data for search/scan tests."""
    table = dynamodb.Table('remedi-recipes')
    # Recipe 1: Breakfast, American, Easy, Vegan
    table.put_item(Item={
        'recipe_id': 'r-test-001',
        'record_type': 'META',
        'title': 'Healthy Green Smoothie',
        'description': 'A nutritious green smoothie with spinach and banana',
        'meal_type': 'BREAKFAST',
        'cuisine_type': 'AMERICAN',
        'difficulty_level': 'EASY',
        'calories_per_serving': 250,
        'protein_g': 8,
        'carbs_g': 45,
        'fat_g': 5,
        'fiber_g': 6,
        'total_time_minutes': 10,
        'servings': 2,
        'image_url': '',
        'created_at': '2026-01-30T00:00:00Z'
    })
    table.put_item(Item={
        'recipe_id': 'r-test-001',
        'record_type': 'DIET#VEGAN',
        'gsi3_pk': 'DIET#VEGAN',
        'reference_value': 'Vegan'
    })
    # Recipe 2: Lunch, Italian, Medium, contains GLUTEN
    table.put_item(Item={
        'recipe_id': 'r-test-002',
        'record_type': 'META',
        'title': 'Chicken Pasta',
        'description': 'Classic Italian chicken pasta with garlic',
        'meal_type': 'LUNCH',
        'cuisine_type': 'ITALIAN',
        'difficulty_level': 'MEDIUM',
        'calories_per_serving': 550,
        'protein_g': 35,
        'carbs_g': 60,
        'fat_g': 15,
        'fiber_g': 3,
        'total_time_minutes': 30,
        'servings': 4,
        'image_url': '',
        'created_at': '2026-01-29T00:00:00Z'
    })
    table.put_item(Item={
        'recipe_id': 'r-test-002',
        'record_type': 'ALRG#GLUTEN',
        'gsi3_pk': 'ALRG#GLUTEN',
        'reference_value': 'Contains Gluten'
    })
    # Recipe 3: Dinner, Indian, Hard, Vegan, low calorie
    table.put_item(Item={
        'recipe_id': 'r-test-003',
        'record_type': 'META',
        'title': 'Vegetable Curry',
        'description': 'Spicy Indian vegetable curry',
        'meal_type': 'DINNER',
        'cuisine_type': 'INDIAN',
        'difficulty_level': 'HARD',
        'calories_per_serving': 180,
        'protein_g': 12,
        'carbs_g': 25,
        'fat_g': 6,
        'fiber_g': 8,
        'total_time_minutes': 60,
        'servings': 3,
        'image_url': '',
        'created_at': '2026-01-28T00:00:00Z'
    })
    table.put_item(Item={
        'recipe_id': 'r-test-003',
        'record_type': 'DIET#VEGAN',
        'gsi3_pk': 'DIET#VEGAN',
        'reference_value': 'Vegan'
    })


def load_handler(module_name):
    """Import (or reimport) a Lambda module and return its handler."""
    if module_name in sys.modules:
        mod = importlib.reload(sys.modules[module_name])
    else:
        mod = importlib.import_module(module_name)
    return mod.lambda_handler


def run_test(name, handler, event, expected_status):
    """Run a single test case. Returns (passed:bool, parsed_body:dict)."""
    global PASS_COUNT, FAIL_COUNT, FAILURES
    try:
        result = handler(event, None)
        status = result.get('statusCode')
        body_str = result.get('body', '{}')
        body = json.loads(body_str) if body_str else {}

        if status == expected_status:
            PASS_COUNT += 1
            print(f"  PASS  {name}")
            return True, body
        else:
            FAIL_COUNT += 1
            err_msg = body.get('error', body.get('message', body_str[:120]))
            FAILURES.append((name, f"expected {expected_status}, got {status}: {err_msg}"))
            print(f"  FAIL  {name}  (expected {expected_status}, got {status}: {err_msg})")
            return False, body
    except Exception as e:
        FAIL_COUNT += 1
        tb = traceback.format_exc()
        FAILURES.append((name, str(e)))
        print(f"  FAIL  {name}  EXCEPTION: {e}")
        print(f"        {tb.splitlines()[-2].strip()}")
        return False, {}


def make_event(method='GET', path_params=None, query_params=None, body=None):
    """Build a mock API Gateway event."""
    event = {'httpMethod': method}
    if path_params is not None:
        event['pathParameters'] = path_params
    else:
        event['pathParameters'] = {}
    if query_params is not None:
        event['queryStringParameters'] = query_params
    if body is not None:
        event['body'] = json.dumps(body) if isinstance(body, dict) else body
    return event


# ======================================================================════
#  T E S T   S U I T E S
# ======================================================================════

def test_users_post(h):
    """Tests for POST /users"""
    print("\n-- users_post --")

    # OPTIONS preflight
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing body
    run_test("Missing body", h, make_event('POST'), 400)

    # Empty body string
    run_test("Empty body string", h, {'httpMethod': 'POST', 'body': '', 'pathParameters': {}}, 400)

    # Invalid JSON body
    run_test("Invalid JSON body", h, {'httpMethod': 'POST', 'body': 'not-json', 'pathParameters': {}}, 400)

    # Missing all required fields
    run_test("Missing all required fields", h, make_event('POST', body={}), 400)

    # Missing individual required fields
    run_test("Missing email only", h, make_event('POST', body={
        'username': 'u', 'password': 'pass123', 'first_name': 'F', 'last_name': 'L'
    }), 400)
    run_test("Missing username only", h, make_event('POST', body={
        'email': 'a@b.com', 'password': 'pass123', 'first_name': 'F', 'last_name': 'L'
    }), 400)
    run_test("Missing password only", h, make_event('POST', body={
        'email': 'a@b.com', 'username': 'u', 'first_name': 'F', 'last_name': 'L'
    }), 400)
    run_test("Missing first_name only", h, make_event('POST', body={
        'email': 'a@b.com', 'username': 'u', 'password': 'pass123', 'last_name': 'L'
    }), 400)
    run_test("Missing last_name only", h, make_event('POST', body={
        'email': 'a@b.com', 'username': 'u', 'password': 'pass123', 'first_name': 'F'
    }), 400)

    # Invalid email format (no @)
    run_test("Invalid email - no @", h, make_event('POST', body={
        'email': 'bademail.com', 'username': 'u1', 'password': 'pass123',
        'first_name': 'F', 'last_name': 'L'
    }), 400)

    # Invalid email format (no .)
    run_test("Invalid email - no .", h, make_event('POST', body={
        'email': 'bad@email', 'username': 'u1', 'password': 'pass123',
        'first_name': 'F', 'last_name': 'L'
    }), 400)

    # Password too short
    run_test("Password too short", h, make_event('POST', body={
        'email': 'a@b.com', 'username': 'u1', 'password': '12345',
        'first_name': 'F', 'last_name': 'L'
    }), 400)

    # Password exactly 6 chars (boundary)
    run_test("Password exactly 6 chars", h, make_event('POST', body={
        'email': 'boundary@test.com', 'username': 'boundary_user', 'password': '123456',
        'first_name': 'F', 'last_name': 'L'
    }), 201)

    # Successful creation
    ok, body = run_test("Create user success", h, make_event('POST', body={
        'email': TEST_EMAIL, 'username': TEST_USERNAME, 'password': TEST_PASSWORD,
        'first_name': 'Test', 'last_name': 'User', 'phone': '1234567890'
    }), 201)

    # Verify password_hash is NOT in response
    if ok:
        user = body.get('user', {})
        if 'password_hash' in user:
            print("  WARN  password_hash leaked in response!")

    # Duplicate email
    run_test("Duplicate email", h, make_event('POST', body={
        'email': TEST_EMAIL, 'username': 'different', 'password': TEST_PASSWORD,
        'first_name': 'F', 'last_name': 'L'
    }), 409)

    # Duplicate username
    run_test("Duplicate username", h, make_event('POST', body={
        'email': 'other@test.com', 'username': TEST_USERNAME, 'password': TEST_PASSWORD,
        'first_name': 'F', 'last_name': 'L'
    }), 409)

    # Body passed as dict (not string) - tests isinstance branch
    run_test("Body as dict (non-string)", h, {
        'httpMethod': 'POST', 'pathParameters': {},
        'body': {'email': 'dict@test.com', 'username': 'dictuser', 'password': 'pass123',
                 'first_name': 'D', 'last_name': 'U'}
    }, 201)


def test_users_get(h):
    """Tests for GET /users"""
    print("\n-- users_get --")

    # OPTIONS preflight
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Basic list (should have users from previous test)
    ok, body = run_test("List users", h, make_event('GET'), 200)
    if ok:
        assert body.get('count', 0) > 0, "Should have at least 1 user"

    # With limit=1
    run_test("List users with limit=1", h, make_event('GET', query_params={'limit': '1'}), 200)

    # Invalid limit (non-numeric) falls back to default 20
    run_test("Invalid limit param", h, make_event('GET', query_params={'limit': 'abc'}), 200)

    # Limit = 0 (should be clamped to 1)
    run_test("Limit=0 clamped to 1", h, make_event('GET', query_params={'limit': '0'}), 200)

    # Limit = 999 (clamped to 100)
    run_test("Limit=999 clamped to 100", h, make_event('GET', query_params={'limit': '999'}), 200)

    # Invalid last_evaluated_key
    run_test("Invalid last_evaluated_key", h,
             make_event('GET', query_params={'last_evaluated_key': 'not-json'}), 400)

    # Null queryStringParameters
    run_test("Null queryStringParameters", h,
             {'httpMethod': 'GET', 'pathParameters': {}, 'queryStringParameters': None}, 200)


def test_users_userid_get(h):
    """Tests for GET /users/{userid}"""
    print("\n-- users_userid_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={}), 400)

    # Null pathParameters
    run_test("Null pathParameters", h, {'httpMethod': 'GET', 'pathParameters': None}, 400)

    # User not found
    run_test("User not found", h, make_event('GET', path_params={'userid': 'nonexistent@test.com'}), 404)

    # Success
    ok, body = run_test("Get user success", h, make_event('GET', path_params={'userid': TEST_EMAIL}), 200)
    if ok:
        user = body.get('user', {})
        assert 'password_hash' not in user, "password_hash should be excluded"

    # Email case normalization (uppercase should find lowercase)
    run_test("Email case normalization", h,
             make_event('GET', path_params={'userid': TEST_EMAIL.upper()}), 200)


def test_users_userid_put(h):
    """Tests for PUT /users/{userid}"""
    print("\n-- users_userid_put --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('PUT', path_params={}, body={'first_name': 'New'}), 400)

    # Missing body
    run_test("Missing body", h, make_event('PUT', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON body", h, {
        'httpMethod': 'PUT', 'pathParameters': {'userid': TEST_EMAIL}, 'body': '{broken'
    }, 400)

    # No valid updatable fields
    run_test("No updatable fields", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'email': 'cant@change.com', 'password': 'nope'}), 400)

    # User not found
    run_test("User not found", h, make_event('PUT', path_params={'userid': 'nonexistent@test.com'},
             body={'first_name': 'X'}), 404)

    # Fields with None value should be skipped
    run_test("Null field values skipped", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'first_name': None, 'last_name': 'Updated'}), 200)

    # Successful update
    run_test("Update first_name", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'first_name': 'Updated'}), 200)

    # Update multiple fields
    run_test("Update multiple fields", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'first_name': 'Multi', 'last_name': 'Update', 'phone': '9999999999'}), 200)

    # Change username to taken username -> 409
    # First create another user
    post_h = load_handler('lambdas.users_post')
    post_h(make_event('POST', body={
        'email': 'user2@test.com', 'username': 'user2', 'password': 'pass123',
        'first_name': 'U', 'last_name': 'T'
    }), None)
    run_test("Username already taken", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'username': 'user2'}), 409)

    # Change to empty username
    run_test("Empty username", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'username': ''}), 400)

    # Change username to same (no conflict check)
    run_test("Same username no conflict", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'username': TEST_USERNAME}), 200)


def test_users_userid_delete(h):
    """Tests for DELETE /users/{userid}"""
    print("\n-- users_userid_delete --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('DELETE', path_params={}), 400)

    # User not found
    run_test("User not found", h, make_event('DELETE', path_params={'userid': 'ghost@test.com'}), 404)

    # Create a temp user, add preferences, then delete all
    post_h = load_handler('lambdas.users_post')
    post_h(make_event('POST', body={
        'email': 'deleteme@test.com', 'username': 'deluser', 'password': 'pass123',
        'first_name': 'D', 'last_name': 'M'
    }), None)
    # Add a preference for this user
    pref_h = load_handler('lambdas.users_userid_preferences_post')
    pref_h(make_event('POST', path_params={'userid': 'deleteme@test.com'},
           body={'preferences': [{'type': 'DIET', 'value': 'VEGAN'}]}), None)

    ok, body = run_test("Delete user with preferences", h,
                        make_event('DELETE', path_params={'userid': 'deleteme@test.com'}), 200)
    if ok:
        assert body.get('items_deleted', 0) >= 2, "Should delete profile + preferences"


def test_users_userid_login_post(h):
    """Tests for POST /users/{userid}/login"""
    print("\n-- users_userid_login_post --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('POST', path_params={}, body={'password': 'x'}), 400)

    # Missing body
    run_test("Missing body", h, make_event('POST', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'POST', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'not-json'
    }, 400)

    # Missing password field
    run_test("Missing password", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'not_password': 'x'}), 400)

    # Empty password
    run_test("Empty password", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'password': ''}), 400)

    # User not found
    run_test("User not found", h, make_event('POST', path_params={'userid': 'ghost@test.com'},
             body={'password': 'x'}), 401)

    # Wrong password
    run_test("Wrong password", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'password': 'wrongpassword'}), 401)

    # Successful login
    ok, body = run_test("Login success", h, make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'password': TEST_PASSWORD}), 200)
    if ok:
        assert 'token' in body, "Response should contain JWT token"
        assert body.get('email') == TEST_EMAIL

    # Deactivated account test - deactivate user first
    dynamodb = boto3.resource('dynamodb')
    users_table = dynamodb.Table('remedi-users')
    users_table.update_item(
        Key={'email': TEST_EMAIL, 'record_type': 'PROFILE'},
        UpdateExpression='SET is_active = :val',
        ExpressionAttributeValues={':val': False}
    )
    run_test("Deactivated account", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'password': TEST_PASSWORD}), 401)

    # Reactivate for further tests
    users_table.update_item(
        Key={'email': TEST_EMAIL, 'record_type': 'PROFILE'},
        UpdateExpression='SET is_active = :val',
        ExpressionAttributeValues={':val': True}
    )


def test_users_userid_preferences_post(h):
    """Tests for POST /users/{userid}/preferences"""
    print("\n-- users_userid_preferences_post --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('POST', path_params={},
             body={'preferences': []}), 400)

    # Missing body
    run_test("Missing body", h, make_event('POST', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'POST', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'bad'
    }, 400)

    # preferences not an array
    run_test("preferences not an array", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': 'not-array'}), 400)

    # Empty preferences array
    run_test("Empty preferences array", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': []}), 400)

    # Missing preferences key
    run_test("Missing preferences key", h,
             make_event('POST', path_params={'userid': TEST_EMAIL}, body={'other': 'data'}), 400)

    # Invalid preference type
    run_test("Invalid preference type", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'INVALID', 'value': 'X'}]}), 400)

    # Missing preference value
    run_test("Missing preference value", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'DIET', 'value': ''}]}), 400)

    # Valid REASON type
    run_test("Create REASON preference", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'REASON', 'value': 'WEIGHT_LOSS'}]}), 201)

    # Valid ALLERGY type
    run_test("Create ALLERGY preference", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'ALLERGY', 'value': 'PEANUTS'}]}), 201)

    # Valid DIET type
    run_test("Create DIET preference", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'DIET', 'value': 'VEGAN'}]}), 201)

    # Multiple preferences at once
    run_test("Multiple preferences", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [
                            {'type': 'DIET', 'value': 'KETO'},
                            {'type': 'ALLERGY', 'value': 'GLUTEN'},
                            {'type': 'REASON', 'value': 'HEALTH'}
                        ]}), 201)

    # Preference with reference_value
    run_test("Preference with reference_value", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'DIET', 'value': 'PALEO',
                                               'reference_value': 'ref-123'}]}), 201)

    # Lowercase type should be uppercased
    run_test("Lowercase type normalized", h,
             make_event('POST', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'diet', 'value': 'vegan'}]}), 201)


def test_users_userid_preferences_get(h):
    """Tests for GET /users/{userid}/preferences"""
    print("\n-- users_userid_preferences_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={}), 400)

    # Get all preferences
    ok, body = run_test("Get all preferences", h,
                        make_event('GET', path_params={'userid': TEST_EMAIL}), 200)
    if ok:
        assert body.get('count', 0) > 0, "Should have preferences"

    # Filter by valid type
    run_test("Filter by DIET type", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'type': 'DIET'}), 200)

    # Filter by invalid type
    run_test("Invalid type filter", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'type': 'INVALID'}), 400)

    # No preferences for unknown user
    ok, body = run_test("No preferences for unknown user", h,
                        make_event('GET', path_params={'userid': 'nobody@test.com'}), 200)
    if ok:
        assert body.get('count') == 0

    # Null queryStringParameters
    run_test("Null queryStringParameters", h,
             {'httpMethod': 'GET', 'pathParameters': {'userid': TEST_EMAIL},
              'queryStringParameters': None}, 200)


def test_users_userid_preferences_put(h):
    """Tests for PUT /users/{userid}/preferences"""
    print("\n-- users_userid_preferences_put --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('PUT', path_params={},
             body={'preferences': []}), 400)

    # Missing body
    run_test("Missing body", h, make_event('PUT', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'PUT', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'bad'
    }, 400)

    # preferences not a list
    run_test("preferences not a list", h,
             make_event('PUT', path_params={'userid': TEST_EMAIL},
                        body={'preferences': 'not-list'}), 400)

    # Invalid type in preferences
    run_test("Invalid type in replace", h,
             make_event('PUT', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'WRONG', 'value': 'X'}]}), 400)

    # Missing value in preferences
    run_test("Missing value in replace", h,
             make_event('PUT', path_params={'userid': TEST_EMAIL},
                        body={'preferences': [{'type': 'DIET', 'value': ''}]}), 400)

    # Successful replace
    ok, body = run_test("Replace all preferences", h,
                        make_event('PUT', path_params={'userid': TEST_EMAIL},
                                   body={'preferences': [
                                       {'type': 'DIET', 'value': 'MEDITERRANEAN'},
                                       {'type': 'REASON', 'value': 'FITNESS'}
                                   ]}), 200)

    # Replace with empty list (deletes all, creates none)
    run_test("Replace with empty list", h,
             make_event('PUT', path_params={'userid': TEST_EMAIL},
                        body={'preferences': []}), 200)


def test_users_userid_activity_post(h):
    """Tests for POST /users/{userid}/activity"""
    print("\n-- users_userid_activity_post --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('POST', path_params={},
             body={'api_endpoint': '/test', 'http_method': 'GET'}), 400)

    # Missing body
    run_test("Missing body", h, make_event('POST', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'POST', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'bad'
    }, 400)

    # Missing api_endpoint
    run_test("Missing api_endpoint", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'http_method': 'GET'}), 400)

    # Missing http_method
    run_test("Missing http_method", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'api_endpoint': '/test'}), 400)

    # Success
    ok, body = run_test("Create activity success", h, make_event('POST',
                        path_params={'userid': TEST_EMAIL},
                        body={'api_endpoint': '/users', 'http_method': 'GET'}), 201)

    global created_activity_ts
    if ok:
        created_activity_ts = body.get('activity', {}).get('timestamp')
        assert created_activity_ts, "Should have timestamp"
        assert body['activity'].get('ttl_expiry'), "Should have TTL"

    # Success with optional fields
    run_test("Activity with optional fields", h, make_event('POST',
             path_params={'userid': TEST_EMAIL},
             body={'api_endpoint': '/recipes/search', 'http_method': 'POST',
                   'response_status': 200, 'session_id': 'sess-123',
                   'request_metadata': {'user_agent': 'test'}}), 201)

    # http_method should be uppercased
    ok2, body2 = run_test("http_method uppercased", h, make_event('POST',
                          path_params={'userid': TEST_EMAIL},
                          body={'api_endpoint': '/test', 'http_method': 'get'}), 201)
    if ok2:
        assert body2['activity']['http_method'] == 'GET'


def test_users_userid_activity_get(h):
    """Tests for GET /users/{userid}/activity"""
    print("\n-- users_userid_activity_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={}), 400)

    # Get all activities
    ok, body = run_test("Get all activities", h,
                        make_event('GET', path_params={'userid': TEST_EMAIL}), 200)
    if ok:
        assert body.get('count', 0) > 0

    # With date range
    run_test("With start and end date", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'start_date': '2026-01-01', 'end_date': '2026-12-31'}), 200)

    # With start_date only
    run_test("With start_date only", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'start_date': '2026-01-01'}), 200)

    # With end_date only
    run_test("With end_date only", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'end_date': '2026-12-31'}), 200)

    # With limit
    run_test("With limit=1", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': '1'}), 200)

    # Invalid limit (falls to default)
    run_test("Invalid limit", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': 'xyz'}), 200)

    # Limit = 0 (clamped to default)
    run_test("Limit = 0", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': '0'}), 200)

    # Limit > MAX (clamped)
    run_test("Limit > max", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': '9999'}), 200)

    # Empty results for unknown user
    ok, body = run_test("Empty for unknown user", h,
                        make_event('GET', path_params={'userid': 'nobody@test.com'}), 200)
    if ok:
        assert body.get('count') == 0

    # Null queryStringParameters
    run_test("Null queryStringParameters", h,
             {'httpMethod': 'GET', 'pathParameters': {'userid': TEST_EMAIL},
              'queryStringParameters': None}, 200)

    # ISO timestamp start_date
    run_test("ISO timestamp start_date", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'start_date': '2026-01-01T00:00:00+00:00'}), 200)


def test_users_userid_activity_activityid_get(h):
    """Tests for GET /users/{userid}/activity/{activityid}"""
    print("\n-- users_userid_activity_activityid_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={'activityid': 'x'}), 400)

    # Missing activityid
    run_test("Missing activityid", h, make_event('GET', path_params={'userid': TEST_EMAIL}), 400)

    # Not found
    run_test("Activity not found", h,
             make_event('GET', path_params={'userid': TEST_EMAIL, 'activityid': 'nonexistent'}), 404)

    # Success
    if created_activity_ts:
        run_test("Get activity success", h,
                 make_event('GET', path_params={'userid': TEST_EMAIL,
                            'activityid': created_activity_ts}), 200)


def test_users_userid_activity_activityid_delete(h):
    """Tests for DELETE /users/{userid}/activity/{activityid}"""
    print("\n-- users_userid_activity_activityid_delete --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('DELETE', path_params={'activityid': 'x'}), 400)

    # Missing activityid
    run_test("Missing activityid", h, make_event('DELETE', path_params={'userid': TEST_EMAIL}), 400)

    # Not found
    run_test("Activity not found", h,
             make_event('DELETE', path_params={'userid': TEST_EMAIL,
                        'activityid': 'nonexistent'}), 404)

    # Success - create one then delete it
    post_h = load_handler('lambdas.users_userid_activity_post')
    ok, body = run_test("Create temp activity", post_h,
                        make_event('POST', path_params={'userid': TEST_EMAIL},
                                   body={'api_endpoint': '/temp', 'http_method': 'DELETE'}), 201)
    if ok:
        ts = body['activity']['timestamp']
        run_test("Delete activity success", h,
                 make_event('DELETE', path_params={'userid': TEST_EMAIL, 'activityid': ts}), 200)


def test_users_userid_goals_post(h):
    """Tests for POST /users/{userid}/goals"""
    print("\n-- users_userid_goals_post --")

    # Missing pathParameters entirely
    run_test("Missing pathParameters", h, {'body': json.dumps({'title': 'T', 'target_days': 30})}, 400)

    # Missing userid in pathParameters
    run_test("Missing userid", h, {
        'pathParameters': {}, 'body': json.dumps({'title': 'T', 'target_days': 30})
    }, 400)

    # Invalid JSON
    run_test("Invalid JSON body", h, {
        'pathParameters': {'userid': TEST_EMAIL}, 'body': '{bad'
    }, 400)

    # Missing title
    run_test("Missing title", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'target_days': 30})
    }, 400)

    # Empty title
    run_test("Empty title", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': '', 'target_days': 30})
    }, 400)

    # Missing target_days
    run_test("Missing target_days", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Test Goal'})
    }, 400)

    # target_days = 0
    run_test("target_days = 0", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Goal', 'target_days': 0})
    }, 400)

    # target_days negative
    run_test("target_days negative", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Goal', 'target_days': -5})
    }, 400)

    # target_days not a number
    run_test("target_days not a number", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Goal', 'target_days': 'abc'})
    }, 400)

    # target_days as float string
    run_test("target_days float string", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Goal', 'target_days': '3.5'})
    }, 400)

    # Success
    global created_goal_id
    ok, body = run_test("Create goal success", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Run Daily', 'target_days': 30, 'description': 'Run every day'})
    }, 201)
    if ok:
        created_goal_id = body.get('goal_id')
        assert created_goal_id and created_goal_id.startswith('g-')
        assert body.get('status') == 'ACTIVE'
        assert body.get('completed_days') == 0

    # target_days = 1 (boundary)
    run_test("target_days = 1 boundary", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Min Goal', 'target_days': 1})
    }, 201)

    # Null body falls back to {}
    run_test("Null body", h, {
        'pathParameters': {'userid': TEST_EMAIL}, 'body': None
    }, 400)


def test_users_userid_goals_get(h):
    """Tests for GET /users/{userid}/goals"""
    print("\n-- users_userid_goals_get --")

    # Missing pathParameters
    run_test("Missing pathParameters", h, {}, 400)

    # Get all goals
    ok, body = run_test("Get all goals", h, {
        'pathParameters': {'userid': TEST_EMAIL}
    }, 200)
    if ok:
        assert body.get('count', 0) > 0

    # Filter by ACTIVE status
    run_test("Filter by ACTIVE status", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'queryStringParameters': {'status': 'ACTIVE'}
    }, 200)

    # Filter by COMPLETED status (should be empty)
    ok, body = run_test("Filter by COMPLETED", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'queryStringParameters': {'status': 'COMPLETED'}
    }, 200)
    if ok:
        assert body.get('count') == 0

    # Invalid status
    run_test("Invalid status filter", h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'queryStringParameters': {'status': 'INVALID'}
    }, 400)

    # Empty results for unknown user
    ok, body = run_test("No goals for unknown user", h, {
        'pathParameters': {'userid': 'nobody@test.com'}
    }, 200)
    if ok:
        assert body.get('count') == 0


def test_users_userid_goals_goalid_get(h):
    """Tests for GET /users/{userid}/goals/{goalid}"""
    print("\n-- users_userid_goals_goalid_get --")

    # Missing pathParameters
    run_test("Missing pathParameters", h, {}, 400)

    # Missing goalid
    run_test("Missing goalid", h, {'pathParameters': {'userid': TEST_EMAIL}}, 400)

    # Not found
    run_test("Goal not found", h, {
        'pathParameters': {'userid': TEST_EMAIL, 'goalid': 'g-nonexistent'}
    }, 404)

    # Success
    if created_goal_id:
        run_test("Get goal success", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id}
        }, 200)


def test_users_userid_goals_goalid_put(h):
    """Tests for PUT /users/{userid}/goals/{goalid}"""
    print("\n-- users_userid_goals_goalid_put --")

    # Missing pathParameters
    run_test("Missing pathParameters", h, {'body': json.dumps({'title': 'X'})}, 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id or 'g-x'},
        'body': '{bad'
    }, 400)

    # Not found
    run_test("Goal not found", h, {
        'pathParameters': {'userid': TEST_EMAIL, 'goalid': 'g-nonexistent'},
        'body': json.dumps({'title': 'X'})
    }, 404)

    if created_goal_id:
        # No updatable fields
        run_test("No updatable fields", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'email': 'x', 'random_field': 'y'})
        }, 400)

        # Empty body
        run_test("Empty body (no fields)", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({})
        }, 400)

        # Invalid target_days (not int)
        run_test("Invalid target_days string", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'target_days': 'abc'})
        }, 400)

        # target_days <= 0
        run_test("target_days = 0", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'target_days': 0})
        }, 400)

        run_test("target_days negative", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'target_days': -1})
        }, 400)

        # Invalid completed_days (negative)
        run_test("completed_days negative", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'completed_days': -1})
        }, 400)

        # Invalid completed_days (not int)
        run_test("completed_days not int", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'completed_days': 'abc'})
        }, 400)

        # Invalid status enum
        run_test("Invalid status", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'status': 'INVALID'})
        }, 400)

        # Invalid last_progress_date format
        run_test("Invalid last_progress_date", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'last_progress_date': 'not-a-date'})
        }, 400)

        # Valid last_progress_date
        run_test("Valid last_progress_date", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'last_progress_date': '2026-01-15'})
        }, 200)

        # last_progress_date = null (valid)
        run_test("last_progress_date null", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'last_progress_date': None})
        }, 200)

        # Update title
        run_test("Update title", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'title': 'Updated Title'})
        }, 200)

        # Update target_days (should recalculate end_date)
        ok, body = run_test("Update target_days recalc end_date", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'target_days': 60})
        }, 200)

        # Auto-completion: set completed_days >= target_days
        ok, body = run_test("Auto-complete goal", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'completed_days': 60})
        }, 200)
        if ok:
            assert body.get('status') == 'COMPLETED', "Should auto-complete"

        # completed_days = 0 (boundary)
        run_test("completed_days = 0", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': created_goal_id},
            'body': json.dumps({'completed_days': 0, 'status': 'ACTIVE'})
        }, 200)


def test_users_userid_goals_goalid_delete(h):
    """Tests for DELETE /users/{userid}/goals/{goalid}"""
    print("\n-- users_userid_goals_goalid_delete --")

    # Missing pathParameters
    run_test("Missing pathParameters", h, {}, 400)

    # Goal not found
    run_test("Goal not found", h, {
        'pathParameters': {'userid': TEST_EMAIL, 'goalid': 'g-nonexistent'}
    }, 404)

    # Success - create then delete
    post_h = load_handler('lambdas.users_userid_goals_post')
    ok, body = run_test("Create temp goal", post_h, {
        'pathParameters': {'userid': TEST_EMAIL},
        'body': json.dumps({'title': 'Temp Goal', 'target_days': 7})
    }, 201)
    if ok:
        temp_id = body['goal_id']
        run_test("Delete goal success", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': temp_id}
        }, 200)

        # Delete already deleted -> 404
        run_test("Delete already deleted", h, {
            'pathParameters': {'userid': TEST_EMAIL, 'goalid': temp_id}
        }, 404)


def test_users_userid_goals_delete(h):
    """Tests for DELETE /users/{userid}/goals (delete all)"""
    print("\n-- users_userid_goals_delete --")

    # Missing pathParameters
    run_test("Missing pathParameters", h, {}, 400)

    # No goals for unknown user (should still return 200)
    ok, body = run_test("No goals to delete", h, {
        'pathParameters': {'userid': 'nobody@test.com'}
    }, 200)
    if ok:
        assert body.get('deleted_count') == 0

    # Delete all goals for test user (has at least the created one)
    ok, body = run_test("Delete all goals", h, {
        'pathParameters': {'userid': TEST_EMAIL}
    }, 200)
    if ok:
        assert body.get('deleted_count', 0) > 0


def test_users_userid_rewards_post(h):
    """Tests for POST /users/{userid}/rewards"""
    print("\n-- users_userid_rewards_post --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('POST', path_params={},
             body={'badge_id': 'b1'}), 400)

    # Missing body
    run_test("Missing body", h, make_event('POST', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'POST', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'bad'
    }, 400)

    # Missing badge_id
    run_test("Missing badge_id", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'notes': 'test'}), 400)

    # Empty badge_id
    run_test("Empty badge_id", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'badge_id': ''}), 400)

    # Success
    ok, body = run_test("Create reward success", h, make_event('POST',
                        path_params={'userid': TEST_EMAIL},
                        body={'badge_id': 'goal_setter'}), 201)
    if ok:
        reward = body.get('reward', {})
        assert reward.get('date_reward_id')
        assert reward.get('badge_id') == 'goal_setter'

    # Success with optional fields
    run_test("Reward with optional fields", h, make_event('POST',
             path_params={'userid': TEST_EMAIL},
             body={'badge_id': 'streak_3', 'goal_id': 'g-123', 'notes': 'Great job!'}), 201)


def test_users_userid_rewards_get(h):
    """Tests for GET /users/{userid}/rewards"""
    print("\n-- users_userid_rewards_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={}), 400)

    # Get all rewards
    ok, body = run_test("Get all rewards", h,
                        make_event('GET', path_params={'userid': TEST_EMAIL}), 200)
    if ok:
        assert body.get('count', 0) > 0

    # With date range
    run_test("With date range", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'start_date': '2026-01-01', 'end_date': '2026-12-31'}), 200)

    # With start_date only
    run_test("With start_date only", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'start_date': '2026-01-01'}), 200)

    # With end_date only
    run_test("With end_date only", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'end_date': '2026-12-31'}), 200)

    # Invalid limit -> ValueError -> 400
    run_test("Invalid limit", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': 'xyz'}), 400)

    # Empty results for unknown user
    ok, body = run_test("No rewards for unknown", h,
                        make_event('GET', path_params={'userid': 'nobody@test.com'}), 200)
    if ok:
        assert body.get('count') == 0


def test_users_userid_alerts_post(h):
    """Tests for POST /users/{userid}/alerts"""
    print("\n-- users_userid_alerts_post --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('POST', path_params={},
             body={'condition': 'c', 'severity': 'LOW', 'title': 't', 'message': 'm'}), 400)

    # Missing body
    run_test("Missing body", h, make_event('POST', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'POST', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'bad'
    }, 400)

    # Missing all required fields
    run_test("Missing all fields", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={}), 400)

    # Missing individual fields
    run_test("Missing condition", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'severity': 'LOW', 'title': 't', 'message': 'm'}), 400)
    run_test("Missing severity", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'condition': 'c', 'title': 't', 'message': 'm'}), 400)
    run_test("Missing title", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'condition': 'c', 'severity': 'LOW', 'message': 'm'}), 400)
    run_test("Missing message", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'condition': 'c', 'severity': 'LOW', 'title': 't'}), 400)

    # Invalid severity
    run_test("Invalid severity", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'condition': 'c', 'severity': 'ULTRA', 'title': 't', 'message': 'm'}), 400)

    # Valid severities
    global created_alert_id
    for sev in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        ok, body = run_test(f"Create {sev} alert", h, make_event('POST',
                            path_params={'userid': TEST_EMAIL},
                            body={'condition': f'test_{sev}', 'severity': sev,
                                  'title': f'{sev} Alert', 'message': f'This is {sev}'}), 201)
        if ok and sev == 'LOW':
            created_alert_id = body['alert']['alert_date_id']

    # Lowercase severity should be uppercased
    run_test("Lowercase severity", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'condition': 'test', 'severity': 'high', 'title': 't', 'message': 'm'}), 201)


def test_users_userid_alerts_get(h):
    """Tests for GET /users/{userid}/alerts"""
    print("\n-- users_userid_alerts_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={}), 400)

    # Get all alerts
    ok, body = run_test("Get all alerts", h,
                        make_event('GET', path_params={'userid': TEST_EMAIL}), 200)
    if ok:
        assert body.get('count', 0) > 0

    # Filter by condition
    run_test("Filter by condition", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'condition': 'test_LOW'}), 200)

    # Filter by date
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    run_test("Filter by date", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'date': today}), 200)

    # Invalid limit
    run_test("Invalid limit", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': 'bad'}), 400)

    # Empty for unknown user
    ok, body = run_test("No alerts for unknown", h,
                        make_event('GET', path_params={'userid': 'nobody@test.com'}), 200)
    if ok:
        assert body.get('count') == 0


def test_users_userid_alerts_alertid_get(h):
    """Tests for GET /users/{userid}/alerts/{alertid}"""
    print("\n-- users_userid_alerts_alertid_get --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={'alertid': 'x'}), 400)

    # Missing alertid
    run_test("Missing alertid", h, make_event('GET', path_params={'userid': TEST_EMAIL}), 400)

    # Not found
    run_test("Alert not found", h,
             make_event('GET', path_params={'userid': TEST_EMAIL, 'alertid': 'nonexistent'}), 404)

    # Success
    if created_alert_id:
        run_test("Get alert success", h,
                 make_event('GET', path_params={'userid': TEST_EMAIL,
                            'alertid': created_alert_id}), 200)


def test_users_userid_alerts_alertid_put(h):
    """Tests for PUT /users/{userid}/alerts/{alertid}"""
    print("\n-- users_userid_alerts_alertid_put --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('PUT', path_params={'alertid': 'x'},
             body={'is_acknowledged': True}), 400)

    # Missing alertid
    run_test("Missing alertid", h, make_event('PUT', path_params={'userid': TEST_EMAIL},
             body={'is_acknowledged': True}), 400)

    # Missing body
    run_test("Missing body", h, make_event('PUT', path_params={'userid': TEST_EMAIL,
             'alertid': created_alert_id or 'x'}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'PUT',
        'pathParameters': {'userid': TEST_EMAIL, 'alertid': created_alert_id or 'x'},
        'body': '{bad'
    }, 400)

    # Alert not found
    run_test("Alert not found", h, make_event('PUT', path_params={
        'userid': TEST_EMAIL, 'alertid': 'nonexistent'},
        body={'is_acknowledged': True}), 404)

    if created_alert_id:
        # No valid fields
        run_test("No valid fields", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'random': 'field'}), 400)

        # is_acknowledged not boolean
        run_test("is_acknowledged not bool", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'is_acknowledged': 'yes'}), 400)

        run_test("is_acknowledged as int", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'is_acknowledged': 1}), 400)

        # Invalid severity
        run_test("Invalid severity", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'severity': 'ULTRA'}), 400)

        # Acknowledge alert (should set acknowledged_at)
        ok, body = run_test("Acknowledge alert", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'is_acknowledged': True}), 200)
        if ok:
            alert = body.get('alert', {})
            assert alert.get('is_acknowledged') is True
            assert alert.get('acknowledged_at'), "Should set acknowledged_at"

        # Update severity
        run_test("Update severity", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'severity': 'CRITICAL'}), 200)

        # Update both fields at once
        run_test("Update both fields", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'is_acknowledged': False, 'severity': 'MEDIUM'}), 200)

        # Lowercase severity should be uppercased
        run_test("Lowercase severity uppercased", h, make_event('PUT', path_params={
            'userid': TEST_EMAIL, 'alertid': created_alert_id},
            body={'severity': 'low'}), 200)


def test_users_userid_alerts_alertid_delete(h):
    """Tests for DELETE /users/{userid}/alerts/{alertid}"""
    print("\n-- users_userid_alerts_alertid_delete --")

    # OPTIONS
    run_test("OPTIONS preflight", h, make_event('OPTIONS'), 200)

    # Missing userid
    run_test("Missing userid", h, make_event('DELETE', path_params={'alertid': 'x'}), 400)

    # Missing alertid
    run_test("Missing alertid", h, make_event('DELETE', path_params={'userid': TEST_EMAIL}), 400)

    # Not found
    run_test("Alert not found", h, make_event('DELETE', path_params={
        'userid': TEST_EMAIL, 'alertid': 'nonexistent'}), 404)

    # Success - create then delete
    post_h = load_handler('lambdas.users_userid_alerts_post')
    ok, body = run_test("Create temp alert", post_h, make_event('POST',
                        path_params={'userid': TEST_EMAIL},
                        body={'condition': 'temp', 'severity': 'LOW',
                              'title': 'Temp', 'message': 'Temp msg'}), 201)
    if ok:
        temp_id = body['alert']['alert_date_id']
        run_test("Delete alert success", h, make_event('DELETE', path_params={
            'userid': TEST_EMAIL, 'alertid': temp_id}), 200)


def test_users_userid_notifications_post(h):
    """Tests for POST /users/{userid}/notifications"""
    print("\n-- users_userid_notifications_post --")

    # Missing userid
    run_test("Missing userid", h, make_event('POST', path_params={},
             body={'type': 'INFO', 'title': 't', 'message_text': 'm'}), 400)

    # Missing body
    run_test("Missing body", h, make_event('POST', path_params={'userid': TEST_EMAIL}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'POST', 'pathParameters': {'userid': TEST_EMAIL}, 'body': 'bad'
    }, 400)

    # Missing type
    run_test("Missing type", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'title': 't', 'message_text': 'm'}), 400)

    # Missing title
    run_test("Missing title", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'type': 'INFO', 'message_text': 'm'}), 400)

    # Missing message_text
    run_test("Missing message_text", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'type': 'INFO', 'title': 't'}), 400)

    # Empty required fields
    run_test("Empty type", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'type': '', 'title': 't', 'message_text': 'm'}), 400)
    run_test("Empty title", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'type': 'INFO', 'title': '', 'message_text': 'm'}), 400)
    run_test("Empty message_text", h, make_event('POST', path_params={'userid': TEST_EMAIL},
             body={'type': 'INFO', 'title': 't', 'message_text': ''}), 400)

    # Success
    global created_notification_ts
    ok, body = run_test("Create notification success", h, make_event('POST',
                        path_params={'userid': TEST_EMAIL},
                        body={'type': 'INFO', 'title': 'Test Notification',
                              'message_text': 'Hello World'}), 201)
    if ok:
        notif = body.get('notification', {})
        created_notification_ts = notif.get('created_at')
        assert notif.get('is_read') is False
        assert notif.get('read_status_created_at', '').startswith('UNREAD#')
        assert notif.get('ttl_expiry')

    # With optional related_entity_id
    run_test("With related_entity_id", h, make_event('POST',
             path_params={'userid': TEST_EMAIL},
             body={'type': 'ALERT', 'title': 'Related', 'message_text': 'Msg',
                   'related_entity_id': 'goal-123'}), 201)

    # Small sleep to ensure different created_at timestamps
    time.sleep(0.01)

    # Create another for list tests
    run_test("Create second notification", h, make_event('POST',
             path_params={'userid': TEST_EMAIL},
             body={'type': 'REMINDER', 'title': 'Second', 'message_text': 'Another'}), 201)


def test_users_userid_notifications_get(h):
    """Tests for GET /users/{userid}/notifications"""
    print("\n-- users_userid_notifications_get --")

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={}), 400)

    # Get all notifications
    ok, body = run_test("Get all notifications", h,
                        make_event('GET', path_params={'userid': TEST_EMAIL}), 200)
    if ok:
        assert body.get('count', 0) > 0

    # Filter unread only
    run_test("Unread only", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'unread_only': 'true'}), 200)

    # unread_only=false (same as no filter)
    run_test("unread_only false", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'unread_only': 'false'}), 200)

    # With limit
    run_test("With limit=1", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': '1'}), 200)

    # Invalid limit (falls to default)
    run_test("Invalid limit", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': 'abc'}), 200)

    # Limit = 0 (clamped)
    run_test("Limit = 0", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': '0'}), 200)

    # Limit > 200 (clamped)
    run_test("Limit > 200", h,
             make_event('GET', path_params={'userid': TEST_EMAIL},
                        query_params={'limit': '999'}), 200)

    # Empty for unknown user
    ok, body = run_test("No notifications for unknown", h,
                        make_event('GET', path_params={'userid': 'nobody@test.com'}), 200)
    if ok:
        assert body.get('count') == 0


def test_users_userid_notifications_notificationid_get(h):
    """Tests for GET /users/{userid}/notifications/{notificationid}"""
    print("\n-- users_userid_notifications_notificationid_get --")

    # Missing userid
    run_test("Missing userid", h, make_event('GET', path_params={'notificationid': 'x'}), 400)

    # Missing notificationid
    run_test("Missing notificationid", h, make_event('GET', path_params={'userid': TEST_EMAIL}), 400)

    # Not found
    run_test("Not found", h,
             make_event('GET', path_params={'userid': TEST_EMAIL,
                        'notificationid': 'nonexistent'}), 404)

    # Success
    if created_notification_ts:
        run_test("Get notification success", h,
                 make_event('GET', path_params={'userid': TEST_EMAIL,
                            'notificationid': created_notification_ts}), 200)


def test_users_userid_notifications_notificationid_delete(h):
    """Tests for DELETE /users/{userid}/notifications/{notificationid}"""
    print("\n-- users_userid_notifications_notificationid_delete --")

    # Missing userid
    run_test("Missing userid", h, make_event('DELETE', path_params={'notificationid': 'x'}), 400)

    # Missing notificationid
    run_test("Missing notificationid", h, make_event('DELETE', path_params={'userid': TEST_EMAIL}), 400)

    # Delete nonexistent (succeeds silently - DynamoDB behavior)
    run_test("Delete nonexistent (silent)", h,
             make_event('DELETE', path_params={'userid': TEST_EMAIL,
                        'notificationid': 'nonexistent'}), 200)

    # Success
    if created_notification_ts:
        run_test("Delete notification success", h,
                 make_event('DELETE', path_params={'userid': TEST_EMAIL,
                            'notificationid': created_notification_ts}), 200)


def test_recipes_search_post(h):
    """Tests for POST /recipes/search"""
    print("\n-- recipes_search_post --")

    # Invalid JSON
    run_test("Invalid JSON", h, {'body': 'not-json'}, 400)

    # No body (returns all META)
    ok, body = run_test("No body - returns all", h, {}, 200)
    if ok:
        assert body.get('count', 0) > 0

    # Empty body
    run_test("Empty body dict", h, {'body': json.dumps({})}, 200)

    # Null body
    run_test("Null body", h, {'body': None}, 200)

    # By meal_type
    ok, body = run_test("Search by meal_type BREAKFAST", h,
                        {'body': json.dumps({'meal_type': 'BREAKFAST'})}, 200)
    if ok:
        assert body.get('count', 0) > 0

    # By meal_type with no results
    ok, body = run_test("Search by meal_type SNACK (no results)", h,
                        {'body': json.dumps({'meal_type': 'SNACK'})}, 200)
    if ok:
        assert body.get('count') == 0

    # By cuisine_type
    run_test("Search by cuisine_type", h,
             {'body': json.dumps({'cuisine_type': 'ITALIAN'})}, 200)

    # By difficulty_level
    run_test("Search by difficulty_level", h,
             {'body': json.dumps({'difficulty_level': 'EASY'})}, 200)

    # By diet_tags
    ok, body = run_test("Search by diet_tags VEGAN", h,
                        {'body': json.dumps({'diet_tags': ['VEGAN']})}, 200)
    if ok:
        assert body.get('count', 0) > 0

    # By diet_tags with empty list (falls through to scan)
    run_test("Empty diet_tags", h,
             {'body': json.dumps({'diet_tags': []})}, 200)

    # With exclude_allergens
    ok, body = run_test("Exclude GLUTEN allergen", h,
                        {'body': json.dumps({'exclude_allergens': ['GLUTEN']})}, 200)

    # With max_calories
    ok, body = run_test("Max calories 300", h,
                        {'body': json.dumps({'max_calories': 300})}, 200)
    if ok:
        for recipe in body.get('recipes', []):
            cal = recipe.get('calories_per_serving')
            if cal is not None:
                assert float(cal) <= 300

    # Invalid max_calories (ignored, not error)
    run_test("Invalid max_calories", h,
             {'body': json.dumps({'max_calories': 'bad'})}, 200)

    # With limit
    run_test("With limit=1", h,
             {'body': json.dumps({'limit': 1})}, 200)

    # Invalid limit (falls to default)
    run_test("Invalid limit", h,
             {'body': json.dumps({'limit': 'bad'})}, 200)

    # Limit boundaries
    run_test("Limit = 0 (clamped)", h,
             {'body': json.dumps({'limit': 0})}, 200)
    run_test("Limit > 100 (clamped)", h,
             {'body': json.dumps({'limit': 999})}, 200)

    # Body as dict
    run_test("Body as dict", h, {'body': {'meal_type': 'BREAKFAST'}}, 200)


def test_recipes_scan_post(h):
    """Tests for POST /recipes/scan"""
    print("\n-- recipes_scan_post --")

    # Invalid JSON
    run_test("Invalid JSON", h, {'body': 'bad'}, 400)

    # No body (default results)
    ok, body = run_test("No body - default", h, {}, 200)
    if ok:
        assert body.get('analysis_method') == 'default'

    # Null body
    run_test("Null body", h, {'body': None}, 200)

    # Empty body
    run_test("Empty body", h, {'body': json.dumps({})}, 200)

    # Text description search
    ok, body = run_test("Text search - smoothie", h,
                        {'body': json.dumps({'text_description': 'green smoothie'})}, 200)
    if ok:
        assert body.get('analysis_method') == 'text_search'
        assert body.get('count', 0) > 0

    # Text search with no matches
    ok, body = run_test("Text search - no matches", h,
                        {'body': json.dumps({'text_description': 'xyznonexistent'})}, 200)
    if ok:
        assert body.get('count') == 0

    # Image analysis (placeholder)
    ok, body = run_test("Image analysis placeholder", h,
                        {'body': json.dumps({'image_base64': 'base64data'})}, 200)
    if ok:
        assert body.get('analysis_method') == 'image_analysis'

    # Nutrient filter
    ok, body = run_test("Nutrient filter - protein min", h,
                        {'body': json.dumps({'nutrients': [{'name': 'protein_g', 'min': 5}]})}, 200)
    if ok:
        assert body.get('analysis_method') == 'nutrient_filter'

    # Nutrient filter with max
    run_test("Nutrient filter with max", h,
             {'body': json.dumps({'nutrients': [{'name': 'calories_per_serving', 'max': 300}]})}, 200)

    # Nutrient filter with min and max
    run_test("Nutrient filter min+max", h,
             {'body': json.dumps({'nutrients': [
                 {'name': 'protein_g', 'min': 5, 'max': 50}
             ]})}, 200)

    # Nutrient filter with nonexistent nutrient name
    ok, body = run_test("Nutrient filter - unknown nutrient", h,
                        {'body': json.dumps({'nutrients': [{'name': 'nonexistent_nutrient', 'min': 1}]})}, 200)
    if ok:
        assert body.get('count') == 0

    # Nutrient filter with empty nutrients list (falls to default)
    run_test("Empty nutrients list", h,
             {'body': json.dumps({'nutrients': []})}, 200)

    # Multiple nutrients
    run_test("Multiple nutrients", h,
             {'body': json.dumps({'nutrients': [
                 {'name': 'protein_g', 'min': 5},
                 {'name': 'fat_g', 'max': 20}
             ]})}, 200)


def test_refvalue_post(h):
    """Tests for POST /refvalue"""
    print("\n-- refvalue_post --")

    # Missing body
    run_test("Missing body", h, make_event('POST'), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {'httpMethod': 'POST', 'body': 'bad'}, 400)

    # Missing reference_type
    run_test("Missing reference_type", h, make_event('POST', body={
        'reference_id': 'r1', 'reference_value': 'v1'}), 400)

    # Missing reference_id
    run_test("Missing reference_id", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_value': 'v1'}), 400)

    # Missing reference_value
    run_test("Missing reference_value", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_id': 'r1'}), 400)

    # Success
    run_test("Create refvalue success", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_id': 'VEGAN',
        'reference_value': 'Vegan Diet'}), 201)

    # Duplicate
    run_test("Duplicate refvalue", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_id': 'VEGAN',
        'reference_value': 'Different'}), 409)

    # With optional description
    run_test("With description", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_id': 'KETO',
        'reference_value': 'Keto Diet', 'description': 'Low carb diet'}), 201)

    # With sort_order
    run_test("With sort_order", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_id': 'PALEO',
        'reference_value': 'Paleo Diet', 'sort_order': 3}), 201)

    # Invalid sort_order
    run_test("Invalid sort_order", h, make_event('POST', body={
        'reference_type': 'DIET', 'reference_id': 'BAD',
        'reference_value': 'Bad', 'sort_order': 'not-int'}), 400)

    # With metadata as object
    run_test("With metadata object", h, make_event('POST', body={
        'reference_type': 'ALLERGY', 'reference_id': 'PEANUTS',
        'reference_value': 'Peanut Allergy', 'metadata': {'severity': 'high'}}), 201)

    # Invalid metadata (not an object)
    run_test("Invalid metadata", h, make_event('POST', body={
        'reference_type': 'ALLERGY', 'reference_id': 'BAD2',
        'reference_value': 'Bad', 'metadata': 'not-object'}), 400)

    # With is_active=False
    run_test("With is_active=False", h, make_event('POST', body={
        'reference_type': 'REASON', 'reference_id': 'INACTIVE',
        'reference_value': 'Inactive', 'is_active': False}), 201)

    # Create another for listing tests
    run_test("Create REASON ref", h, make_event('POST', body={
        'reference_type': 'REASON', 'reference_id': 'WEIGHT_LOSS',
        'reference_value': 'Weight Loss', 'is_active': True, 'sort_order': 1}), 201)


def test_refvalue_get(h):
    """Tests for GET /refvalue"""
    print("\n-- refvalue_get --")

    # Get all
    ok, body = run_test("Get all refvalues", h, make_event('GET'), 200)
    if ok:
        assert body.get('count', 0) > 0

    # Filter by type
    ok, body = run_test("Filter by DIET type", h,
                        make_event('GET', query_params={'type': 'DIET'}), 200)
    if ok:
        assert body.get('count', 0) > 0

    # Filter by active_only
    run_test("Active only", h,
             make_event('GET', query_params={'active_only': 'true'}), 200)

    # Combined type + active_only
    run_test("Type + active_only", h,
             make_event('GET', query_params={'type': 'DIET', 'active_only': 'true'}), 200)

    # active_only=false (same as no filter)
    run_test("active_only false", h,
             make_event('GET', query_params={'active_only': 'false'}), 200)

    # No results for unknown type
    ok, body = run_test("Unknown type empty", h,
                        make_event('GET', query_params={'type': 'NONEXISTENT'}), 200)
    if ok:
        assert body.get('count') == 0

    # Null queryStringParameters
    run_test("Null queryStringParameters", h,
             {'httpMethod': 'GET', 'queryStringParameters': None}, 200)


def test_refvalue_refvalueid_get(h):
    """Tests for GET /refvalue/{refvalueid}"""
    print("\n-- refvalue_refvalueid_get --")

    # Missing refvalueid
    run_test("Missing refvalueid", h, make_event('GET', path_params={}), 400)

    # Invalid format (no #)
    run_test("Invalid format - no hash", h,
             make_event('GET', path_params={'refvalueid': 'nohash'}), 400)

    # Invalid format (empty parts)
    run_test("Invalid format - empty left", h,
             make_event('GET', path_params={'refvalueid': '#VEGAN'}), 400)

    run_test("Invalid format - empty right", h,
             make_event('GET', path_params={'refvalueid': 'DIET#'}), 400)

    # Not found
    run_test("Not found", h,
             make_event('GET', path_params={'refvalueid': 'NONEXISTENT#NOPE'}), 404)

    # Success
    run_test("Get refvalue success", h,
             make_event('GET', path_params={'refvalueid': 'DIET#VEGAN'}), 200)


def test_refvalue_refvalueid_put(h):
    """Tests for PUT /refvalue/{refvalueid}"""
    print("\n-- refvalue_refvalueid_put --")

    # Missing refvalueid
    run_test("Missing refvalueid", h, make_event('PUT', path_params={},
             body={'reference_value': 'x'}), 400)

    # Invalid format
    run_test("Invalid format", h, make_event('PUT', path_params={'refvalueid': 'nohash'},
             body={'reference_value': 'x'}), 400)

    # Not found
    run_test("Not found", h, make_event('PUT', path_params={'refvalueid': 'NONEXISTENT#NOPE'},
             body={'reference_value': 'x'}), 404)

    # Missing body
    run_test("Missing body", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'}), 400)

    # Invalid JSON
    run_test("Invalid JSON", h, {
        'httpMethod': 'PUT', 'pathParameters': {'refvalueid': 'DIET#VEGAN'}, 'body': 'bad'
    }, 400)

    # No updatable fields
    run_test("No updatable fields", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'random_field': 'x'}), 400)

    # Invalid sort_order
    run_test("Invalid sort_order", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'sort_order': 'bad'}), 400)

    # Invalid metadata
    run_test("Invalid metadata", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'metadata': 'not-dict'}), 400)

    # Invalid is_active
    run_test("Invalid is_active", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'is_active': 'yes'}), 400)

    run_test("is_active as int", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'is_active': 1}), 400)

    # Success - update reference_value
    run_test("Update reference_value", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'reference_value': 'Updated Vegan Diet'}), 200)

    # Update description
    run_test("Update description", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'description': 'A plant-based diet'}), 200)

    # Update is_active
    run_test("Update is_active", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'is_active': False}), 200)

    # Update sort_order
    run_test("Update sort_order", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'sort_order': 5}), 200)

    # Update metadata
    run_test("Update metadata", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'metadata': {'category': 'plant_based'}}), 200)

    # Null sort_order (valid)
    run_test("Null sort_order", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'sort_order': None}), 200)

    # Null metadata (valid)
    run_test("Null metadata", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'metadata': None}), 200)

    # Multiple fields at once
    run_test("Multiple fields", h, make_event('PUT', path_params={'refvalueid': 'DIET#VEGAN'},
             body={'reference_value': 'V2', 'description': 'D2', 'is_active': True}), 200)


def test_refvalue_refvalueid_delete(h):
    """Tests for DELETE /refvalue/{refvalueid}"""
    print("\n-- refvalue_refvalueid_delete --")

    # Missing refvalueid
    run_test("Missing refvalueid", h, make_event('DELETE', path_params={}), 400)

    # Invalid format
    run_test("Invalid format", h,
             make_event('DELETE', path_params={'refvalueid': 'nohash'}), 400)

    # Delete nonexistent (succeeds silently - DynamoDB behavior)
    run_test("Delete nonexistent (silent)", h,
             make_event('DELETE', path_params={'refvalueid': 'NONEXISTENT#NOPE'}), 200)

    # Create one then delete it
    post_h = load_handler('lambdas.refvalue_post')
    post_h(make_event('POST', body={
        'reference_type': 'TEMP', 'reference_id': 'DEL_ME',
        'reference_value': 'Temporary'}), None)

    run_test("Delete refvalue success", h,
             make_event('DELETE', path_params={'refvalueid': 'TEMP#DEL_ME'}), 200)


# ======================================================================════
#  M A I N   R U N N E R
# ======================================================================════

@mock_aws
def main():
    global PASS_COUNT, FAIL_COUNT, FAILURES
    global created_activity_ts, created_goal_id, created_alert_id, created_notification_ts

    PASS_COUNT = 0
    FAIL_COUNT = 0
    FAILURES = []
    created_activity_ts = None
    created_goal_id = None
    created_alert_id = None
    created_notification_ts = None

    # -- Setup --------------------------------------------------------------
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    create_all_tables(dynamodb)
    seed_recipes(dynamodb)

    # Make sure lambdas dir is on path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lambdas'))
    lambdas_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lambdas')
    if lambdas_dir not in sys.path:
        sys.path.insert(0, lambdas_dir)

    print("=" * 70)
    print("  COMPREHENSIVE LAMBDA TEST SUITE")
    print("=" * 70)

    # -- Users --------------------------------------------------------------
    test_users_post(load_handler('lambdas.users_post'))
    test_users_get(load_handler('lambdas.users_get'))
    test_users_userid_get(load_handler('lambdas.users_userid_get'))
    test_users_userid_put(load_handler('lambdas.users_userid_put'))
    test_users_userid_login_post(load_handler('lambdas.users_userid_login_post'))

    # -- Preferences --------------------------------------------------------
    test_users_userid_preferences_post(load_handler('lambdas.users_userid_preferences_post'))
    test_users_userid_preferences_get(load_handler('lambdas.users_userid_preferences_get'))
    test_users_userid_preferences_put(load_handler('lambdas.users_userid_preferences_put'))

    # -- Activity -----------------------------------------------------------
    test_users_userid_activity_post(load_handler('lambdas.users_userid_activity_post'))
    test_users_userid_activity_get(load_handler('lambdas.users_userid_activity_get'))
    test_users_userid_activity_activityid_get(load_handler('lambdas.users_userid_activity_activityid_get'))
    test_users_userid_activity_activityid_delete(load_handler('lambdas.users_userid_activity_activityid_delete'))

    # -- Goals --------------------------------------------------------------
    test_users_userid_goals_post(load_handler('lambdas.users_userid_goals_post'))
    test_users_userid_goals_get(load_handler('lambdas.users_userid_goals_get'))
    test_users_userid_goals_goalid_get(load_handler('lambdas.users_userid_goals_goalid_get'))
    test_users_userid_goals_goalid_put(load_handler('lambdas.users_userid_goals_goalid_put'))
    test_users_userid_goals_goalid_delete(load_handler('lambdas.users_userid_goals_goalid_delete'))
    test_users_userid_goals_delete(load_handler('lambdas.users_userid_goals_delete'))

    # -- Rewards ------------------------------------------------------------
    test_users_userid_rewards_post(load_handler('lambdas.users_userid_rewards_post'))
    test_users_userid_rewards_get(load_handler('lambdas.users_userid_rewards_get'))

    # -- Alerts -------------------------------------------------------------
    test_users_userid_alerts_post(load_handler('lambdas.users_userid_alerts_post'))
    test_users_userid_alerts_get(load_handler('lambdas.users_userid_alerts_get'))
    test_users_userid_alerts_alertid_get(load_handler('lambdas.users_userid_alerts_alertid_get'))
    test_users_userid_alerts_alertid_put(load_handler('lambdas.users_userid_alerts_alertid_put'))
    test_users_userid_alerts_alertid_delete(load_handler('lambdas.users_userid_alerts_alertid_delete'))

    # -- Notifications ------------------------------------------------------
    test_users_userid_notifications_post(load_handler('lambdas.users_userid_notifications_post'))
    test_users_userid_notifications_get(load_handler('lambdas.users_userid_notifications_get'))
    test_users_userid_notifications_notificationid_get(load_handler('lambdas.users_userid_notifications_notificationid_get'))
    test_users_userid_notifications_notificationid_delete(load_handler('lambdas.users_userid_notifications_notificationid_delete'))

    # -- Recipes ------------------------------------------------------------
    test_recipes_search_post(load_handler('lambdas.recipes_search_post'))
    test_recipes_scan_post(load_handler('lambdas.recipes_scan_post'))

    # -- Reference Values ---------------------------------------------------
    test_refvalue_post(load_handler('lambdas.refvalue_post'))
    test_refvalue_get(load_handler('lambdas.refvalue_get'))
    test_refvalue_refvalueid_get(load_handler('lambdas.refvalue_refvalueid_get'))
    test_refvalue_refvalueid_put(load_handler('lambdas.refvalue_refvalueid_put'))
    test_refvalue_refvalueid_delete(load_handler('lambdas.refvalue_refvalueid_delete'))

    # -- Delete user last (cleans up) --------------------------------------
    test_users_userid_delete(load_handler('lambdas.users_userid_delete'))

    # -- Summary ------------------------------------------------------------
    total = PASS_COUNT + FAIL_COUNT
    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {PASS_COUNT}/{total} passed, {FAIL_COUNT} failed")
    print(f"{'=' * 70}")

    if FAILURES:
        print("\nFailed tests:")
        for name, reason in FAILURES:
            print(f"  - {name}: {reason}")

    return FAIL_COUNT == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
