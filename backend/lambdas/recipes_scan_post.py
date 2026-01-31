import json
import os
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

MAX_RESULTS = 10


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _scan_meta_records(table):
    """Scan the table for all META records."""
    items = []
    scan_kwargs = {
        'FilterExpression': Attr('record_type').eq('META')
    }
    response = table.scan(**scan_kwargs)
    items.extend(response.get('Items', []))
    while 'LastEvaluatedKey' in response:
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.scan(**scan_kwargs)
        items.extend(response.get('Items', []))
    return items


def _build_recipe_summary(recipe):
    """Build a summary dict from a recipe META record."""
    return {
        'recipe_id': recipe.get('recipe_id'),
        'title': recipe.get('title'),
        'description': recipe.get('description'),
        'meal_type': recipe.get('meal_type'),
        'cuisine_type': recipe.get('cuisine_type'),
        'difficulty_level': recipe.get('difficulty_level'),
        'calories_per_serving': recipe.get('calories_per_serving'),
        'protein_g': recipe.get('protein_g'),
        'carbs_g': recipe.get('carbs_g'),
        'fat_g': recipe.get('fat_g'),
        'fiber_g': recipe.get('fiber_g'),
        'total_time_minutes': recipe.get('total_time_minutes'),
        'servings': recipe.get('servings'),
        'image_url': recipe.get('image_url'),
        'created_at': recipe.get('created_at')
    }


def lambda_handler(event, context):
    """POST /receipes/scan — Scan/analyze food for recipe matching."""
    try:
        table_name = os.environ.get('RECIPES_TABLE', 'remedi-recipes')
        table = dynamodb.Table(table_name)

        # Parse request body
        body = event.get('body')
        if not body:
            body = {}
        elif isinstance(body, str):
            body = json.loads(body)

        image_base64 = body.get('image_base64')
        text_description = body.get('text_description')
        nutrients = body.get('nutrients')  # e.g. [{"name": "protein_g", "min": 20}, ...]

        results = []
        analysis_method = None

        if nutrients and len(nutrients) > 0:
            # Filter META records by nutritional content
            analysis_method = 'nutrient_filter'
            all_recipes = _scan_meta_records(table)

            for recipe in all_recipes:
                matches_all = True
                for nutrient in nutrients:
                    nutrient_name = nutrient.get('name')
                    min_val = nutrient.get('min')
                    max_val = nutrient.get('max')

                    if not nutrient_name:
                        continue

                    recipe_val = recipe.get(nutrient_name)
                    if recipe_val is None:
                        matches_all = False
                        break

                    try:
                        recipe_val = float(recipe_val)
                    except (ValueError, TypeError):
                        matches_all = False
                        break

                    if min_val is not None and recipe_val < float(min_val):
                        matches_all = False
                        break
                    if max_val is not None and recipe_val > float(max_val):
                        matches_all = False
                        break

                if matches_all:
                    results.append(recipe)

                if len(results) >= MAX_RESULTS:
                    break

        elif text_description:
            # Basic keyword matching on title and description
            analysis_method = 'text_search'
            all_recipes = _scan_meta_records(table)

            # Tokenize the search text into lowercase keywords
            keywords = [kw.strip().lower() for kw in text_description.split() if kw.strip()]

            scored_recipes = []
            for recipe in all_recipes:
                title = (recipe.get('title') or '').lower()
                description = (recipe.get('description') or '').lower()
                combined_text = f"{title} {description}"

                # Count how many keywords match
                match_count = sum(1 for kw in keywords if kw in combined_text)
                if match_count > 0:
                    scored_recipes.append((match_count, recipe))

            # Sort by match count descending
            scored_recipes.sort(key=lambda x: x[0], reverse=True)
            results = [r[1] for r in scored_recipes[:MAX_RESULTS]]

        elif image_base64:
            # Image analysis requires external service integration
            analysis_method = 'image_analysis'
            all_recipes = _scan_meta_records(table)

            # Return some default results since image analysis is not yet integrated
            results = all_recipes[:MAX_RESULTS]

            summaries = [_build_recipe_summary(r) for r in results]

            return respond(200, {
                'message': 'Image analysis requires integration with an external service (e.g., AWS Rekognition). Returning default recipe results.',
                'analysis_method': analysis_method,
                'recipes': summaries,
                'count': len(summaries)
            })

        else:
            # No criteria provided — return a default set of recipes
            analysis_method = 'default'
            all_recipes = _scan_meta_records(table)
            results = all_recipes[:MAX_RESULTS]

        summaries = [_build_recipe_summary(r) for r in results]

        return respond(200, {
            'analysis_method': analysis_method,
            'recipes': summaries,
            'count': len(summaries)
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
