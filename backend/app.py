from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import io
import csv
from io import StringIO


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
        value = resume.get(field)
        if isinstance(value, list) and len(value) > 0:
                 score += per_field_score
        elif isinstance(value, str) and value.strip():
            if resume[field].strip():
                  score += per_field_score

    return round(score)

def get_recommendation(score):
    if score >= 85:
        return "Strong Candidate"
    elif score >= 60:
        return "Decent Profile"
    elif score >= 30:
        return "Needs More Details"
    else:
        return "Weak / Incomplete"

    

@app.route('/')
def home():
    return "Welcome to Resume API"

@app.route('/submit', methods=['POST'])
def submit_resume():
    data = request.get_json()

    data['score'] = calculate_score(data)
    data['recommendation'] = get_recommendation(data['score'])
    
    resumes = load_data()
    resumes.append(data)
    save_data(resumes)
    return jsonify({"message": "Resume submitted successfully", "total": len(resumes)})

@app.route('/resume', methods=['GET'])
def get_resumes():
    try:
        resumes = load_data()

        for r in resumes:
            r['score'] = calculate_score(r)
            r['recommendation'] = get_recommendation(r['score'])

        return jsonify(resumes)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/stats', methods=['GET'])
def get_stats():
    resumes = load_data()
    
    summary = {
        "total": len(resumes),
        "strong": 0,
        "decent": 0,
        "needs_more": 0,
        "weak": 0
    }

    for r in resumes:
        score = calculate_score(r)
        if score >= 85:
            summary["strong"] += 1
        elif score >= 60:
            summary["decent"] += 1
        elif score >= 30:
            summary["needs_more"] += 1
        else:
            summary["weak"] += 1

    return jsonify(summary)

    
@app.route('/export', methods=['GET'])
def export_csv():
    resumes = load_data()

    for r in resumes:
        r['score'] = calculate_score(r)
        r['recommendation'] = get_recommendation(r['score'])

    # Write CSV as string first
    csv_string_io = io.StringIO()
    writer = csv.DictWriter(csv_string_io, fieldnames=[
        'name', 'email', 'skills', 'education', 'experience',
        'projects', 'certifications', 'score', 'recommendation'
    ])
    writer.writeheader()
    writer.writerows(resumes)

    # Convert string to bytes
    csv_bytes_io = io.BytesIO()
    csv_bytes_io.write(csv_string_io.getvalue().encode('utf-8'))
    csv_bytes_io.seek(0)

    return send_file(
        csv_bytes_io,
        mimetype='text/csv',
        as_attachment=True,
        download_name='resumes_export.csv'
    )


if __name__ == '__main__':
    app.run(debug=True)

