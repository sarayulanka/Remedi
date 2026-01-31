import boto3
import json
import sys

session = boto3.Session(profile_name='sarayu', region_name='us-east-1')
apig = session.client('apigateway')
lam = session.client('lambda')

ACCOUNT_ID = '740701771875'
REGION = 'us-east-1'

# VTL mapping template: transforms API Gateway request into Lambda-compatible event
MAPPING_TEMPLATE = """{
  "body": "$util.escapeJavaScript($input.body)",
  "httpMethod": "$context.httpMethod",
  "resource": "$context.resourcePath",
  "pathParameters": {
    #foreach($key in $input.params().path.keySet())
    "$key": "$input.params().path.get($key)"#if($foreach.hasNext),#end
    #end
  },
  "queryStringParameters": {
    #foreach($key in $input.params().querystring.keySet())
    "$key": "$input.params().querystring.get($key)"#if($foreach.hasNext),#end
    #end
  }
}"""

# All routes: (path, method, lambda_function_name)
ROUTES = [
    ('/users', 'POST', 'users_post'),
    ('/users', 'GET', 'users_get'),
    ('/users/{userid}', 'PUT', 'users_userid_put'),
    ('/users/{userid}', 'GET', 'users_userid_get'),
    ('/users/{userid}', 'DELETE', 'users_userid_delete'),
    ('/users/{userid}/login', 'POST', 'users_userid_login_post'),
    ('/users/{userid}/preferences', 'POST', 'users_userid_preferences_post'),
    ('/users/{userid}/preferences', 'GET', 'users_userid_preferences_get'),
    ('/users/{userid}/preferences', 'PUT', 'users_userid_preferences_put'),
    ('/users/{userid}/activity', 'POST', 'users_userid_activity_post'),
    ('/users/{userid}/activity', 'GET', 'users_userid_activity_get'),
    ('/users/{userid}/activity/{activityid}', 'GET', 'users_userid_activity_activityid_get'),
    ('/users/{userid}/activity/{activityid}', 'DELETE', 'users_userid_activity_activityid_delete'),
    ('/users/{userid}/goals', 'POST', 'users_userid_goals_post'),
    ('/users/{userid}/goals', 'GET', 'users_userid_goals_get'),
    ('/users/{userid}/goals', 'DELETE', 'users_userid_goals_delete'),
    ('/users/{userid}/goals/{goalid}', 'PUT', 'users_userid_goals_goalid_put'),
    ('/users/{userid}/goals/{goalid}', 'GET', 'users_userid_goals_goalid_get'),
    ('/users/{userid}/goals/{goalid}', 'DELETE', 'users_userid_goals_goalid_delete'),
    ('/users/{userid}/rewards', 'POST', 'users_userid_rewards_post'),
    ('/users/{userid}/rewards', 'GET', 'users_userid_rewards_get'),
    ('/users/{userid}/alerts', 'POST', 'users_userid_alerts_post'),
    ('/users/{userid}/alerts', 'GET', 'users_userid_alerts_get'),
    ('/users/{userid}/alerts/{alertid}', 'PUT', 'users_userid_alerts_alertid_put'),
    ('/users/{userid}/alerts/{alertid}', 'GET', 'users_userid_alerts_alertid_get'),
    ('/users/{userid}/alerts/{alertid}', 'DELETE', 'users_userid_alerts_alertid_delete'),
    ('/users/{userid}/notifications', 'POST', 'users_userid_notifications_post'),
    ('/users/{userid}/notifications', 'GET', 'users_userid_notifications_get'),
    ('/users/{userid}/notifications/{notificationid}', 'GET', 'users_userid_notifications_notificationid_get'),
    ('/users/{userid}/notifications/{notificationid}', 'DELETE', 'users_userid_notifications_notificationid_delete'),
    ('/recipes/search', 'POST', 'recipes_search_post'),
    ('/recipes/scan', 'POST', 'recipes_scan_post'),
    ('/refvalue', 'POST', 'refvalue_post'),
    ('/refvalue', 'GET', 'refvalue_get'),
    ('/refvalue/{refvalueid}', 'GET', 'refvalue_refvalueid_get'),
    ('/refvalue/{refvalueid}', 'PUT', 'refvalue_refvalueid_put'),
    ('/refvalue/{refvalueid}', 'DELETE', 'refvalue_refvalueid_delete'),
]


def main():
    # ── 1. Create REST API ──────────────────────────────────────────────
    print("Creating REST API 'remedi-backend-api'...")
    api = apig.create_rest_api(
        name='remedi-backend-api',
        description='Remedi Mobile Application Backend API',
        endpointConfiguration={'types': ['REGIONAL']}
    )
    api_id = api['id']
    print(f"  API ID: {api_id}")

    # ── 2. Get root resource ────────────────────────────────────────────
    resources = apig.get_resources(restApiId=api_id)
    root_id = [r for r in resources['items'] if r['path'] == '/'][0]['id']

    # ── 3. Collect all unique resource paths and create them ────────────
    all_paths = set()
    for path, _, _ in ROUTES:
        parts = path.strip('/').split('/')
        for i in range(1, len(parts) + 1):
            all_paths.add('/' + '/'.join(parts[:i]))

    sorted_paths = sorted(all_paths, key=lambda p: (p.count('/'), p))
    resource_map = {'/': root_id}

    print(f"\nCreating {len(sorted_paths)} resources...")
    for path in sorted_paths:
        parent_path = path.rsplit('/', 1)[0] or '/'
        path_part = path.rsplit('/', 1)[-1]
        parent_id = resource_map[parent_path]

        resource = apig.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        resource_map[path] = resource['id']
        print(f"  {path}")

    # ── 4. Create methods, integrations, and Lambda permissions ─────────
    print(f"\nConfiguring {len(ROUTES)} method integrations...")
    success = 0
    errors = []

    for path, method, func_name in ROUTES:
        try:
            resource_id = resource_map[path]
            lambda_arn = f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{func_name}'
            integration_uri = (
                f'arn:aws:apigateway:{REGION}:lambda:path'
                f'/2015-03-31/functions/{lambda_arn}/invocations'
            )

            # Collect path parameters from the full path
            request_params = {}
            for part in path.strip('/').split('/'):
                if part.startswith('{') and part.endswith('}'):
                    param = part[1:-1]
                    request_params[f'method.request.path.{param}'] = True

            # 4a. Method
            apig.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                authorizationType='NONE',
                requestParameters=request_params
            )

            # 4b. Integration (AWS type = non-proxy Lambda)
            apig.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                type='AWS',
                integrationHttpMethod='POST',
                uri=integration_uri,
                passthroughBehavior='WHEN_NO_MATCH',
                requestTemplates={
                    'application/json': MAPPING_TEMPLATE
                }
            )

            # 4c. Method response (200)
            apig.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                statusCode='200',
                responseModels={'application/json': 'Empty'},
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': False
                }
            )

            # 4d. Integration response (200, passthrough)
            apig.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method,
                statusCode='200',
                responseTemplates={'application/json': ''},
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )

            # 4e. Grant API Gateway permission to invoke the Lambda
            try:
                lam.add_permission(
                    FunctionName=func_name,
                    StatementId=f'apigw-{func_name}',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f'arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/*/{method}{path}'
                )
            except lam.exceptions.ResourceConflictException:
                pass  # Permission already exists

            success += 1
            print(f"  {method:6s} {path:55s} -> {func_name}")

        except Exception as e:
            errors.append((path, method, func_name, str(e)))
            print(f"  FAIL  {method:6s} {path} -> {e}")

    # ── 5. Deploy to 'dev' stage ────────────────────────────────────────
    print("\nDeploying to 'dev' stage...")
    apig.create_deployment(
        restApiId=api_id,
        stageName='dev',
        description='Initial deployment'
    )

    invoke_url = f'https://{api_id}.execute-api.{REGION}.amazonaws.com/dev'

    print(f"\n{'=' * 65}")
    print(f"  API: remedi-backend-api")
    print(f"  ID:  {api_id}")
    print(f"  Methods configured: {success}/{len(ROUTES)}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for p, m, f, e in errors:
            print(f"    {m} {p} -> {e}")
    print(f"  Invoke URL: {invoke_url}")
    print(f"{'=' * 65}")


if __name__ == '__main__':
    main()
