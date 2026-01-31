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


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _query_all_pages(table, **kwargs):
    """Helper to paginate through all results of a DynamoDB query."""
    items = []
    response = table.query(**kwargs)
    items.extend(response.get('Items', []))
    while 'LastEvaluatedKey' in response:
        kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
        response = table.query(**kwargs)
        items.extend(response.get('Items', []))
    return items


def lambda_handler(event, context):
    """POST /receipes/search — Search recipes by various criteria."""
    try:
        table_name = os.environ.get('RECIPES_TABLE', 'remedi-recipes')
        table = dynamodb.Table(table_name)

        # Parse request body
        body = event.get('body')
        if not body:
            body = {}
        elif isinstance(body, str):
            body = json.loads(body)

        meal_type = body.get('meal_type')
        cuisine_type = body.get('cuisine_type')
        difficulty_level = body.get('difficulty_level')
        diet_tags = body.get('diet_tags')  # e.g. ["VEGAN", "KETO"]
        exclude_allergens = body.get('exclude_allergens')  # e.g. ["GLUTEN", "DAIRY"]
        max_calories = body.get('max_calories')

        try:
            limit = int(body.get('limit', 20))
            if limit < 1:
                limit = 20
            if limit > 100:
                limit = 100
        except (ValueError, TypeError):
            limit = 20

        recipes = []

        # Search strategy: use the most specific GSI available
        if meal_type:
            # Query GSI gsi-meal-type
            recipes = _query_all_pages(
                table,
                IndexName='gsi-meal-type',
                KeyConditionExpression=Key('meal_type').eq(meal_type),
                ScanIndexForward=False
            )

        elif cuisine_type:
            # Query GSI gsi-cuisine-type
            recipes = _query_all_pages(
                table,
                IndexName='gsi-cuisine-type',
                KeyConditionExpression=Key('cuisine_type').eq(cuisine_type),
                ScanIndexForward=False
            )

        elif difficulty_level:
            # Query GSI gsi-difficulty
            recipes = _query_all_pages(
                table,
                IndexName='gsi-difficulty',
                KeyConditionExpression=Key('difficulty_level').eq(difficulty_level),
                ScanIndexForward=False
            )

        elif diet_tags and len(diet_tags) > 0:
            # For each diet tag, query GSI gsi-diet-allergen-index and intersect recipe_ids
            recipe_id_sets = []
            for tag in diet_tags:
                tag_items = _query_all_pages(
                    table,
                    IndexName='gsi-diet-allergen-index',
                    KeyConditionExpression=Key('gsi3_pk').eq(f"DIET#{tag}")
                )
                tag_recipe_ids = {item['recipe_id'] for item in tag_items}
                recipe_id_sets.append(tag_recipe_ids)

            # Intersect all sets to find recipes matching ALL diet tags
            if recipe_id_sets:
                matching_recipe_ids = recipe_id_sets[0]
                for s in recipe_id_sets[1:]:
                    matching_recipe_ids = matching_recipe_ids.intersection(s)

                # Fetch META records for matching recipe_ids
                for recipe_id in matching_recipe_ids:
                    response = table.get_item(
                        Key={
                            'recipe_id': recipe_id,
                            'record_type': 'META'
                        }
                    )
                    item = response.get('Item')
                    if item:
                        recipes.append(item)

        else:
            # No specific filter — Scan for META records
            scan_kwargs = {
                'FilterExpression': Attr('record_type').eq('META')
            }
            response = table.scan(**scan_kwargs)
            recipes = response.get('Items', [])
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = table.scan(**scan_kwargs)
                recipes.extend(response.get('Items', []))

        # Exclude allergens: query GSI for each allergen and remove matching recipe_ids
        if exclude_allergens and len(exclude_allergens) > 0:
            excluded_recipe_ids = set()
            for allergen in exclude_allergens:
                allergen_items = _query_all_pages(
                    table,
                    IndexName='gsi-diet-allergen-index',
                    KeyConditionExpression=Key('gsi3_pk').eq(f"ALRG#{allergen}")
                )
                for item in allergen_items:
                    excluded_recipe_ids.add(item.get('recipe_id'))

            recipes = [r for r in recipes if r.get('recipe_id') not in excluded_recipe_ids]

        # Filter by max_calories
        if max_calories is not None:
            try:
                max_cal = float(max_calories)
                recipes = [
                    r for r in recipes
                    if r.get('calories_per_serving') is not None
                    and float(r['calories_per_serving']) <= max_cal
                ]
            except (ValueError, TypeError):
                pass  # Ignore invalid max_calories

        # Apply limit
        recipes = recipes[:limit]

        # Build summary objects
        summaries = []
        for r in recipes:
            summary = {
                'recipe_id': r.get('recipe_id'),
                'title': r.get('title'),
                'meal_type': r.get('meal_type'),
                'cuisine_type': r.get('cuisine_type'),
                'difficulty_level': r.get('difficulty_level'),
                'calories_per_serving': r.get('calories_per_serving'),
                'total_time_minutes': r.get('total_time_minutes'),
                'image_url': r.get('image_url'),
                'created_at': r.get('created_at')
            }
            summaries.append(summary)

        return respond(200, {
            'recipes': summaries,
            'count': len(summaries)
        })

    except json.JSONDecodeError:
        return respond(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        return respond(500, {'error': str(e)})
