from flask import Flask, request, jsonify, make_response
import requests
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
@app.route('/', defaults={'path': ''}, methods=['POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['POST', 'OPTIONS'])
def get_keyword_masks(path):
    # Обработка CORS preflight
    if request.method == 'OPTIONS':
        headers = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'POST', 'Access-Control-Allow-Headers': 'Content-Type'}
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}
    request_json = request.get_json(silent=True)
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    page_url = request_json.get('url')

    try:
        page_response = requests.get(page_url)
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.text, 'html.parser')
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        page_text = ' '.join(soup.stripped_strings)[:2000]

        prompt = f"You are a Google Ads PPC specialist. Based on the website text below, suggest 10 keyword masks (2-5 words each) in Russian, without repetitions or quotation marks. Text: {page_text}"
        openai_payload = {"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        openai_headers = {"Authorization": f"Bearer {openai_api_key}", "Content-Type": "application/json"}

        openai_response = requests.post("https://api.openai.com/v1/chat/completions", headers=openai_headers, json=openai_payload)
        openai_response.raise_for_status()
        result = openai_response.json()
        text = result['choices'][0]['message']['content']
        masks = [line.strip().lstrip('-•0123456789. ') for line in text.split('\n') if line.strip()]
        return jsonify({'masks': masks}), 200, headers
    except Exception as e:
        return jsonify({'error': str(e)}), 500, headers
