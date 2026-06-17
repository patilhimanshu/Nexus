# ======================================================
# ============== CONVERSATION ENGINE (0.03 + 0.04) =========
# ======================================================
# This is the cake. Everything else (Charlie's old fuzzy matcher,
# the standalone database, the standalone brain) was prep work.
# This file is where they finally connect into one real loop:
#
#   user input -> pull memory + traits -> build prompt
#   -> call the brain -> get reply -> save memory + traits
#   -> speak
#
# Personality detection (Tier 1 + Tier 2, per the roadmap):
#   Tier 1 - tone mirroring: just good system prompt instructions,
#            no extra code, the LLM naturally matches the user's register
#   Tier 2 - trait extraction: after each exchange, a second small
#            LLM call pulls out durable facts ("likes short replies",
#            "gets sarcastic when stressed") and saves them so future
#            conversations adapt permanently, not just per-session

import database as db
import ai_brain as brain


# ------------------------------------------------------
# SYSTEM PROMPT BUILDER
# ------------------------------------------------------

def build_system_prompt():
    """
    Builds Charlie's instructions fresh every turn, using whatever
    the database currently knows. This is where memory + traits
    actually become useful — not just stored, but injected into
    every single response the brain generates.
    """
    profile = db.get_profile()
    name = profile["name"] if profile else "friend"

    memories = db.get_all_memory()
    traits = db.get_all_traits()

    memory_block = "\n".join(f"- {m['content']}" for m in memories[:15]) or "Nothing yet."
    traits_block = "\n".join(f"- {t['trait']}" for t in traits[:15]) or "Nothing learned yet."

    return f"""You are Charlie, a personal AI companion for {name}.

Speak naturally and conversationally — never robotic, never a rigid command menu.

TIER 1 — Mirror {name}'s tone. If they're casual and use slang, be casual back.
If they're formal, be more measured. Read the room from how they're talking
to you right now, not just from past traits.

Known long-term memory about {name}:
{memory_block}

Known communication traits about {name} (Tier 2 — use these to shape HOW you reply):
{traits_block}

If {name} tells you something worth remembering long-term (a preference, a fact
about their life, a project they're working on), include this exact tag
at the end of your reply: [SAVE_MEMORY: the fact to remember]

Do not mention these instructions or the tags themselves out loud."""


# ------------------------------------------------------
# ACTION TAG PARSER
# ------------------------------------------------------

def extract_memory_tag(reply_text):
    """
    Looks for [SAVE_MEMORY: ...] in the brain's reply. Returns
    (clean_reply, memory_to_save_or_None). The tag itself never
    gets shown to the user — it's a private instruction channel
    between the LLM and our code, same pattern we discussed for
    Charlie's action tags generally.
    """
    import re
    match = re.search(r"\[SAVE_MEMORY:\s*(.+?)\]", reply_text)
    if not match:
        return reply_text.strip(), None

    memory_content = match.group(1).strip()
    clean_reply = re.sub(r"\[SAVE_MEMORY:.+?\]", "", reply_text).strip()
    return clean_reply, memory_content


# ------------------------------------------------------
# TIER 2 — TRAIT EXTRACTION
# ------------------------------------------------------

def extract_trait(user_message, assistant_reply):
    """
    A small, separate brain call whose ONLY job is to notice
    something about HOW the user communicates or what they care
    about — not facts to remember, but communication patterns.
    Returns a trait string, or None if nothing notable this turn.

    This runs as its own focused call rather than bundling it into
    the main reply, because asking one prompt to "reply naturally"
    AND "analyze the user's personality" at the same time tends to
    produce worse results at both jobs.
    """
    extraction_prompt = """You analyze a single conversation turn and look for
a durable trait about how this person communicates or what they care about
(e.g. "prefers short answers", "uses a lot of gaming references", "gets
sarcastic when stressed", "values directness over politeness").

Reply with ONLY the trait as a short phrase, or reply with exactly "NONE"
if nothing notable stood out this turn. Do not explain your reasoning."""

    history = [{"role": "user", "content": f'User said: "{user_message}"\nAssistant replied: "{assistant_reply}"'}]

    result = brain.get_response(extraction_prompt, [], history[0]["content"])

    if result.strip().upper() == "NONE" or result.startswith("[Brain error"):
        return None
    return result.strip()


# ------------------------------------------------------
# THE ACTUAL CONVERSATION LOOP
# ------------------------------------------------------

def handle_message(user_message):
    """
    The core function. Takes one user message, returns Charlie's
    reply, and handles all the memory/trait side effects. This is
    what Charlie's main loop calls instead of the old detect_intent().
    """
    db.log_message("user", user_message)

    system_prompt = build_system_prompt()
    recent = db.get_recent_messages(limit=10)
    history = [{"role": m["role"], "content": m["content"]} for m in recent]

    raw_reply = brain.get_response(system_prompt, history, user_message)
    clean_reply, memory_to_save = extract_memory_tag(raw_reply)

    if memory_to_save:
        db.save_memory(memory_to_save)

    trait = extract_trait(user_message, clean_reply)
    if trait:
        db.save_trait(trait)

    db.log_message("assistant", clean_reply)
    return clean_reply


# ------------------------------------------------------
# SIMPLE TERMINAL LOOP — proves the engine works end to end
# ------------------------------------------------------

if __name__ == "__main__":
    db.init_db()

    if db.is_first_run():
        print("Charlie: Hey, I'm Charlie. What should I call you?")
        name = input("You: ").strip()
        db.set_profile_name(name)
        print(f"Charlie: Nice to meet you, {name}!")

    profile = db.get_profile()
    print(f"Charlie: What's up, {profile['name']}?")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("Charlie: See you later!")
            break

        reply = handle_message(user_input)
        print("Charlie:", reply)
