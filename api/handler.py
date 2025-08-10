from flask import Flask, request, jsonify, make_response
import requests
import json

# Создаем веб-приложение
app = Flask(__name__)

# Эта функция будет обрабатывать все запросы к /api/handler
@app.route('/api/handler', methods=['POST', 'OPTIONS'])
def get_ads_accounts():
    # Настройка заголовков для ответа (CORS)
    # Это позволяет нашему сайдбару в Google Sheets обращаться к этой функции
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    # Обработка pre-flight запроса от браузера
    if request.method == 'OPTIONS':
        return make_response('', 204, headers)

    # --- НАША СТАРАЯ ЛОГИКА ОСТАЛАСЬ ПОЧТИ БЕЗ ИЗМЕНЕНИЙ ---

    LOGIN_CUSTOMER_ID = "9042451471"

    # Получаем данные из запроса от Apps Script
    request_json = request.get_json(silent=True)
    if not request_json or 'accessToken' not in request_json or 'developerToken' not in request_json:
        return jsonify({'error': 'Missing accessToken or developerToken'}), 400, headers

    access_token = request_json['accessToken']
    developer_token = request_json['developerToken']

    # Формируем URL и заголовки для запроса к Google Ads API
    api_url = 'https://googleads.googleapis.com/v15/customers:listAccessibleCustomers'
    
    api_headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'login-customer-id': LOGIN_CUSTOMER_ID,
        'Accept': 'application/json'
    }

    # Делаем запрос к Google Ads API
    try:
        response = requests.get(api_url, headers=api_headers)
        response.raise_for_status()

        api_data = response.json()
        customer_ids = [name.split('/')[1] for name in api_data.get("resourceNames", [])]
        
        # Возвращаем успешный результат
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
