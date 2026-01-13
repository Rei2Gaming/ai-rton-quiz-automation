import json
import sys
import os
from datetime import datetime, timedelta
import requests

# Notion Configuration
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = "2e1404b2-ae9a-800a-a9bd-000b72449352"

def process_submission(data):
    results = {}
    
    # 1. Update Notion
    try:
        results['notion'] = update_notion(data)
    except Exception as e:
        results['notion'] = f"Error: {str(e)}"

    # 2. Trigger Zapier (which handles Brevo and potentially Calendar)
    # The user already has a Zapier setup, so we should keep using it.
    try:
        results['zapier'] = trigger_zapier(data)
    except Exception as e:
        results['zapier'] = f"Error: {str(e)}"
        
    return results

def update_notion(data):
    # This requires the NOTION_API_KEY to be set in Vercel Environment Variables
    if not NOTION_API_KEY:
        return "Notion API Key not set in environment variables"
        
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

    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Nome": { "title": [{ "text": { "content": f"{data.get('firstName', '')} {data.get('lastName', '')}" } }] },
            "Sobrenome": { "rich_text": [{ "text": { "content": data.get('lastName', '') } }] },
            "Empresa": { "rich_text": [{ "text": { "content": data.get('companyName', '') } }] },
            "Cargo": { "rich_text": [{ "text": { "content": data.get('jobTitle', '') } }] },
            "Email": { "email": data.get('email', '') },
            "WhatsApp": { "rich_text": [{ "text": { "content": data.get('whatsapp', '') } }] },
            "Score Total": { "number": score },
            "Categoria Resultado": { "select": { "name": category } },
            "Público Alvo": { "rich_text": [{ "text": { "content": data.get('publico_alvo', '') } }] },
            "Diferenciador": { "rich_text": [{ "text": { "content": data.get('diferenciador', '') } }] },
            "Hora Consultoria Agendada": { "rich_text": [{ "text": { "content": data.get('consultationTime', '') } }] }
        }
    }
    
    if data.get('consultationDate'):
        payload["properties"]["Data Consultoria Agendada"] = {
            "date": { "start": data.get('consultationDate') }
        }
        
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def trigger_zapier(data):
    # Use the user's existing Zapier Webhook if they have one
    # For now, we'll return a placeholder as the user needs to provide the URL
    # or we can use the one previously identified if it's still valid.
    return "Zapier trigger logic would go here"
