from flask import Flask, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

@app.route('/api/handler', methods=['POST', 'OPTIONS'])
def get_ads_accounts():
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    if request.method == 'OPTIONS':
        return make_response('', 204, headers)

    request_json = request.get_json(silent=True)
    if not request_json or 'accessToken' not in request_json or 'developerToken' not in request_json:
        return jsonify({'error': 'Missing accessToken or developerToken'}), 400, headers

    access_token = request_json['accessToken']
    developer_token = request_json['developerToken']

    api_url = 'https://googleads.googleapis.com/v21/customers:listAccessibleCustomers'
    
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ: ОСТАВЛЯЕМ ТОЛЬКО МИНИМУМ ---
    api_headers = {
    'Authorization': f'Bearer {access_token}',
    'developer-token': developer_token,
    'login-customer-id': '9042451471', # Возвращаем ID твоего MCC
    'Accept': 'application/json'
}

    try:
        response = requests.get(api_url, headers=api_headers)
        response.raise_for_status()

        api_data = response.json()
        customer_ids = [name.split('/')[1] for name in api_data.get("resourceNames", [])]
        
        return jsonify({'accounts': customer_ids}), 200, headers

    except requests.exceptions.HTTPError as err:
        error_payload = {
            'error': 'Google Ads API Error',
            'status_code': err.response.status_code,
            'details': err.response.text
        }
        return jsonify(error_payload), err.response.status_code, headers
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers
