import functions_framework
import requests
import json

# Эта переменная больше не нужна, так как Vercel не требует project_id в заголовках
# GCP_PROJECT_ID = "ppc-tool-fresh-start" 
LOGIN_CUSTOMER_ID = "9042451471"

@functions_framework.http
def get_ads_accounts(request):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    request_json = request.get_json(silent=True)
    if not request_json or 'accessToken' not in request_json or 'developerToken' not in request_json:
        return (json.dumps({'error': 'Missing accessToken or developerToken'}), 400, headers)
    access_token = request_json['accessToken']
    developer_token = request_json['developerToken']
    api_url = 'https://googleads.googleapis.com/v15/customers:listAccessibleCustomers'
    api_headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'login-customer-id': LOGIN_CUSTOMER_ID,
        'Accept': 'application/json'
    }
    try:
        response = requests.get(api_url, headers=api_headers)
        response.raise_for_status()
        api_data = response.json()
        customer_ids = [name.split('/')[1] for name in api_data.get("resourceNames", [])]
        return (json.dumps({'accounts': customer_ids}), 200, headers)
    except requests.exceptions.HTTPError as err:
        error_payload = { 'error': 'Google Ads API Error', 'status_code': err.response.status_code, 'details': err.response.text }
        return (json.dumps(error_payload), err.response.status_code, headers)
    except Exception as e:
        return (json.dumps({'error': str(e)}), 500, headers)
