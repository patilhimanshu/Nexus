# ======================================================
# ================= TRIAL MANAGER 🔐 ===================
# ======================================================
# Handles everything trial/tier related:
#
#   1. DEVICE FINGERPRINT  — hardware-tied ID, strongest signal
#   2. ABUSE CHECK         — fingerprint + IP + email layered check
#   3. TRIAL SETUP         — first-run trial initialization
#   4. TIER ENFORCEMENT    — what the user can/can't do per tier
#   5. LIMIT TRACKING      — session messages, daily image/search caps
#   6. LAST-DAY NOTIF      — fires once when trial is about to end
#
# Tier hierarchy:
#   "trial"   → full Premium access, 3 months free
#   "free"    → rage bait mode 😭 (5 msg/session, 1-2 daily uses)
#   "basic"   → $1/mo (details TBD — "the box of the cake")
#   "premium" → $10/mo (details TBD)

import os
import uuid
import socket
import hashlib
import urllib.request
from datetime import datetime, timezone, timedelta
import database as db


# ======================================================
# 1. DEVICE FINGERPRINT
# ======================================================
# Combines stable hardware/OS signals into one hash.
# Not unbreakable — a determined user could spoof these — but
# combined with IP + email it's a meaningfully high bar for
# casual trial abuse. Lives in a local file so it persists
# even if companion.db gets deleted and recreated.

FINGERPRINT_FILE = os.path.join(
    os.path.dirname(db.DB_PATH), "device.id"
)


def get_device_id():
    """
    Returns this installation's device fingerprint. Creates and
    caches it on first call. Combining multiple signals means
    changing one (like reinstalling the OS) doesn't automatically
    give a clean slate.
    """
    if os.path.exists(FINGERPRINT_FILE):
        with open(FINGERPRINT_FILE, "r") as f:
            return f.read().strip()

    # Build a fingerprint from stable machine signals
    signals = [
        str(uuid.getnode()),           # MAC address (hardware)
        os.environ.get("COMPUTERNAME", ""),    # Windows machine name
        os.environ.get("HOSTNAME", ""),        # Linux/Mac hostname
        os.environ.get("USERNAME", ""),        # OS username
        os.environ.get("USERPROFILE", ""),     # Windows user profile path
    ]
    raw = "|".join(signals)
    device_id = hashlib.sha256(raw.encode()).hexdigest()[:32]

    with open(FINGERPRINT_FILE, "w") as f:
        f.write(device_id)

    return device_id


def get_public_ip():
    """
    Gets the current public IP. Returns "unknown" gracefully if
    there's no internet connection — don't let an IP lookup failure
    block the app from starting.
    """
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=4) as r:
            return r.read().decode().strip()
    except Exception:
        return "unknown"


# ======================================================
# 2. ABUSE CHECK
# ======================================================

def check_trial_abuse(email):
    """
    Checks three layered signals against previously used trial data:
      1. Device fingerprint (strongest — hardware-tied)
      2. IP address (moderate — changes but not trivially)
      3. Email address (catches re-signup on fresh device/IP)

    Returns (is_abuse: bool, reason: str).
    Any single signal matching a past trial is enough to deny.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT device_id, ip_address, email FROM trial_fingerprints")
    past = cur.fetchall()
    conn.close()

    if not past:
        return False, ""

    device_id = get_device_id()
    public_ip = get_public_ip()

    for row in past:
        if row["device_id"] and row["device_id"] == device_id:
            return True, "device"
        if row["ip_address"] and row["ip_address"] == public_ip and public_ip != "unknown":
            return True, "ip"
        if row["email"] and row["email"].lower() == email.lower():
            return True, "email"

    return False, ""


def save_trial_fingerprint(email):
    """
    Saves the current device/IP/email combo so future installs can
    be checked against it. Called once when a new trial starts.
    """
    device_id = get_device_id()
    public_ip = get_public_ip()

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trial_fingerprints (device_id, ip_address, email, created_at)
        VALUES (?, ?, ?, ?)
    """, (device_id, public_ip, email.lower(),
          datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()


# ======================================================
# 3. TRIAL SETUP
# ======================================================

def start_trial(email):
    """
    Initializes the 3-month trial for a new install after passing
    the abuse check. Saves the fingerprint so future re-installs
    can be detected.
    """
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=90)  # 3 months

    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_tier (
            id, tier, trial_start, trial_end,
            notified_last_day, session_message_count,
            daily_image_count, daily_file_search_count,
            last_daily_reset
        )
        VALUES (1, 'trial', ?, ?, 0, 0, 0, 0, ?)
        ON CONFLICT(id) DO NOTHING
    """, (now.isoformat(), trial_end.isoformat(), now.date().isoformat()))
    conn.commit()
    conn.close()

    save_trial_fingerprint(email)


def get_tier_row():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_tier WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def set_tier(tier):
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user_tier SET tier = ? WHERE id = 1", (tier,))
    conn.commit()
    conn.close()


# ======================================================
# 4. TIER ENFORCEMENT
# ======================================================

TIER_LIMITS = {
    "free": {
        "session_messages": 5,
        "daily_images": 1,
        "daily_file_searches": 2,
        "memory_persistence": False,
        "context_resets_on_new_chat": True,
    },
    "trial": {
        "session_messages": None,   # unlimited
        "daily_images": None,
        "daily_file_searches": None,
        "memory_persistence": True,
        "context_resets_on_new_chat": False,
    },
    "basic": {
        "session_messages": None,   # TBD — "the box of the cake"
        "daily_images": None,
        "daily_file_searches": None,
        "memory_persistence": True,
        "context_resets_on_new_chat": False,
    },
    "premium": {
        "session_messages": None,   # TBD
        "daily_images": None,
        "daily_file_searches": None,
        "memory_persistence": True,
        "context_resets_on_new_chat": False,
    },
}


def get_current_tier():
    """
    Returns the user's current effective tier, automatically
    downgrading "trial" to "free" if the 90-day window has passed.
    """
    row = get_tier_row()
    if not row:
        return "free"  # no tier row = no trial was ever started

    if row["tier"] == "trial":
        trial_end = datetime.fromisoformat(row["trial_end"])
        if datetime.now(timezone.utc) > trial_end:
            set_tier("free")
            return "free"

    return row["tier"]


def can_send_message():
    """
    Returns (allowed: bool, reason: str).
    Checks the session message cap for free tier users.
    """
    tier = get_current_tier()
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    if limits["session_messages"] is None:
        return True, ""  # unlimited

    row = get_tier_row()
    count = row["session_message_count"] if row else 0

    if count >= limits["session_messages"]:
        return False, (
            f"🚫 You've hit the {limits['session_messages']}-message limit for this session.\n"
            f"Upgrade to Basic ($1/mo) to keep the conversation going — "
            f"or start a new session and explain yourself again from scratch. 💀"
        )
    return True, ""


def can_use_image_gen():
    """Returns (allowed: bool, reason: str) for image generation."""
    tier = get_current_tier()
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    if limits["daily_images"] is None:
        return True, ""

    row = get_tier_row()
    _reset_daily_counts_if_needed(row)
    row = get_tier_row()  # re-fetch after potential reset
    count = row["daily_image_count"] if row else 0

    if count >= limits["daily_images"]:
        return False, (
            f"🖼️ You've used your {limits['daily_images']} free image gen today. "
            f"Come back tomorrow, or upgrade to Basic ($1/mo) for unlimited. ✨"
        )
    return True, ""


def can_use_file_search():
    """Returns (allowed: bool, reason: str) for file search."""
    tier = get_current_tier()
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    if limits["daily_file_searches"] is None:
        return True, ""

    row = get_tier_row()
    _reset_daily_counts_if_needed(row)
    row = get_tier_row()
    count = row["daily_file_search_count"] if row else 0

    if count >= limits["daily_file_searches"]:
        return False, (
            f"🔍 Daily file search limit hit. "
            f"Upgrade to Basic ($1/mo) to search freely. 📂"
        )
    return True, ""


# ======================================================
# 5. LIMIT TRACKING — increment counters
# ======================================================

def increment_session_messages():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE user_tier
        SET session_message_count = session_message_count + 1
        WHERE id = 1
    """)
    conn.commit()
    conn.close()


def reset_session_message_count():
    """Call this at the start of each new chat session."""
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE user_tier SET session_message_count = 0 WHERE id = 1")
    conn.commit()
    conn.close()


def increment_daily_image_count():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE user_tier
        SET daily_image_count = daily_image_count + 1
        WHERE id = 1
    """)
    conn.commit()
    conn.close()


def increment_daily_file_search_count():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE user_tier
        SET daily_file_search_count = daily_file_search_count + 1
        WHERE id = 1
    """)
    conn.commit()
    conn.close()


def _reset_daily_counts_if_needed(row):
    """Resets daily counters if the date has rolled over."""
    if not row:
        return
    today = datetime.now(timezone.utc).date().isoformat()
    if row["last_daily_reset"] != today:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE user_tier
            SET daily_image_count = 0,
                daily_file_search_count = 0,
                last_daily_reset = ?
            WHERE id = 1
        """, (today,))
        conn.commit()
        conn.close()


# ======================================================
# 6. LAST-DAY NOTIFICATION
# ======================================================

def check_trial_notifications():
    """
    Returns a notification string if the trial is ending soon,
    or None if there's nothing to notify. Call this on startup.

    Fires once on the last day of the trial (not every hour —
    once is enough, spam is not the vibe 🙅).
    """
    row = get_tier_row()
    if not row or row["tier"] != "trial":
        return None

    trial_end = datetime.fromisoformat(row["trial_end"])
    now = datetime.now(timezone.utc)
    days_left = (trial_end - now).days

    if days_left <= 0:
        # trial just expired this session
        set_tier("free")
        return (
            "⏰ Your 3-month free trial just ended.\n"
            "You're now on the free tier — 5 messages per session, "
            "no memory, and the vibe is very limited 😬\n"
            "Upgrade to Basic ($1/mo) or Premium ($10/mo) to keep "
            "the full experience. 🚀"
        )

    if days_left <= 1 and not row["notified_last_day"]:
        # fire the last-day notification exactly once
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE user_tier SET notified_last_day = 1 WHERE id = 1"
        )
        conn.commit()
        conn.close()
        return (
            "⚠️ Last day of your free trial!\n"
            "Tomorrow your access drops to the free tier.\n"
            "Lock in Basic ($1/mo) or Premium ($10/mo) before it expires. 🔐"
        )

    if days_left <= 7:
        return (
            f"🕐 Heads up — your free trial ends in {days_left} day(s).\n"
            "Upgrade anytime to keep your memory, unlimited chat, "
            "and full feature access. 💎"
        )

    return None
