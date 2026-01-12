from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Authentication Models
class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    fullName: Optional[str] = ''
    age: Optional[int] = 0
    gender: Optional[str] = ''
    location: Optional[str] = ''
    nutritionGoals: Optional[List[str]] = []
    healthConditions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    dietType: Optional[str] = ''

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    userId: str
    username: str

# User Profile Models
class DietaryPreferences(BaseModel):
    allergies: List[str] = []
    dietType: Optional[str] = None  # vegetarian, vegan, keto, etc.
    restrictions: List[str] = []
    preferences: List[str] = []

class UserProfile(BaseModel):
    userId: str
    username: str
    email: str
    fullName: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    nutritionGoals: Optional[List[str]] = None
    healthConditions: Optional[List[str]] = None
    dietaryPreferences: Optional[DietaryPreferences] = None
    createdAt: str
    updatedAt: str

# Gamification Models
class Streak(BaseModel):
    userId: str
    currentStreak: int = 0
    longestStreak: int = 0
    lastCheckIn: Optional[str] = None

class Badge(BaseModel):
    badgeId: str
    name: str
    description: str
    icon: str
    earnedAt: str

class Goal(BaseModel):
    goalId: str
    userId: str
    title: str
    description: str
    targetDays: int
    currentDays: int = 0
    completed: bool = False
    createdAt: str
    completedAt: Optional[str] = None

# Location Models
class SavedLocation(BaseModel):
    locationId: str
    userId: str
    name: str
    address: str
    latitude: float
    longitude: float
    type: str  # shelter, kitchen, food_bank
    hours: Optional[str] = None
    phone: Optional[str] = None
    savedAt: str

# Remedy Models
class FoodRemedy(BaseModel):
    foods: List[str]
    nutrients: List[str]
    explanation: str
    fdaSource: Optional[str] = None

class SavedRemedy(BaseModel):
    remedyId: str
    userId: str
    condition: str
    conditionExplanation: str
    remedy: FoodRemedy
    imageUrl: Optional[str] = None
    savedAt: str

# Health Analysis Request
class HealthAnalysisRequest(BaseModel):
    imageBase64: Optional[str] = None
    textDescription: Optional[str] = None
    userConcerns: Optional[str] = None
