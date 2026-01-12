from fastapi import APIRouter, Depends
from models import HealthAnalysisRequest
from services.health_service import HealthAnalysisService
from auth import get_current_user
from typing import Dict

router = APIRouter(prefix="/health", tags=["Health Analysis"])
health_service = HealthAnalysisService()

@router.post("/analyze")
async def analyze_health_concern(
    request: HealthAnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict:
    """Analyze a health concern using image and/or text description"""
    return health_service.analyze_health_concern(
        user_id=current_user["userId"],
        image_base64=request.imageBase64,
        text_description=request.textDescription,
        user_concerns=request.userConcerns
    )

@router.post("/save-remedy")
async def save_remedy(
    remedy_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """Save a remedy to user's collection"""
    return health_service.save_remedy(
        user_id=current_user["userId"],
        condition=remedy_data.get("condition"),
        condition_explanation=remedy_data.get("conditionExplanation"),
        remedy=remedy_data.get("remedy"),
        image_url=remedy_data.get("imageUrl")
    )

@router.get("/saved-remedies")
async def get_saved_remedies(current_user: dict = Depends(get_current_user)):
    """Get all saved remedies for the current user"""
    return health_service.get_saved_remedies(current_user["userId"])
