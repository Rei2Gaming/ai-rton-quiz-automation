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
# Using the Data Source ID which is required for collection-based databases
NOTION_DATABASE_ID = "2e1404b2-ae9a-800a-a9bd-000b72449352"

def update_notion(data):
    if not NOTION_API_KEY:
        return {"error": "Notion API Key not set"}
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    score = int(data.get('score', 0))
    category = "Ainda Não (<15)"
    if score >= 28:
        category = "Estás Pronto (28+)"
    elif score >= 15:
        category = "Quase Lá (15-27)"

    # Map form answers to Notion select options
    respostas = data.get('respostas', {})
    
    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Nome": { "title": [{ "text": { "content": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip() or data.get('nome', 'Sem Nome') } }] },
            "Sobrenome": { "rich_text": [{ "text": { "content": data.get('lastName', '') } }] },
            "Empresa": { "rich_text": [{ "text": { "content": data.get('companyName', '') } }] },
            "Cargo": { "rich_text": [{ "text": { "content": data.get('jobTitle', '') } }] },
            "Email": { "email": data.get('email') if data.get('email') else None },
            "WhatsApp": { "rich_text": [{ "text": { "content": data.get('whatsapp', '') } }] },
            "Score Total": { "number": score },
            "Categoria Resultado": { "select": { "name": category } },
            "Bloqueio Atual": { "select": { "name": respostas.get('q1', '') } } if respostas.get('q1') else None,
            "Objetivo Principal Site": { "select": { "name": respostas.get('q3', '') } } if respostas.get('q3') else None,
            "Tipo de Solução Desejada": { "select": { "name": respostas.get('q4', '') } } if respostas.get('q4') else None,
            "Escopo Claro": { "select": { "name": respostas.get('q5', '') } } if respostas.get('q5') else None,
            "Tem Conteúdo Pronto": { "select": { "name": respostas.get('q6', '') } } if respostas.get('q6') else None,
            "Tem Visão Clara": { "select": { "name": respostas.get('q7', '') } } if respostas.get('q7') else None,
            "SEO Importante": { "select": { "name": respostas.get('q11', '') } } if respostas.get('q11') else None,
            "Hora Consultoria Agendada": { "rich_text": [{ "text": { "content": data.get('consultationTime', '') } }] }
        }
    }
    
    # Clean up None values
    payload["properties"] = {k: v for k, v in payload["properties"].items() if v is not None}
    
    if data.get('consultationDate'):
        try:
            # Ensure date is in YYYY-MM-DD format
            date_str = data.get('consultationDate')
            payload["properties"]["Data Consultoria Agendada"] = {
                "date": { "start": date_str }
            }
        except:
            pass
            
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

@app.route('/submit', methods=['POST'])
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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({"status": "active", "message": "AI.rton Quiz Backend is running"}), 200
