from flask import Flask, request, jsonify, make_response
import requests

app = Flask(__name__)

# --- ИЗМЕНЕНИЕ ЗДЕСЬ: Разрешаем методы POST и OPTIONS ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def get_ads_accounts(path):
    # Обработка CORS preflight
    if request.method == 'OPTIONS':
        headers = {'Access-Control-Allow-Origin': '*', 'Access-control-allow-headers': 'Content-Type'}
        return ('', 204, headers)

    # Основная логика
    headers = {'Access-Control-Allow-Origin': '*'}
    request_json = request.get_json(silent=True)
    access_token = request_json.get('accessToken')
    developer_token = request_json.get('developerToken')

    api_url = 'https://googleads.googleapis.com/v21/customers:listAccessibleCustomers'
    api_headers = {'Authorization': f'Bearer {access_token}', 'developer-token': developer_token, 'Accept': 'application/json'}
    
    try:
        response = requests.get(api_url, headers=api_headers)
        response.raise_for_status()
        api_data = response.json()
        customer_ids = [name.split('/')[1] for name in api_data.get("resourceNames", [])]
        return jsonify({'accounts': customer_ids}), 200, headers
    except requests.exceptions.HTTPError as err:
        return jsonify({'error': 'Google Ads API Error', 'details': err.response.text}), err.response.status_code, headers
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers
