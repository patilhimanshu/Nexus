# ======================================================
# ===================== AI BRAIN =========================
# ======================================================
# Everything LLM-related in one file: config, routing, and all
# four provider implementations. Same swappable-brain design as
# before, just merged so you're not jumping between files in
# your editor. Scroll down to find what you need:
#
#   1. CONFIG          - pick the active provider here
#   2. INTERFACE        - get_response(), called by Charlie
#   3. OLLAMA PROVIDER  - free, local, no key
#   4. CLAUDE PROVIDER  - cloud, needs real API key
#   5. GEMINI PROVIDER  - cloud, needs real API key
#   6. OPENAI PROVIDER  - cloud, needs real API key

import requests


# ======================================================
# 1. CONFIG
# ======================================================
# Change ACTIVE_PROVIDER and nothing else in this file needs to
# change. That one line is the entire "swap the brain" mechanism.

ACTIVE_PROVIDER = "ollama"  # "ollama" | "claude" | "gemini" | "openai"

# ---- Ollama (free, local, no key needed) ----
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"  # change to whatever you've pulled, e.g. "mistral"

# ---- Cloud providers: REAL METERED API KEYS ONLY ----
# Never put a personal ChatGPT Plus / Claude Pro / Gemini subscription
# login here \u2014 that's against every provider's terms of service for
# automated/app access. These must be proper pay-per-token API keys.
#
# Get keys from:
#   Claude  -> https://console.anthropic.com
#   Gemini  -> https://aistudio.google.com
#   OpenAI  -> https://platform.openai.com

CLAUDE_API_KEY = ""
CLAUDE_MODEL = "claude-sonnet-4-6"

GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-2.5-flash"

OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o-mini"

MAX_RESPONSE_TOKENS = 300
REQUEST_TIMEOUT_SECONDS = 30


# ======================================================
# 2. INTERFACE \u2014 Charlie only ever calls this function
# ======================================================

def get_response(system_prompt, conversation_history, user_message):
    """
    The ONE function Charlie's Conversation Engine calls.

    system_prompt: string describing Charlie's personality + available actions
    conversation_history: list of {"role": "user"/"assistant", "content": "..."}
    user_message: the latest thing the user typed

    Returns: plain string reply from whichever provider is active in
    ACTIVE_PROVIDER above. Charlie's code never needs to know which
    provider is running \u2014 that's the whole point of this design.
    """
    providers = {
        "ollama": _generate_ollama,
        "claude": _generate_claude,
        "gemini": _generate_gemini,
        "openai": _generate_openai,
    }

    if ACTIVE_PROVIDER not in providers:
        raise ValueError(
            f"Unknown provider '{ACTIVE_PROVIDER}'. Valid options: {list(providers.keys())}"
        )

    try:
        return providers[ACTIVE_PROVIDER](system_prompt, conversation_history, user_message)
    except Exception as e:
        # Never let a network/API failure crash the whole app.
        return f"[Brain error: {ACTIVE_PROVIDER} failed \u2014 {e}]"


# ======================================================
# 3. OLLAMA PROVIDER \u2014 free, local, no API key
# ======================================================
# Requires Ollama installed and running (https://ollama.com)
# with a model pulled, e.g. `ollama pull llama3.2`

def _generate_ollama(system_prompt, conversation_history, user_message):
    messages = [{"role": "system", "content": system_prompt}]
    for turn in conversation_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"].strip()


# ======================================================
# 4. CLAUDE PROVIDER \u2014 needs real metered API key
# ======================================================

def _generate_claude(system_prompt, conversation_history, user_message):
    if not CLAUDE_API_KEY:
        raise RuntimeError(
            "No Claude API key set. Get one at console.anthropic.com "
            "(costs money per token, unlike Ollama)"
        )

    messages = []
    for turn in conversation_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": MAX_RESPONSE_TOKENS,
            "system": system_prompt,
            "messages": messages,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"].strip()


# ======================================================
# 5. GEMINI PROVIDER \u2014 needs real metered API key
# ======================================================

def _generate_gemini(system_prompt, conversation_history, user_message):
    if not GEMINI_API_KEY:
        raise RuntimeError("No Gemini API key set. Get one at aistudio.google.com")

    # Gemini has no separate "system" role in the basic API \u2014
    # fold the system prompt into the first turn instead.
    contents = [{"role": "user", "parts": [{"text": system_prompt}]}]
    contents.append({"role": "model", "parts": [{"text": "Understood."}]})

    for turn in conversation_history:
        role = "model" if turn["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": turn["content"]}]})

    contents.append({"role": "user", "parts": [{"text": user_message}]})

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    response = requests.post(
        url,
        json={"contents": contents, "generationConfig": {"maxOutputTokens": MAX_RESPONSE_TOKENS}},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


# ======================================================
# 6. OPENAI PROVIDER \u2014 needs real metered API key
# ======================================================

def _generate_openai(system_prompt, conversation_history, user_message):
    if not OPENAI_API_KEY:
        raise RuntimeError("No OpenAI API key set. Get one at platform.openai.com")

    messages = [{"role": "system", "content": system_prompt}]
    for turn in conversation_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={"model": OPENAI_MODEL, "messages": messages, "max_tokens": MAX_RESPONSE_TOKENS},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
