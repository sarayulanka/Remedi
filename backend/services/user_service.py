from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)
from botocore.exceptions import ClientError
from database import get_table, DATA_TYPE_PROFILE, DATA_TYPE_DIETARY_PREFS, DATA_TYPE_STREAK
from auth import hash_password, verify_password, create_access_token
from models import UserSignup, UserLogin, TokenResponse, UserProfile, DietaryPreferences, Streak
from fastapi import HTTPException, status

class UserService:
    def __init__(self):
        self.table = get_table()
    
    def signup(self, user_data: UserSignup) -> TokenResponse:
        """Register a new user"""
        logger.debug(f"Signup attempt for username: {user_data.username}")

        # Check if username already exists
        try:
            response = self.table.query(
                IndexName='username-index',
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={
                    ':username': user_data.username
                }
            )
            
            if response['Items']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error: {str(e)}"
                )
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Store user profile
        try:
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': DATA_TYPE_PROFILE,
                    'username': user_data.username,
                    'email': user_data.email,
                    'password': hashed_password,
                    'fullName': user_data.fullName or '',
                    'age': user_data.age or 0,
                    'gender': user_data.gender or '',
                    'location': user_data.location or '',
                    'nutritionGoals': user_data.nutritionGoals or [],
                    'healthConditions': user_data.healthConditions or [],
                    'allergies': user_data.allergies or [],
                    'dietType': user_data.dietType or '',
                    'createdAt': timestamp,
                    'updatedAt': timestamp
                }
            )
            
            # Streak record is created on first gamification access
            # via _ensure_streak_exists() with all required fields.

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user_id, "username": user_data.username}
        )
        
        return TokenResponse(
            access_token=access_token,
            userId=user_id,
            username=user_data.username
        )
    
    def login(self, login_data: UserLogin) -> TokenResponse:
        """Authenticate a user"""
        try:
            # Find user by username
            logger.debug(f"Login attempt for username: {login_data.username}")
            response = self.table.query(
                IndexName='username-index',
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={
                    ':username': login_data.username
                }
            )

            if not response['Items']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            # Find the profile item
            user_items = [item for item in response['Items'] if item['dataType'] == DATA_TYPE_PROFILE]

            if not user_items:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            user = user_items[0]

            # Verify password
            try:
                password_valid = verify_password(login_data.password, user['password'])
            except Exception as pw_error:
                logger.error(f"Password verification error: {str(pw_error)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            if not password_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password"
                )

            # Create access token
            access_token = create_access_token(
                data={"sub": user['userId'], "username": user['username']}
            )

            logger.debug(f"Login successful for user: {user['userId']}")
            return TokenResponse(
                access_token=access_token,
                userId=user['userId'],
                username=user['username']
            )

        except HTTPException:
            raise
        except ClientError as e:
            logger.error(f"Database error during login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Login error occurred"
            )
    
    def get_profile(self, user_id: str) -> UserProfile:
        """Get user profile"""
        try:
            response = self.table.get_item(
                Key={
                    'userId': user_id,
                    'dataType': DATA_TYPE_PROFILE
                }
            )
            
            if 'Item' not in response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user = response['Item']
            
            # Get dietary preferences if they exist
            dietary_prefs = None
            try:
                prefs_response = self.table.get_item(
                    Key={
                        'userId': user_id,
                        'dataType': DATA_TYPE_DIETARY_PREFS
                    }
                )
                if 'Item' in prefs_response:
                    dietary_prefs = DietaryPreferences(**prefs_response['Item'])
            except (ClientError, KeyError, TypeError) as e:
                logger.debug(f"Could not load dietary preferences: {e}")
                pass
            
            return UserProfile(
                userId=user['userId'],
                username=user['username'],
                email=user['email'],
                fullName=user.get('fullName', ''),
                age=user.get('age'),
                gender=user.get('gender', ''),
                location=user.get('location', ''),
                nutritionGoals=user.get('nutritionGoals', []),
                healthConditions=user.get('healthConditions', []),
                allergies=user.get('allergies', []),
                dietType=user.get('dietType', ''),
                dietaryPreferences=dietary_prefs,
                createdAt=user['createdAt'],
                updatedAt=user['updatedAt']
            )
            
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
    
    def update_dietary_preferences(self, user_id: str, preferences: DietaryPreferences):
        """Update user's dietary preferences"""
        try:
            self.table.put_item(
                Item={
                    'userId': user_id,
                    'dataType': DATA_TYPE_DIETARY_PREFS,
                    'allergies': preferences.allergies,
                    'dietType': preferences.dietType or '',
                    'restrictions': preferences.restrictions,
                    'preferences': preferences.preferences,
                    'updatedAt': datetime.now(timezone.utc).isoformat()
                }
            )
            return {"message": "Dietary preferences updated successfully"}
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update preferences: {str(e)}"
            )
