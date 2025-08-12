from flask import Flask, request, jsonify, make_response
import requests

app = Flask(__name__)

# Эта функция будет вызываться для любого запроса к /api/
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def handler(path):
    # Обработка CORS
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type")
        response.headers.add('Access-Control-Allow-Methods', "POST")
        return response

    request_json = request.get_json(silent=True)
    if not request_json: return jsonify({'error': 'Invalid JSON'}), 400

    action = request_json.get('action')

    if action == 'get_accounts':
        return get_ads_accounts(request_json)
    elif action == 'get_keywords':
        return get_keyword_ideas(request_json)
    else:
        return jsonify({'error': 'Invalid action specified'}), 400

def get_ads_accounts(data):
    access_token = data.get('accessToken')
    developer_token = data.get('developerToken')
    api_url = 'https://googleads.googleapis.com/v21/customers:listAccessibleCustomers'
    api_headers = {'Authorization': f'Bearer {access_token}', 'developer-token': developer_token, 'Accept': 'application/json'}
    try:
        response = requests.get(api_url, headers=api_headers)
        response.raise_for_status()
        api_data = response.json()
        customer_ids = [name.split('/')[1] for name in api_data.get("resourceNames", [])]
        return jsonify({'accounts': customer_ids})
    except requests.exceptions.HTTPError as err:
        return jsonify({'error': 'Google Ads API Error', 'details': err.response.text}), err.response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_keyword_ideas(data):
    access_token = data.get('accessToken')
    developer_token = data.get('developerToken')
    customer_id = data.get('customerId')
    api_url = f"https://googleads.googleapis.com/v21/customers/{customer_id.replace('-', '')}:generateKeywordIdeas"
    payload = {
        "keywordSeed": {"keywords": data.get('masks', [])},
        "language": f"languageConstants/{data.get('languageId')}",
        "geoTargetConstants": [f"geoTargetConstants/{data.get('countryId')}"]
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'developer-token': developer_token,
        'login-customer-id': customer_id.replace('-', ''),
        'Content-Type': 'application/json', 'Accept': 'application/json'
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        ideas = response.json().get("results", [])
        keyword_results = []
        for idea in ideas:
            metrics = idea.get("keywordIdeaMetrics", {})
            keyword_results.append({
                "text": idea.get("text"),
                "avgMonthlySearches": metrics.get("avgMonthlySearches"),
                "mask": data.get('masks')[0]
            })
        return jsonify({'keywords': keyword_results})
    except requests.exceptions.HTTPError as err:
        return jsonify({'error': 'Google Ads API Error', 'details': err.response.text}), err.response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500
