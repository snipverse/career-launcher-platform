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

def calculate_score(resume):
    score = 0
    fields = ['name', 'skills', 'email', 'education', 'experience', 'projects', 'certifications']
    per_field_score = 100 / len(fields)

    for field in fields:
        if resume.get(field):
            if isinstance(resume[field], list):
                if len(resume[field]) > 0:
                    score += per_field_score
            elif isinstance(resume[field], str):
               if resume[field].strip():
                   score += per_field_score

    return round(score)

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
    try:
        resumes = load_data()  # ✅ FIXED: was loading wrong file before
        for r in resumes:
            r['score'] = calculate_score(r)

        return jsonify(resumes)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

