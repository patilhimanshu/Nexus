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
import trial_manager as tm
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
# 0.05 — REASONING LAYER (intent + action + priority, ONE call)
# ------------------------------------------------------
# This is NOT three separate engines. It's one focused brain call
# that reasons through all three questions at once, then returns
# clean structured output (JSON) that our Python code can act on.
# Running it BEFORE the main reply means the conversational reply
# never has to also produce machine-parseable output — it can just
# focus on sounding like Charlie.

REASONING_PROMPT = """You analyze a single user message and classify it.
Reply with ONLY a JSON object, nothing else, no explanation, no markdown
fences. Use exactly this shape:

{"intent": "...", "action": "...", "priority": "...", "task_type": "..."}

intent must be one of: question, task, memory, research, conversation
action is a short phrase describing what should happen (e.g. "answer
directly", "create a task", "save as memory", "search the web", "just chat")
priority must be one of: low, medium, high
task_type must be one of: text, code, image, file_search
  - "code" if the user wants code written, explained, or debugged
  - "image" if the user wants a picture/image/drawing generated
  - "file_search" if the user is asking where a file is, or wants to
    find a file/folder on their computer
  - "text" for everything else (default)

Examples:
User: "remind me to submit the assignment by tomorrow night, it's worth 30% of my grade"
{"intent": "task", "action": "create a task with a due date", "priority": "high", "task_type": "text"}

User: "lol what's up"
{"intent": "conversation", "action": "reply casually", "priority": "low", "task_type": "text"}

User: "write me a python function to sort a list"
{"intent": "task", "action": "write code", "priority": "low", "task_type": "code"}

User: "generate an image of a cat wearing sunglasses"
{"intent": "task", "action": "generate an image", "priority": "low", "task_type": "image"}

User: "where is my physics PDF"
{"intent": "question", "action": "search for file", "priority": "low", "task_type": "file_search"}

User: "find my resume"
{"intent": "question", "action": "search for file", "priority": "low", "task_type": "file_search"}"""


def reason_about_message(user_message):
    """
    Returns a dict like {"intent": "task", "action": "create a task",
    "priority": "high", "task_type": "code"}. Falls back to safe
    defaults if the brain returns something unparseable — a malformed
    JSON response should never crash the whole conversation turn.
    """
    import json

    raw = brain.get_response(REASONING_PROMPT, [], user_message)

    try:
        result = json.loads(raw.strip())
        # validate shape, don't just trust the brain blindly
        if not all(k in result for k in ("intent", "action", "priority", "task_type")):
            raise ValueError("missing expected keys")
        if result["priority"] not in ("low", "medium", "high"):
            result["priority"] = "medium"
        if result["task_type"] not in ("text", "code", "image", "file_search"):
            result["task_type"] = "text"
        return result
    except (json.JSONDecodeError, ValueError):
        # safe fallback — treat as ordinary low-priority text conversation
        return {"intent": "conversation", "action": "reply normally", "priority": "low", "task_type": "text"}


# ------------------------------------------------------
# TASK ROUTER — picks the right provider/path based on task_type
# ------------------------------------------------------

def route_task(reasoning, user_message):
    """
    Reads reasoning["task_type"] and decides what kind of work this
    turn actually needs:
      - "image": skip text reply, call get_image()
      - "code": temporarily switch provider to Claude, restore after
      - "file_search": call Nexus find_file(), return matches
      - "text" (default): no provider switch, normal text reply

    Returns a dict the caller inspects to know which shape it got.
    This function does NOT call the brain itself.
    """
    import re
    task_type = reasoning.get("task_type", "text")

    if task_type == "image":
        image_result = brain.get_image(user_message)
        return {"type": "image", "result": image_result}

    if task_type == "file_search":
        # Strip filler phrases to get a clean search query.
        # "where is my physics PDF" -> "physics PDF"
        query = user_message.lower()
        for filler in ["where is my", "where is", "find my", "find",
                       "locate my", "locate", "search for", "look for",
                       "can you find", "do you know where"]:
            query = query.replace(filler, "")
        query = query.strip().strip("?").strip()

        from nexus_fixed.core.file_search import find_file
        matches = find_file(query)
        return {"type": "file_search", "query": query, "matches": matches}

    if task_type == "code":
        return {"type": "text", "provider_override": "claude"}

    return {"type": "text", "provider_override": None}


# ------------------------------------------------------
# 0.06 — PLANNER
# ------------------------------------------------------
# Triggered whenever reasoning["intent"] == "task". This is its own
# focused call (not folded into 0.05) because deciding "is this one
# task or does it secretly need breaking into steps" deserves the
# model's full attention on just that question, separate from intent
# classification, same lesson as Tier 2 and the reasoning layer.
#
# If the goal is simple ("buy milk"), the planner creates exactly
# ONE task and stops. If it's a real multi-step goal ("make an AI
# cat channel"), it breaks it into ordered subtasks and creates all
# of them as real rows in companion.db via db.create_task().

PLANNER_PROMPT = """A user stated something they want to get done.
Decide if this is a SIMPLE single task, or a multi-step GOAL that
needs breaking into subtasks.

Reply with ONLY a JSON object, nothing else, no markdown fences.

For a simple task, use this shape:
{"is_goal": false, "tasks": [{"title": "...", "priority": "low|medium|high"}]}

For a multi-step goal, break it into 3-6 ordered subtasks:
{"is_goal": true, "tasks": [{"title": "...", "priority": "low|medium|high"}, ...]}

Examples:
User: "buy milk"
{"is_goal": false, "tasks": [{"title": "Buy milk", "priority": "low"}]}

User: "make an AI cat channel"
{"is_goal": true, "tasks": [
  {"title": "Research AI cat content niche", "priority": "medium"},
  {"title": "Create channel logo", "priority": "medium"},
  {"title": "Create channel banner", "priority": "low"},
  {"title": "Script and upload first video", "priority": "high"}
]}"""


def plan_task(user_message):
    """
    Calls the brain to decompose the task, then ACTUALLY creates
    every resulting subtask as a real row in companion.db via
    db.create_task(). Returns the list of created task dicts.

    Falls back to creating one plain task with the raw user message
    as the title if the brain's output is unparseable — a malformed
    plan should still result in SOMETHING useful getting saved,
    not silently nothing.
    """
    import json

    raw = brain.get_response(PLANNER_PROMPT, [], user_message)

    try:
        plan = json.loads(raw.strip())
        tasks_to_create = plan.get("tasks", [])
        if not tasks_to_create:
            raise ValueError("no tasks in plan")
    except (json.JSONDecodeError, ValueError):
        tasks_to_create = [{"title": user_message, "priority": "medium"}]

    created = []
    for task in tasks_to_create:
        title = task.get("title", "Untitled task")
        priority = task.get("priority", "medium")
        if priority not in ("low", "medium", "high"):
            priority = "medium"

        task_id = db.create_task(title=title, priority=priority)
        created.append({"id": task_id, "title": title, "priority": priority})

    return created


# ------------------------------------------------------
# THE ACTUAL CONVERSATION LOOP
# ------------------------------------------------------

def handle_message(user_message):
    """
    The core function. Takes one user message, returns Charlie's
    reply, and handles all the memory/trait/reasoning/planning side
    effects. This is what Charlie's main loop calls instead of the
    old detect_intent().

    Returns (reply, reasoning) for text turns, or
    (image_result_dict, reasoning) for image turns — the caller
    needs to check reasoning["task_type"] to know which shape it got.

    Tier gate runs FIRST — if the user's on free tier and hit their
    session message cap, nothing else executes. No wasted brain
    calls on a message that's getting blocked anyway. 🚫
    """
    allowed, block_reason = tm.can_send_message()
    if not allowed:
        return block_reason, {"intent": "blocked", "action": "none",
                                "priority": "low", "task_type": "text"}

    tm.increment_session_messages()
    db.log_message("user", user_message)

    reasoning = reason_about_message(user_message)
    routing = route_task(reasoning, user_message)

    if routing["type"] == "image":
        allowed_img, block_msg = tm.can_use_image_gen()
        if not allowed_img:
            return block_msg, reasoning
        tm.increment_daily_image_count()

        # Image turns skip memory/trait extraction — that's a
        # text-conversation concept, not an image-generation one.
        db.log_message("assistant", f"[generated image for: {user_message}]")
        return routing["result"], reasoning

    if routing["type"] == "file_search":
        allowed_fs, block_msg = tm.can_use_file_search()
        if not allowed_fs:
            return block_msg, reasoning
        tm.increment_daily_file_search_count()

        query = routing["query"]
        matches = routing["matches"]

        if not matches:
            reply = f"I searched Desktop, Downloads, and Documents for '{query}' but couldn't find anything. It might be somewhere else on your PC, or the filename could be slightly different."
        elif len(matches) == 1:
            reply = f"Found it! 📂 {matches[0]}"
        else:
            paths = "\n".join(f"  - {m}" for m in matches[:5])
            reply = f"Found {len(matches)} match(es) for '{query}':\n{paths}"
            if len(matches) > 5:
                reply += f"\n  ...and {len(matches) - 5} more."

        db.log_message("assistant", reply)
        return reply, reasoning

    # 0.06 Planner — runs whenever the reasoning layer says this is
    # a task, BEFORE the conversational reply, so Charlie's actual
    # response can reference what just got created ("added 4 tasks
    # for your cat channel") instead of being unaware of it.
    created_tasks = None
    if reasoning["intent"] == "task":
        created_tasks = plan_task(user_message)

    system_prompt = build_system_prompt()
    if created_tasks:
        task_list = "\n".join(f"- {t['title']} ({t['priority']})" for t in created_tasks)
        system_prompt += f"\n\nYou just created these task(s) in the task manager:\n{task_list}\nMention this naturally in your reply."

    recent = db.get_recent_messages(limit=10)
    history = [{"role": m["role"], "content": m["content"]} for m in recent]

    # Temporarily override the provider for this one call if routing
    # says so (e.g. code tasks go to Claude), then restore it — other
    # parts of the app shouldn't be silently affected by one routing
    # decision made for a single message.
    original_provider = brain.ACTIVE_PROVIDER
    if routing["provider_override"]:
        brain.ACTIVE_PROVIDER = routing["provider_override"]

    try:
        raw_reply = brain.get_response(system_prompt, history, user_message)
    finally:
        brain.ACTIVE_PROVIDER = original_provider

    clean_reply, memory_to_save = extract_memory_tag(raw_reply)

    if memory_to_save:
        db.save_memory(memory_to_save)

    trait = extract_trait(user_message, clean_reply)
    if trait:
        db.save_trait(trait)

    db.log_message("assistant", clean_reply)
    return clean_reply, reasoning


# ------------------------------------------------------
# SIMPLE TERMINAL LOOP — proves the engine works end to end
# ------------------------------------------------------

if __name__ == "__main__":
    db.init_db()

    if db.is_first_run():
        print("Charlie: Hey, I'm Charlie. What should I call you? 👋")
        name = input("You: ").strip()
        db.set_profile_name(name)

        print("Charlie: One more thing — I need an email to set up your free trial. 📧")
        email = input("Email: ").strip()

        is_abuse, reason = tm.check_trial_abuse(email)
        if is_abuse:
            print(f"Charlie: Looks like a trial's already been used on this "
                  f"{'device' if reason == 'device' else reason}. "
                  f"You're starting on the free tier instead. 😬")
            tm.set_tier("free")
        else:
            tm.start_trial(email)
            print(f"Charlie: Nice to meet you, {name}! 🎉 Your 3-month free trial "
                  f"just started — full access, no limits. Let's get it. 🚀")
    else:
        # returning user — check for trial notifications every startup
        notif = tm.check_trial_notifications()
        if notif:
            print(f"Charlie: {notif}")

    tm.reset_session_message_count()  # fresh message cap every new session

    profile = db.get_profile()
    print(f"Charlie: What's up, {profile['name']}? ✨")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("Charlie: See you later!")
            break

        reply, reasoning = handle_message(user_input)

        if reasoning.get("task_type") == "image":
            if "error" in reply:
                print("Charlie: Couldn't generate that image —", reply["error"])
            elif "image_url" in reply:
                print("Charlie: Here's your image:", reply["image_url"])
            elif "image_base64" in reply:
                print("Charlie: Generated an image (base64 data, length:", len(reply["image_base64"]), "chars)")
        else:
            # covers text, code, file_search — all return a plain string
            print("Charlie:", reply)
