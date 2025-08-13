from flask import Flask, request, jsonify, make_response
import requests

app = Flask(__name__)

# --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def get_keyword_ideas(path):
    # Обработка CORS preflight
    if request.method == 'OPTIONS':
        headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'Content-Type'}
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}
    request_json = request.get_json(silent=True)
    access_token = request_json.get('accessToken')
    developer_token = request_json.get('developerToken')
    customer_id = request_json.get('customerId')
    language_id = request_json.get('languageId')
    country_id = request_json.get('countryId')
    masks = request_json.get('masks', [])
    
    keyword_results = []
    
    for mask in masks:
        api_url = f"https://googleads.googleapis.com/v21/customers/{customer_id.replace('-', '')}:generateKeywordIdeas"
        payload = {"keywordSeed": {"keywords": [mask]}, "language": f"languageConstants/{language_id}", "geoTargetConstants": [f"geoTargetConstants/{country_id}"]}
        api_headers = {'Authorization': f'Bearer {access_token}', 'developer-token': developer_token, 'login-customer-id': customer_id.replace('-', ''), 'Content-Type': 'application/json', 'Accept': 'application/json'}
        try:
            response = requests.post(api_url, headers=api_headers, json=payload)
            response.raise_for_status()
            ideas = response.json().get("results", [])
            for idea in ideas:
                metrics = idea.get("keywordIdeaMetrics", {})
                keyword_results.append({"text": idea.get("text"), "avgMonthlySearches": metrics.get("avgMonthlySearches"), "mask": mask})
        except requests.exceptions.HTTPError as err:
            return jsonify({'error': f'Google Ads API Error for mask "{mask}"', 'details': err.response.text}), err.response.status_code, headers
        except Exception as e:
            return jsonify({'error': str(e)}), 500, headers
    
    return jsonify({'keywords': keyword_results}), 200, headers
