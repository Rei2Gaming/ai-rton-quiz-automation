from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# Add the current directory to sys.path so we can import form_handler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import form_handler

app = Flask(__name__)
CORS(app)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        print(f"Received submission: {data}")
        
        # Run the handler logic directly instead of using subprocess
        # This is necessary for Vercel Serverless Functions
        result = form_handler.process_submission(data)
        
        return jsonify({
            "status": "success", 
            "message": "Submission processed",
            "details": result
        }), 200
    except Exception as e:
        print(f"Error processing submission: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Vercel requires the app to be named 'app'
# and it will handle the routing based on vercel.json
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({"status": "active", "message": "AI.rton Quiz Backend is running"}), 200
