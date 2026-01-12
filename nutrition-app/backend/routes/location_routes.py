from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from services.location_service import LocationService
from auth import get_current_user

router = APIRouter(prefix="/locations", tags=["Locations"])
location_service = LocationService()

@router.get("/search")
async def search_locations(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: int = Query(5000, description="Search radius in meters"),
    types: Optional[str] = Query(None, description="Comma-separated location types"),
    current_user: dict = Depends(get_current_user)
):
    """Search for food locations near a coordinate"""
    location_types = types.split(',') if types else None
    
    return location_service.find_food_locations(
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        location_types=location_types
    )

@router.post("/save")
async def save_location(
    location_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Save a location to user's collection"""
    return location_service.save_location(
        user_id=current_user["userId"],
        location_data=location_data
    )

@router.get("/saved")
async def get_saved_locations(current_user: dict = Depends(get_current_user)):
    """Get all saved locations for the current user"""
    return location_service.get_saved_locations(current_user["userId"])

@router.delete("/saved/{location_id}")
async def delete_saved_location(
    location_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a saved location"""
    return location_service.delete_saved_location(
        user_id=current_user["userId"],
        location_id=location_id
    )
