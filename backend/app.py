from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = 'resumes.json'

# Read from JSON file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Write to JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return "Welcome to Resume API"

@app.route('/submit', methods=['POST'])
def submit_resume():
    data = request.get_json()
    resumes = load_data()
    resumes.append(data)
    save_data(resumes)
    return jsonify({"message": "Resume submitted successfully", "total": len(resumes)})

@app.route('/resume', methods=['GET'])
def get_resumes():
    return jsonify(load_data())

if __name__ == '__main__':
    app.run(debug=True)

