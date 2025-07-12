from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import io
import csv
from io import StringIO
from flask import render_template_string
from xhtml2pdf import pisa


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

def generate_feedback(resume):
    feedback = []

    # If projects missing or empty
    if not resume.get("projects") or not resume["projects"].strip():
        feedback.append("⚠️ Add at least one project to showcase your work.")

    # If certifications missing
    if not resume.get("certifications") or not resume["certifications"].strip():
        feedback.append("📜 Include certifications to boost credibility.")

    # If experience missing
    if not resume.get("experience") or not resume["experience"].strip():
        feedback.append("🧑‍💼 Add internships or part-time experience.")

    # If skills too few
    if not resume.get("skills") or len(resume["skills"]) < 3:
        feedback.append("💡 Add at least 3 skills relevant to your role.")

    # If education is blank
    if not resume.get("education") or not resume["education"].strip():
        feedback.append("🎓 Mention your education background.")

    # Default message if everything good
    return feedback if feedback else ["✅ Your resume looks well-prepared!"]


@app.route('/submit', methods=['POST'])
def submit_resume():
    data = request.get_json()

    data['score'] = calculate_score(data)
    data['recommendation'] = get_recommendation(data['score'])
    data['feedback'] = generate_feedback(data)
    
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
            r['feedback'] = generate_feedback(r)

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


@app.route('/resume/<email>', methods=["DELETE"])
def delete_resume(email):
    resumes = load_data()

    for i, r in enumerate(resumes):
        if "email" in r and r["email"] == email:
            removed = resumes.pop(i)
            save_data(resumes)
            return jsonify({"message": f"✅ Deleted: {removed.get('name', 'Unknown')}"})
    
    return jsonify({"error": "❌ Resume not found or invalid structure."}), 404


@app.route('/resume/<email>', methods=['PUT'])
def update_resume(email):
    resumes = load_data()
    updated = request.get_json()

    for i, r in enumerate(resumes):
        if r.get("email") == email:
            # Replace and recalculate
            resumes[i].update(updated)
            resumes[i]['score'] = calculate_score(resumes[i])
            resumes[i]['recommendation'] = get_recommendation(resumes[i]['score'])
            resumes[i]['feedback'] = generate_feedback(resumes[i])

            save_data(resumes)
            return jsonify({"message": f"✅ Updated resume for {updated['name']}"}), 200

    return jsonify({"error": "Resume not found"}), 404


@app.route('/export', methods=['GET'])
def export_csv():
    resumes = load_data()

    for r in resumes:
        r['score'] = calculate_score(r)
        r['recommendation'] = get_recommendation(r['score'])
        r['feedback'] = " | ".join(generate_feedback(r))


    # Write CSV as string first
    csv_string_io = io.StringIO()
    writer = csv.DictWriter(csv_string_io, fieldnames=[
        'name', 'email', 'skills', 'education', 'experience',
        'projects', 'certifications', 'score', 'recommendation', 'feedback'
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

@app.route('/download-pdf/<email>', methods=['GET'])
def download_pdf(email):
    resumes = load_data()
    resume = next((r for r in resumes if r['email'] == email), None)

    if not resume:
        return jsonify({"error": "Resume not found"}), 404

    html_template = f"""
    <html>
    <body>
        <h1>{resume['name']}</h1>
        <p><strong>Email:</strong> {resume['email']}</p>
        <p><strong>Skills:</strong> {', '.join(resume['skills'])}</p>
        <p><strong>Education:</strong> {resume['education']}</p>
        <p><strong>Experience:</strong> {resume['experience']}</p>
        <p><strong>Projects:</strong> {resume['projects']}</p>
        <p><strong>Certifications:</strong> {resume['certifications']}</p>
        <p><strong>Score:</strong> {resume['score']}%</p>
        <p><strong>Recommendation:</strong> {resume['recommendation']}</p>
        <p><strong>Feedback:</strong> <br>{"<br>".join(resume.get("feedback", []))}</p>
    </body>
    </html>
    """

    pdf_bytes = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_template, dest=pdf_bytes)

    if pisa_status.err:
        return jsonify({"error": "Failed to generate PDF"}), 500

    pdf_bytes.seek(0)
    return send_file(
        pdf_bytes,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{resume['name']}_resume.pdf"
    )


if __name__ == '__main__':
    app.run(debug=True)

