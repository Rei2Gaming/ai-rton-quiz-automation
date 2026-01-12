import json
import sys
import os
from datetime import datetime, timedelta
import subprocess

def call_mcp_tool(server, tool, input_data):
    # Some servers might require specific handling or just work better via shell
    # Use double quotes for the JSON input to avoid issues with single quotes in the data
    input_json = json.dumps(input_data).replace("'", "'\\''")
    if server == "google-calendar":
        # Google Calendar MCP might have issues with the cli tool call directly in some environments
        # Let's try to use the full path or a different approach if needed, but first let's check the error again.
        # The error says "must be invoked via shell tool call", which is what I'm doing.
        pass
    cmd = f"manus-mcp-cli tool call {tool} --server {server} --input '{input_json}'"
    # Use shell=True and ensure the environment is correct
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=os.environ)
    if result.returncode != 0:
        print(f"Error calling {tool} on {server}: {result.stderr}")
        return None
    try:
        # The output might be a path to a JSON file or the JSON itself
        output = result.stdout.strip()
        if "saved to:" in output:
            path = output.split("saved to:")[1].strip().split("\n")[0]
            with open(path, 'r') as f:
                return json.load(f)
        if "Tool execution result:" in output:
            json_str = output.split("Tool execution result:")[1].strip()
            return json.loads(json_str)
        return json.loads(output)
    except:
        # If it's not JSON, just return the raw output
        return result.stdout.strip()

def handle_submission(data):
    # 1. Update Notion
    # Using the correct data_source_id found from fetch
    notion_parent = {"data_source_id": "2e1404b2-ae9a-800a-a9bd-000b72449352"}
    
    # Map score to category
    score = int(data.get('score', 0))
    category = "Ainda Não (<15)"
    if score >= 28:
        category = "Estás Pronto (28+)"
    elif score >= 15:
        category = "Quase Lá (15-27)"

    notion_properties = {
        "Nome": f"{data.get('firstName', '')} {data.get('lastName', '')}",
        "Sobrenome": data.get('lastName', ''),
        "Empresa": data.get('companyName', ''),
        "Cargo": data.get('jobTitle', ''),
        "Email": data.get('email', ''),
        "WhatsApp": data.get('whatsapp', ''),
        "Score Total": score,
        "Categoria Resultado": category,
        "Público Alvo": data.get('publico_alvo', ''),
        "Diferenciador": data.get('diferenciador', ''),
        "date:Data de Submissão:start": datetime.now().strftime("%Y-%m-%d"),
        "date:Data de Submissão:is_datetime": 0,
        "Hora Consultoria Agendada": data.get('consultationTime', '')
    }
    
    if data.get('consultationDate'):
        notion_properties["date:Data Consultoria Agendada:start"] = data.get('consultationDate')
        notion_properties["date:Data Consultoria Agendada:is_datetime"] = 0

    print("Updating Notion...")
    notion_result = call_mcp_tool("notion", "notion-create-pages", {
        "parent": notion_parent,
        "pages": [{"properties": notion_properties}]
    })
    print(f"Notion Result: {notion_result}")

    # 2. Create Brevo Contact (via Zapier MCP)
    print("Creating Brevo contact via Zapier MCP...")
    brevo_input = {
        "email": data.get('email', ''),
        "Attribute__COLON____SPACE__NOME_AIRTON": data.get('firstName', ''),
        "Attribute__COLON____SPACE__SOBRENOME_AIRTON": data.get('lastName', ''),
        "Attribute__COLON____SPACE__EMPRESA_PROFISSIONAL_AIRTON": data.get('companyName', ''),
        "Attribute__COLON____SPACE__CARGO_PROFISSAO_AIRTON": data.get('jobTitle', ''),
        "Attribute__COLON____SPACE__NUMERO_WHATSAPP_AIRTON": data.get('whatsapp', ''),
        "instructions": "Add or update contact in Brevo with the provided details.",
        "output_hint": "id"
    }
    brevo_result = call_mcp_tool("zapier", "brevo_add_or_update_contact", brevo_input)
    print(f"Brevo Result: {brevo_result}")
    # Since I don't have a direct Brevo MCP, I'll use the Zapier Webhook provided in the HTML
    # or I can try to use Zapier MCP if I can add the tool. 
    # But the user already has a Zapier Webhook URL in the HTML.
    # I will assume the Zapier Webhook handles Brevo.
    
    # 3. Set Google Calendar Reminder
    if data.get('consultationDate') and data.get('consultationTime'):
        try:
            start_dt_str = f"{data['consultationDate']}T{data['consultationTime']}:00"
            # Assuming UTC for simplicity or user's local time
            start_dt = datetime.fromisoformat(start_dt_str)
            end_dt = start_dt + timedelta(hours=1)
            
            calendar_event = {
                "summary": f"Consultoria: {data.get('firstName')} {data.get('lastName')}",
                "description": f"Empresa: {data.get('companyName')}\nEmail: {data.get('email')}\nWhatsApp: {data.get('whatsapp')}\nScore: {score}",
                "start_time": f"{data['consultationDate']}T{data['consultationTime']}:00Z",
                "end_time": (start_dt + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reminders": [30, 60]
            }
            print("Creating Google Calendar event...")
            # Use a direct shell call for google-calendar as it seems to be picky
            input_json = json.dumps({"events": [calendar_event]})
            cmd = f"manus-mcp-cli tool call google_calendar_create_events --server google-calendar --input '{input_json}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print(f"Calendar Result: {result.stdout}")
        except Exception as e:
            print(f"Error creating calendar event: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
            handle_submission(data)
