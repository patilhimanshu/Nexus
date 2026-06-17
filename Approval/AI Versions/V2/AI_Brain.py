# ======================================================
# ===================== AI BRAIN =========================
# ======================================================
# Everything LLM-related in one file: config, routing, and all
# provider implementations (text + image). Same swappable-brain
# design as before, just merged so you're not jumping between
# files in your editor. Scroll down to find what you need:
#
#   1. CONFIG               - pick the active text/image provider here
#   2. INTERFACE             - get_response(), called by Charlie
#   3. OLLAMA PROVIDER       - free, local, no key
#   4. CLAUDE PROVIDER       - cloud, needs real API key
#   5. GEMINI PROVIDER       - cloud, needs real API key
#   6. OPENAI PROVIDER       - cloud, needs real API key
#   7. IMAGE INTERFACE       - get_image(), separate from text
#   8. OPENAI IMAGE (DALL-E) - cloud, needs real API key
#   9. GEMINI IMAGE          - cloud, needs real API key

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

# ---- Image generation providers (separate from text above) ----
# task_type "image" routes here instead of the text providers.
# Same rule: real metered API keys only, never a subscription login.

ACTIVE_IMAGE_PROVIDER = "openai"  # "openai" (DALL-E) | "gemini"

OPENAI_IMAGE_MODEL = "dall-e-3"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"

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


# ======================================================
# 7. IMAGE GENERATION INTERFACE \u2014 separate from text above
# ======================================================

def get_image(prompt):
    """
    The ONE function Charlie calls for image generation, same pattern
    as get_response() above but for images instead of text. Routes to
    whichever provider is set in ACTIVE_IMAGE_PROVIDER.

    Returns: dict with either {"image_url": "..."} or {"error": "..."}.
    Never raises — image generation failures shouldn't crash Charlie
    any more than a text brain failure should.
    """
    providers = {
        "openai": _generate_image_openai,
        "gemini": _generate_image_gemini,
    }

    if ACTIVE_IMAGE_PROVIDER not in providers:
        raise ValueError(
            f"Unknown image provider '{ACTIVE_IMAGE_PROVIDER}'. "
            f"Valid options: {list(providers.keys())}"
        )

    try:
        return providers[ACTIVE_IMAGE_PROVIDER](prompt)
    except Exception as e:
        return {"error": f"{ACTIVE_IMAGE_PROVIDER} image generation failed \u2014 {e}"}


# ======================================================
# 8. OPENAI IMAGE PROVIDER (DALL-E) \u2014 needs real metered API key
# ======================================================
# Costs real money PER IMAGE, not per token \u2014 check OpenAI's current
# pricing before generating in bulk. This is NOT the same key tier as
# free Ollama usage; be deliberate about testing this live.

def _generate_image_openai(prompt):
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "No OpenAI API key set. Get one at platform.openai.com "
            "(image generation costs money per image, separate from text pricing)"
        )

    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
        json={"model": OPENAI_IMAGE_MODEL, "prompt": prompt, "n": 1, "size": "1024x1024"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return {"image_url": data["data"][0]["url"]}


# ======================================================
# 9. GEMINI IMAGE PROVIDER \u2014 needs real metered API key
# ======================================================
# Gemini's image model returns base64-encoded image bytes inline,
# NOT a hosted URL like DALL-E does \u2014 different enough that Charlie's
# code calling this needs to handle both shapes differently.

def _generate_image_gemini(prompt):
    if not GEMINI_API_KEY:
        raise RuntimeError("No Gemini API key set. Get one at aistudio.google.com")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_IMAGE_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )

    response = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()

    parts = data["candidates"][0]["content"]["parts"]
    for part in parts:
        if "inlineData" in part:
            return {"image_base64": part["inlineData"]["data"]}

    raise RuntimeError("Gemini response contained no image data")
