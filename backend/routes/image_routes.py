"""
Image routes for fetching food images dynamically.
"""
from typing import List
from fastapi import APIRouter, Query
from services.image_service import search_food_image, get_food_image_sync

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/food")
async def get_food_image(
    name: str = Query(..., description="Name of the food to get an image for"),
    size: str = Query("medium", description="Image size: small, medium, large, or original")
):
    """
    Get an image URL for a food item.

    This endpoint searches for food images dynamically using the Pexels API.

    Args:
        name: The name of the food (e.g., "salmon", "spinach", "almonds")
        size: The desired image size

    Returns:
        JSON with the image URL
    """
    image_url = await search_food_image(name, size)
    return {
        "food": name,
        "imageUrl": image_url,
        "size": size
    }


@router.post("/food/batch")
async def get_food_images_batch(
    foods: List[str],
    size: str = Query("medium", description="Image size: small, medium, large, or original")
):
    """
    Get image URLs for multiple food items in a single request.

    Args:
        foods: List of food names
        size: The desired image size

    Returns:
        JSON with food names mapped to image URLs
    """
    results = {}
    for food in foods[:20]:  # Limit to 20 items per request
        image_url = await search_food_image(food, size)
        results[food] = image_url

    return {
        "images": results,
        "size": size,
        "count": len(results)
    }
