import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "api_log.txt")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
data_store = []

@app.route('/')
def home():
    return "Welcome to Resume API"

@app.route('/resume', methods=['GET'])
def get_resumes():
    return jsonify(data_store)

@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.get_json()

      # Defensive check
    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' field"}), 400
    
    data_store.append(data)
    logging.info(f"Resume Submitted: {data}")
    return jsonify({
        "message": f"Resume received from {data['name']}",
        "total_resumes": len(data_store)
    })

if __name__ == '__main__':
    app.run(debug=True)
