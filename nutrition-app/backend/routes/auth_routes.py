from fastapi import APIRouter, Depends
from models import UserSignup, UserLogin, TokenResponse, UserProfile, DietaryPreferences
from services.user_service import UserService
from auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()

@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserSignup):
    """Register a new user"""
    return user_service.signup(user_data)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user"""
    return user_service.login(login_data)

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    return user_service.get_profile(current_user["userId"])

@router.put("/dietary-preferences")
async def update_dietary_preferences(
    preferences: DietaryPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update user's dietary preferences"""
    return user_service.update_dietary_preferences(current_user["userId"], preferences)
