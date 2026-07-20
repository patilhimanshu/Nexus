import requests
from dotenv import load_dotenv
import os
from config.models import INTENT_MODEL
from config.model_prompt import system_prompt_intent
from config.model_prompt import base_identity, casual_personality, general_personality, mixed_personality, context_personality
load_dotenv()

def detect_intent(question):

    system_prompt = system_prompt_intent.format(question = question)
    api_key = os.getenv("GROQ_API_KEY")
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": INTENT_MODEL,
            "messages": [{"role": "user", "content": system_prompt}]
        }
    )
    answer = response.json()["choices"][0]["message"]["content"]
    return answer


def build_context(intent, full_context, summary):

    if intent == "casual":
        system_prompt = f"""{base_identity}, Personality: {casual_personality}"""
        return system_prompt

    elif intent == "general":
        system_prompt = f"""{base_identity}, Personality: {general_personality}"""
        return system_prompt

    elif intent == "mixed":
        system_prompt = f"""{base_identity}, Personality: {mixed_personality}, Summary: {summary}"""
        return system_prompt

    elif intent == "project":
        system_prompt = f"""{base_identity}, Personality: {context_personality}, Project Context: {full_context}"""
        return system_prompt

    else:
        return base_identity

