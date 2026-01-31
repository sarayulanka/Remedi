import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

table_name = os.getenv('DYNAMODB_TABLE_NAME', 'nutrition-users')

def create_table_if_not_exists():
    """Create the DynamoDB table if it doesn't exist"""
    try:
        # Try to describe the table
        dynamodb.meta.client.describe_table(TableName=table_name)
        print(f"Table {table_name} already exists")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            # Table doesn't exist, create it
            print(f"Creating table {table_name}...")
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'userId',
                        'KeyType': 'HASH'  # Partition key
                    },
                    {
                        'AttributeName': 'dataType',
                        'KeyType': 'RANGE'  # Sort key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'userId',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'dataType',
                        'AttributeType': 'S'
                    },
                    {
                        'AttributeName': 'username',
                        'AttributeType': 'S'
                    }
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'username-index',
                        'KeySchema': [
                            {
                                'AttributeName': 'username',
                                'KeyType': 'HASH'
                            }
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
            print(f"Table {table_name} created successfully")
            return True
        else:
            print(f"Error checking/creating table: {e}")
            return False

def _clean_item(item):
    """Recursively convert floats to Decimal and strip None values for DynamoDB."""
    cleaned = {}
    for k, v in item.items():
        if v is None:
            continue
        if isinstance(v, float):
            cleaned[k] = Decimal(str(v))
        elif isinstance(v, dict):
            cleaned[k] = _clean_item(v)
        elif isinstance(v, list):
            cleaned[k] = [
                _clean_item(i) if isinstance(i, dict)
                else Decimal(str(i)) if isinstance(i, float)
                else i
                for i in v if i is not None
            ]
        else:
            cleaned[k] = v
    return cleaned


class _SafeTable:
    """Wrapper around DynamoDB Table that auto-cleans items on put_item.
    Converts Python floats to Decimal and strips None values so every
    write across the entire app is safe."""

    def __init__(self, table):
        self._table = table

    def put_item(self, **kwargs):
        if 'Item' in kwargs:
            kwargs['Item'] = _clean_item(kwargs['Item'])
        return self._table.put_item(**kwargs)

    def __getattr__(self, name):
        return getattr(self._table, name)


def get_table():
    """Get the DynamoDB table wrapped with automatic type safety."""
    return _SafeTable(dynamodb.Table(table_name))

# Data type constants for the sort key
DATA_TYPE_PROFILE = "PROFILE"
DATA_TYPE_STREAK = "STREAK"
DATA_TYPE_BADGE = "BADGE"
DATA_TYPE_SAVED_REMEDY = "SAVED_REMEDY"
DATA_TYPE_GOAL = "GOAL"
DATA_TYPE_DIETARY_PREFS = "DIETARY_PREFS"
DATA_TYPE_FREEZE_LOG = "FREEZE"
DATA_TYPE_XP = "XP"
DATA_TYPE_CHALLENGE = "CHALLENGE"
