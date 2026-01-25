from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Notion Configuration
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
# Using the correct Database ID found via search
NOTION_DATABASE_ID = "2e1404b2-ae9a-803b-9dca-d434fcd37f23"

def update_notion(data):
    if not NOTION_API_KEY:
        return {"error": "Notion API Key not set"}
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    score = int(data.get("score", 0))
    category = "Ainda Não (<15)"
    if score >= 28:
        category = "Estás Pronto (28+)"
    elif score >= 15:
        category = "Quase Lá (15-27)"

    # Map form answers to Notion select options
    respostas = data.get("respostas", {})
    
    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Nome": { "title": [{ "text": { "content": f"{data.get("firstName", "")} {data.get("lastName", "")}".strip() or data.get("nome", "Sem Nome") } }] },
            "Sobrenome": { "rich_text": [{ "text": { "content": data.get("lastName", "") } }] },
            "Empresa": { "rich_text": [{ "text": { "content": data.get("companyName", "") } }] },
            "Cargo": { "rich_text": [{ "text": { "content": data.get("jobTitle", "") } }] },
            "Email": { "email": data.get("email") if data.get("email") else None },
            "WhatsApp": { "rich_text": [{ "text": { "content": data.get("whatsapp", "") } }] },
            "Score Total": { "number": score },
            "Categoria Resultado": { "select": { "name": category } },
            "Hora Consultoria Agendada": { "rich_text": [{ "text": { "content": data.get("consultationTime", "") } }] }
        }
    }
    
    # Clean up None values
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v is not None}
    
    if data.get("consultationDate"):
        try:
            # Ensure date is in YYYY-MM-DD format
            date_str = data.get("consultationDate")
            payload["properties"]["Data Consultoria Agendada"] = {
                "date": { "start": date_str }
            }
        except:
            pass
            
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        # Process Notion update
        notion_result = update_notion(data)
        
        return jsonify({
            "status": "success", 
            "message": "Submission processed",
            "notion": notion_result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return jsonify({"status": "active", "message": "AI.rton Quiz Backend is running"}), 200
