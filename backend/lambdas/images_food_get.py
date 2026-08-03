import json
import boto3
from urllib.request import Request, urlopen
from urllib.parse import quote

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

PEXELS_BASE_URL = 'https://api.pexels.com/v1'

_secrets_cache = {}

def _get_secret(key):
    if not _secrets_cache:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId='remedi_api_keys')
        _secrets_cache.update(json.loads(resp['SecretString']))
    return _secrets_cache.get(key, '')


def respond(status_code, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str)
    }


def _search_pexels(query, size='medium'):
    search_queries = [
        query,
        f"{query} food",
        f"fresh {query}",
    ]
    for q in search_queries:
        try:
            url = f"{PEXELS_BASE_URL}/search?query={quote(q)}&per_page=5&orientation=square"
            req = Request(url, headers={'Authorization': _get_secret('PEXELS_API_KEY')})
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                photos = data.get('photos', [])
                if photos:
                    photo = photos[0]
                    return photo['src'].get(size, photo['src'].get('medium', ''))
        except Exception:
            continue
    return ''


def lambda_handler(event, context):
    try:
        if event.get('httpMethod') == 'OPTIONS':
            return respond(200, {'message': 'OK'})

        params = event.get('queryStringParameters') or {}
        food_name = params.get('name', '')
        size = params.get('size', 'medium')

        if not food_name:
            return respond(400, {'error': 'name query parameter is required'})

        image_url = _search_pexels(food_name.lower().strip(), size)

        return respond(200, {
            'food': food_name,
            'imageUrl': image_url,
            'size': size
        })

    except Exception as e:
        return respond(500, {'error': str(e)})
