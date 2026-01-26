from fastapi import APIRouter, Depends
from services.gamification_service import GamificationService
from auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/gamification", tags=["Gamification"])
gamification_service = GamificationService()

class GoalCreate(BaseModel):
    title: str
    description: str
    targetDays: int

@router.post("/check-in")
async def check_in(current_user: dict = Depends(get_current_user)):
    """Record a daily check-in"""
    return gamification_service.check_in(current_user["userId"])

@router.get("/streak")
async def get_streak(current_user: dict = Depends(get_current_user)):
    """Get current streak information"""
    return gamification_service.get_streak(current_user["userId"])

@router.get("/badges")
async def get_badges(current_user: dict = Depends(get_current_user)):
    """Get all earned badges"""
    return gamification_service.get_badges(current_user["userId"])

@router.get("/badges/available")
async def get_available_badges():
    """Get all available badges"""
    return gamification_service.get_all_available_badges()

@router.post("/goals")
async def create_goal(
    goal: GoalCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new nutrition goal"""
    return gamification_service.create_goal(
        user_id=current_user["userId"],
        title=goal.title,
        description=goal.description,
        target_days=goal.targetDays
    )

@router.put("/goals/{goal_id}/progress")
async def update_goal_progress(
    goal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Update progress on a goal"""
    return gamification_service.update_goal_progress(
        user_id=current_user["userId"],
        goal_id=goal_id
    )

@router.get("/goals")
async def get_goals(current_user: dict = Depends(get_current_user)):
    """Get all goals"""
    return gamification_service.get_goals(current_user["userId"])

@router.get("/streak/milestones")
async def get_milestones(current_user: dict = Depends(get_current_user)):
    """Get milestone progress"""
    return gamification_service.get_milestones(current_user["userId"])

@router.post("/streak/use-freeze")
async def use_streak_freeze(current_user: dict = Depends(get_current_user)):
    """Check freeze availability"""
    return gamification_service.use_streak_freeze(current_user["userId"])

@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a goal"""
    return gamification_service.delete_goal(
        user_id=current_user["userId"],
        goal_id=goal_id
    )

# ==================== XP ENDPOINTS ====================

@router.get("/xp")
async def get_xp(current_user: dict = Depends(get_current_user)):
    """Get current XP and level status"""
    return gamification_service.get_xp(current_user["userId"])

@router.get("/xp/history")
async def get_xp_history(current_user: dict = Depends(get_current_user)):
    """Get XP history for charts"""
    return gamification_service.get_xp_history(current_user["userId"])

class XPAward(BaseModel):
    action: str
    amount: int = None

@router.post("/xp/award")
async def award_xp(
    xp_data: XPAward,
    current_user: dict = Depends(get_current_user)
):
    """Award XP for an action (primarily for internal use)"""
    return gamification_service.award_xp(
        user_id=current_user["userId"],
        action=xp_data.action,
        base_amount=xp_data.amount
    )

# ==================== AI GOAL GENERATION ====================

@router.post("/goals/generate")
async def generate_goals(current_user: dict = Depends(get_current_user)):
    """Check if all goals are completed and generate new AI-powered goals"""
    return gamification_service.check_and_generate_goals(current_user["userId"])
