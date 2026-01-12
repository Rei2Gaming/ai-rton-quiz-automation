from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import subprocess
import os

app = Flask(__name__)
CORS(app)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    print(f"Received submission: {data}")
    
    # Save data to a temporary file
    temp_file = "/tmp/submission.json"
    with open(temp_file, 'w') as f:
        json.dump(data, f)
    
    # Run the handler script in the background
    subprocess.Popen(["python3", "/home/ubuntu/form_handler.py", temp_file])
    
    return jsonify({"status": "success", "message": "Submission received and processing"}), 200

if __name__ == '__main__':
    app.run(port=5000)
