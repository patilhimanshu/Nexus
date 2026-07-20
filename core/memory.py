import os
from config.models import SUMMARY_MODEL
import requests
import json
from datetime import datetime
from config.model_prompt import summary_prompt
from dotenv import load_dotenv
load_dotenv()
def summarize_and_save(conversation_history, project_path):
    date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    prompt = summary_prompt.format(conversation_history=conversation_history)
    api_key = os.getenv('GROQ_API_KEY')
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model" :SUMMARY_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    answer = response.json()["choices"][0]["message"]["content"]
    if os.path.exists("memory.json"):
        with open("memory.json", "r") as f:
            data = json.load(f)
    else:
        data = {"sessions": []}
        with open ("memory.json", "w") as f:
            json.dump(data, f)
    data["sessions"].append({
        "date": date,
        "project": project_path,
        "summary": answer
    })
    with open("memory.json", "w") as f:
        json.dump(data, f, indent=4)
def load_memory():
    if os.path.exists("memory.json"):
        with open("memory.json", "r") as f:
            data = json.load(f)
            sessions = data.get("sessions", [])
            recent = sessions[-3:]
            return "\n".join([f"[{s['date']}] {s['summary']}" for s in recent])
    return ""


