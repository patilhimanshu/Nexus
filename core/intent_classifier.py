import requests
def detect_intent(question):
    system_prompt = f"""Classify the following question into exactly one of these categories:
- casual: greetings, small talk, emotions
- general: coding or tech questions not related to a specific project
- mixed: contains both greeting and project related content
- project: specific questions about the user's project

Reply with ONLY one word. No explanation. No punctuation.

Question: {question}"""
    response = requests.post("http://localhost:11434/api/generate", json={"model": "gemma3", "prompt": system_prompt, "stream" : False})
    answer = response.json()["response"]
    return answer


def build_context(intent, full_context, summary):
    base_identity = "You are Nexus, a smart modular AI workspace assistant designed to help developers manage their projects, files, and workflows.If you dont know something, dont hallucinate, say clearly what you do not know and possibly ask user for more data"

    if intent == "casual":
        personality = "You now have a fun,sarcastic, highly energetic and positive personality towards the user. Use different emojis to express yourself, and try to cheer up the user"
        system_prompt = f"""{base_identity}, Personality: {personality}"""
        return system_prompt

    elif intent == "general":
        personality = "You have a professional but user-friendly personality. Use different emojis to express yourself, and try to be helpful towards the user"
        system_prompt = f"""{base_identity}, Personality: {personality}"""
        return system_prompt

    elif intent == "mixed":
        personality = "You have a fun and professional personality. Be cheerful and help the user with the given context.Use professional emojis or understand the user's mood and answer accordingly"
        system_prompt = f"""{base_identity}, Personality: {personality}, Summary: {summary}"""
        return system_prompt

    elif intent == "project":
        personality = "You have a very professional personality and deeply focused in helping the user with the given context. Use the context wisely and answer user's questions accordingly. Use emojis to express yourself sometimes"
        context = full_context
        system_prompt = f"""{base_identity}, Personality: {personality}, Project Context: {context}"""
        return system_prompt

    else:
        return base_identity

