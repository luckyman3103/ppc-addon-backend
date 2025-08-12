from flask import Flask, request, jsonify, make_response
import requests
import json

app = Flask(__name__)

# --- ОБЩАЯ ФУНКЦИЯ ДЛЯ ОБРАБОТКИ CORS ---
def build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

# --- ФУНКЦИЯ 1: ПОЛУЧЕНИЕ СПИСКА АККАУНТОВ ---
@app.route('/api/get-ads-accounts', methods=['POST', 'OPTIONS'])
def get_ads_accounts():
    if request.method == 'OPTIONS':
        return build_cors_preflight_response()

    # (Логика этой функции остается без изменений)
    request_json = request.get_json(silent=True)
    if not request_json or 'accessToken' not in request_json or 'developerToken' not in request_json:
        return jsonify({'error': 'Missing tokens'}), 400
    
    access_token = request_json['accessToken']
    developer_token = request_json['developerToken']
    api_url = 'https://googleads.googleapis.com/v21/customers:listAccessibleCustomers'
    api_headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'Accept': 'application/json'
    }
    try:
        response = requests.get(api_url, headers=api_headers)
        response.raise_for_status()
        api_data = response.json()
        customer_ids = [name.split('/')[1] for name in api_data.get("resourceNames", [])]
        return jsonify({'accounts': customer_ids}), 200
    except requests.exceptions.HTTPError as err:
        return jsonify({'error': 'Google Ads API Error', 'details': err.response.text}), err.response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- НОВАЯ ФУНКЦИЯ 2: СБОР КЛЮЧЕВЫХ СЛОВ ---
@app.route('/api/get-keyword-ideas', methods=['POST', 'OPTIONS'])
def get_keyword_ideas():
    if request.method == 'OPTIONS':
        return build_cors_preflight_response()

    # Получаем все необходимые данные от Apps Script
    request_json = request.get_json(silent=True)
    if not request_json:
        return jsonify({'error': 'Invalid JSON'}), 400

    # Проверяем наличие всех ключей
    required_keys = ['accessToken', 'developerToken', 'customerId', 'languageId', 'countryId', 'masks']
    if not all(key in request_json for key in required_keys):
        return jsonify({'error': 'Missing required parameters'}), 400

    access_token = request_json['accessToken']
    developer_token = request_json['developerToken']
    customer_id = request_json['customerId']
    language_id = request_json['languageId']
    country_id = request_json['countryId']
    masks = request_json['masks']
    
    keyword_results = []

    # Проходим по каждой маске и делаем отдельный запрос
    for mask in masks:
        api_url = f"https://googleads.googleapis.com/v21/customers/{customer_id.replace('-', '')}:generateKeywordIdeas"
        
        payload = {
            "keywordSeed": {"keywords": [mask]},
            "language": f"languageConstants/{language_id}",
            "geoTargetConstants": [f"geoTargetConstants/{country_id}"]
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'developer-token': developer_token,
            'login-customer-id': customer_id.replace('-', ''),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            ideas = response.json().get("results", [])
            for idea in ideas:
                metrics = idea.get("keywordIdeaMetrics", {})
                keyword_results.append({
                    "text": idea.get("text"),
                    "avgMonthlySearches": metrics.get("avgMonthlySearches"),
                    "mask": mask
                })
        except requests.exceptions.HTTPError as err:
            # Если хоть один запрос неудачный, возвращаем ошибку
            return jsonify({'error': f'Google Ads API Error for mask "{mask}"', 'details': err.response.text}), err.response.status_code
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    # Возвращаем успешный результат
    return jsonify({'keywords': keyword_results}), 200
