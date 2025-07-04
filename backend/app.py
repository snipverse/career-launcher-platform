import logging

logging.basicConfig(filename='api_log.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
data_store = []

@app.route('/')
def home():
    return "Welcome to Resume API"

@app.route('/resume', methods=['GET'])
def get_resume():
    return jsonify({"name": "Sachin", "skills": ["Python", "Flask"]})

@app.route('/submit', methods=['POST'])
def submit_data():
    data = request.get_json()
    data_store.append(data)
    logging.info(f"Data received: {data}")
    return jsonify({
        "received": data,
        "total_submissions": len(data_store)
    })

if __name__ == '__main__':
    app.run(debug=True)
