from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import json
import os
import io
import csv
from xhtml2pdf import pisa

app = Flask(__name__)
CORS(app)

DATA_FILE = 'resumes.json'

# ---------------- Helper Functions ---------------- #

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

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

def generate_feedback(resume):
    feedback = []

    if not resume.get("projects") or not resume["projects"].strip():
        feedback.append("⚠️ Add at least one project to showcase your work.")

    if not resume.get("certifications") or not resume["certifications"].strip():
        feedback.append("📜 Include certifications to boost credibility.")

    if not resume.get("experience") or not resume["experience"].strip():
        feedback.append("🧑‍💼 Add internships or part-time experience.")

    if not resume.get("skills") or len(resume["skills"]) < 3:
        feedback.append("💡 Add at least 3 skills relevant to your role.")

    if not resume.get("education") or not resume["education"].strip():
        feedback.append("🎓 Mention your education background.")

    return feedback if feedback else ["✅ Your resume looks well-prepared!"]

# ---------------- Frontend Routes ---------------- #

@app.route('/')
def home():
    return "✅ Resume API is running."

@app.route('/form')
def resume_form():
    return render_template("index.html")

@app.route('/resumes')
def resumes_ui():
    return render_template("resume.html")

@app.route('/dashboard')
def dashboard_ui():
    return render_template("dashboard.html")

# ---------------- API Routes ---------------- #

@app.route('/submit', methods=['POST'])
def submit_resume():
    data = request.get_json()
    resumes = load_data()

    if any(r['email'] == data['email'] for r in resumes):
        return jsonify({"error": "⚠️ Email already exists. Please use a different email."}), 409

    data['score'] = calculate_score(data)
    data['recommendation'] = get_recommendation(data['score'])
    data['feedback'] = generate_feedback(data)

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
    summary = {"total": len(resumes), "strong": 0, "decent": 0, "needs_more": 0, "weak": 0}

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
        if r.get("email") == email:
            removed = resumes.pop(i)
            save_data(resumes)
            return jsonify({"message": f"✅ Deleted: {removed.get('name', 'Unknown')}"}), 200
    return jsonify({"error": "❌ Resume not found."}), 404

@app.route('/resume/<email>', methods=['PUT'])
def update_resume(email):
    resumes = load_data()
    updated = request.get_json()

    for i, r in enumerate(resumes):
        if r.get("email") == email:
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

    csv_string_io = io.StringIO()
    writer = csv.DictWriter(csv_string_io, fieldnames=[
        'name', 'email', 'skills', 'education', 'experience',
        'projects', 'certifications', 'score', 'recommendation', 'feedback'
    ])
    writer.writeheader()
    writer.writerows(resumes)

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
        <h1>{resume.get('name', '')}</h1>
        <p><strong>Email:</strong> {resume.get('email', '')}</p>
        <p><strong>Skills:</strong> {', '.join(resume.get('skills', []))}</p>
        <p><strong>Education:</strong> {resume.get('education', 'N/A')}</p>
        <p><strong>Experience:</strong> {resume.get('experience', 'N/A')}</p>
        <p><strong>Projects:</strong> {resume.get('projects', 'N/A')}</p>
        <p><strong>Certifications:</strong> {resume.get('certifications', 'N/A')}</p>
        <p><strong>Score:</strong> {resume.get('score', 0)}%</p>
        <p><strong>Recommendation:</strong> {resume.get('recommendation', 'N/A')}</p>
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

@app.route('/repair', methods=['GET'])
def repair_resumes():
    try:
        resumes = load_data()
        repaired = 0

        for r in resumes:
            changed = False
            if 'score' not in r:
                r['score'] = calculate_score(r)
                changed = True
            if 'recommendation' not in r:
                r['recommendation'] = get_recommendation(r['score'])
                changed = True
            if 'feedback' not in r:
                r['feedback'] = generate_feedback(r)
                changed = True

            if changed:
                repaired += 1

        if repaired > 0:
            save_data(resumes)
            print(f"✅ Auto-repaired {repaired} resume(s) on startup.")
        else:
            print("✅ No repair needed. All resumes are clean.")

    except Exception as e:
        print(f"❌ Error during resume repair: {str(e)}")

# ---------------- Launch App ---------------- #

if __name__ == '__main__':
    repair_resumes()
    port = int(os.environ.get("PORT", 5000))  # Read PORT from Render env
    app.run(host='0.0.0.0', port=port, debug=True)  # Bind to 0.0.0.0
