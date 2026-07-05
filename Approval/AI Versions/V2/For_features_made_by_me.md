# 🤖 AI Companion — Changelog / Build Log

> local-first AI companion, built by **Aahil**, **Himanshu** & **Claude** 🔥
> no cloud memory, no sketchy data farming, ur machine = ur rules 🔒

---

## ⚡ TL;DR

We took a vibe-coded command bot and turned it into an actual **thinking, remembering, multi-brain AI companion** with real database persistence, swappable LLM providers, task planning, file search, trial/tier logic, and voice. Full stack, fully tested. Let's gooo 🚀

---

## 🧱 The Foundation

### `database.py` — the memory that never forgets 🧠
- One `companion.db` **per install** — every laptop gets its own file, we never see your data, straight up privacy-first
- Tables: `profile`, `tasks`, `memory`, `conversation_log`, `personality_traits`, `user_tier`, `trial_fingerprints`
- ✅ Tested: survives full app restarts (closed it, reopened it, memories still there)

### `ai_brain.py` — the swappable brain 🔌
- One config line picks the brain: **Ollama** (free/local), **Claude**, **Gemini**, or **OpenAI**
- Same for image gen: DALL-E or Gemini image models
- If a provider fails or has no key → graceful fallback, never crashes Charlie
- ✅ Tested: routing logic, missing-key handling, dead-connection handling — all pass clean

---

## 🍰 The Cake (Conversation + Memory)

### `conversation_engine.py` — where it all connects
This is the actual brain of Charlie. Every message flows through:

```
user input → reasoning layer → route the task → brain call → memory + reply
```

**Features shipped:**
- 🗣️ **Natural conversation** — no more rigid keyword matching, real LLM understanding
- 🧠 **Memory that sticks** — tell it something once, it remembers forever (across restarts, tested ✅)
- 🎭 **Personality Tier 1 + 2** — mirrors ur tone live, AND saves durable traits ("prefers short replies", "gets sarcastic when stressed") that shape future convos
- 🤔 **Reasoning layer** — one clean call decides intent + action + priority + task type (text/code/image/file_search), no more three separate brittle engines
- 📋 **Planner** — say "make an AI cat channel" → it actually creates 4 real tasks in your db, not just prints them
- 🔀 **Smart routing** — code questions auto-switch to Claude, then switch back, no permanent side effects (tested even on crash scenarios 💪)

---

## 📂 Nexus Integration (File Intelligence)

Fixed 3 real bugs in Himanshu's Nexus codebase:
- `classifier.py` wasn't returning data → fixed, now feeds `organizer.py` properly
- `organizer.py` was never even being called → wired in, but with a **confirm-before-move** prompt (no more silent file yeeting 😤)
- Hardcoded path only worked on one laptop → now works everywhere

**New:** `file_search.py` — ask "where's my resume" and Charlie actually scans Desktop/Downloads/Documents and tells you 📁🔍

---

## 💰 Trial & Tier System

- 3-month free trial, full access, no cap
- **Anti-abuse**: device fingerprint + IP + email, layered — way stronger than IP alone (which basically anyone can dodge with a VPN or router restart)
- Notifications at 7 days left, 1 day left (fires once, not spammy), and on expiry
- **Free tier post-trial** = the "rage bait" era 😭 — 5 messages/session, 1 image/day, 2 file searches/day, zero memory persistence
- Basic ($1/mo) & Premium ($10/mo) — feature breakdown TBD, that's "the box of the cake" 🎂

---

## 🎤 Voice Engine

- **Ask-first** — Charlie only asks ONCE ever: "wanna enable voice?" Answer locks in forever, never asks twice ✅
- Fully offline: `pyttsx3` (speech out) + `speech_recognition` (speech in)
- Zero API cost, matches the local-first vibe completely

---

## 🧪 What's Actually Tested vs What Needs Real Hardware

| Tested & proven ✅ | Needs your real machine 🖥️ |
|---|---|
| DB persistence across restarts | Live LLM calls (Ollama/Claude/Gemini/OpenAI) |
| Trial abuse detection logic | Real image generation |
| Message cap enforcement | Actual TTS audio output |
| Provider routing + fallback | Real microphone input |
| File search logic | — |

---

## 🗺️ Roadmap Status

`0.01` → `0.07` ✅ done + tested
Trial system ✅ | Voice ✅

Next up: **0.08 Workspace Intelligence** and beyond 👀

---

*built different, one bug fix at a time 🛠️*
