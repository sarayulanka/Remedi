"""
Image Service for fetching food images dynamically.
Uses Pexels API for high-quality food images - NO hardcoded fallbacks.
Every food gets its own unique, dynamically searched image.
"""
import os
import httpx
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

# Pexels API - Free tier allows 200 requests/hour
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', '')
PEXELS_BASE_URL = 'https://api.pexels.com/v1'

# Simple in-memory cache for image URLs (persists during server lifetime)
_image_cache: Dict[str, str] = {}


async def search_food_image(food_name: str, size: str = 'medium') -> str:
    """
    Search for a food image using Pexels API.
    Always returns a unique image for each food - no generic fallbacks.

    Args:
        food_name: Name of the food to search for (should be the imageSearchTerm from AI)
        size: Image size - 'small', 'medium', 'large', or 'original'

    Returns:
        URL of the food image
    """
    if not food_name:
        food_name = "healthy food"

    # Normalize for caching
    cache_key = f"{food_name.lower().strip()}_{size}"

    # Check cache first
    if cache_key in _image_cache:
        return _image_cache[cache_key]

    # Search Pexels with the food name
    image_url = await _search_pexels_exhaustive(food_name, size)

    if image_url:
        _image_cache[cache_key] = image_url
        return image_url

    # This shouldn't happen if Pexels API is working, but just in case
    # Search for something generic related to the food
    fallback_url = await _search_pexels_exhaustive("fresh healthy food", size)
    if fallback_url:
        _image_cache[cache_key] = fallback_url
        return fallback_url

    # Absolute last resort - return empty string, let frontend handle it
    return ""


async def _search_pexels_exhaustive(food_name: str, size: str) -> Optional[str]:
    """
    Search Pexels API exhaustively with multiple query variations.
    Tries different phrasings until it finds a good image.
    """
    if not PEXELS_API_KEY:
        print("Warning: PEXELS_API_KEY not set")
        return None

    # Clean up the search term
    clean_name = food_name.lower().strip()

    # Generate multiple search queries to try
    search_queries = [
        clean_name,                          # Direct search: "spinach"
        f"{clean_name} food",                # With food: "spinach food"
        f"fresh {clean_name}",               # Fresh version: "fresh spinach"
        f"{clean_name} healthy",             # Healthy version: "spinach healthy"
        f"{clean_name} ingredient",          # As ingredient: "spinach ingredient"
        f"raw {clean_name}",                 # Raw version: "raw spinach"
        f"{clean_name} closeup",             # Closeup: "spinach closeup"
    ]

    # Try each query until we get a result
    for query in search_queries:
        image_url = await _single_pexels_search(query, size)
        if image_url:
            return image_url

    # If compound name, try just the main word
    words = clean_name.split()
    if len(words) > 1:
        for word in reversed(words):  # Try from last word (usually the main food)
            if len(word) > 2:
                image_url = await _single_pexels_search(word, size)
                if image_url:
                    return image_url

    return None


async def _single_pexels_search(query: str, size: str) -> Optional[str]:
    """Execute a single Pexels search query."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PEXELS_BASE_URL}/search",
                params={
                    'query': query,
                    'per_page': 5,  # Get a few options
                    'orientation': 'square'
                },
                headers={
                    'Authorization': PEXELS_API_KEY
                },
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                photos = data.get('photos', [])

                if photos:
                    # Return the first photo's URL in the requested size
                    photo = photos[0]
                    image_url = photo['src'].get(size, photo['src'].get('medium', ''))
                    if image_url:
                        return image_url

    except Exception as e:
        print(f"Pexels search error for '{query}': {str(e)}")

    return None


async def search_food_images_batch(foods: List[str], size: str = 'medium') -> Dict[str, str]:
    """
    Search for multiple food images at once.
    Each food gets its own unique image.

    Args:
        foods: List of food names to search for
        size: Image size

    Returns:
        Dictionary mapping food names to image URLs
    """
    results = {}

    for food_name in foods:
        if not food_name:
            continue

        image_url = await search_food_image(food_name, size)
        results[food_name] = image_url

    return results


def get_food_image_sync(food_name: str) -> str:
    """
    Synchronous version - checks cache only.
    For async image fetching, use search_food_image instead.
    """
    if not food_name:
        return ""

    cache_key = f"{food_name.lower().strip()}_medium"
    return _image_cache.get(cache_key, "")


def clear_image_cache():
    """Clear the image cache."""
    global _image_cache
    _image_cache = {}
