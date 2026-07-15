# ======================================================
# ================ KNOWLEDGE ENGINE (0.10) =================
# ======================================================
# Caches research findings from the Research Engine (0.09) so
# Charlie doesn't re-look-up the same topic every single time.
# Reuses the existing `memory` table with category="knowledge" —
# no new table needed, keeps the schema lean.
#
# FUZZY MATCHING: research queries rarely repeat word-for-word.
# "who was einstein", "einstein", and "tell me about einstein"
# should all hit the same cached result. Uses difflib's
# SequenceMatcher (same approach as old Charlie's fuzzy intent
# matching) rather than pulling in a heavier NLP dependency for
# something this small.
#
# Cache format stored in memory.content: "QUERY::ANSWER" — the
# query prefix is what gets fuzzy-matched against, everything
# after "::" is the actual cached research summary.

from difflib import SequenceMatcher
import database as db

CACHE_CATEGORY = "knowledge"
FUZZY_MATCH_THRESHOLD = 0.5

# Common question filler words that shouldn't count toward similarity —
# without stripping these, "who was einstein" vs "who was napoleon"
# scores HIGHER than "who was einstein" vs "tell me about einstein",
# because raw string comparison rewards shared filler ("who was")
# over the actual topic keyword. Stripping filler first fixes this.
FILLER_WORDS = {
    "who", "what", "where", "when", "why", "how", "is", "was", "are",
    "were", "the", "a", "an", "tell", "me", "about", "explain", "of",
    "on", "in", "to", "do", "you", "know", "can",
}


def _extract_keywords(text):
    """Strips filler words, returns the meaningful terms as a
    space-joined string for comparison."""
    words = [w for w in text.lower().split() if w not in FILLER_WORDS]
    return " ".join(words) if words else text.lower()


def _similarity(a, b):
    """
    Compares the MEANINGFUL keywords of two queries, not the raw
    strings. This is what fixes the bug where shared filler phrases
    ("who was") would outweigh the actual topic word in similarity.
    """
    return SequenceMatcher(None, _extract_keywords(a), _extract_keywords(b)).ratio()


def _parse_cache_entry(content):
    """
    Splits a stored "QUERY::ANSWER" string back into its parts.
    Returns (query, answer) or (None, None) if the format is
    somehow malformed (e.g. old memory entries without the
    knowledge format) — never crash on unexpected data.
    """
    if "::" not in content:
        return None, None
    query, _, answer = content.partition("::")
    return query, answer


def check_knowledge_cache(query):
    """
    Fuzzy-searches past cached research for something close enough
    to the current query. Returns the cached answer string, or None
    if nothing similar enough has been researched before.
    """
    all_memories = db.get_all_memory()
    knowledge_entries = [m for m in all_memories if m.get("category") == CACHE_CATEGORY]

    best_match = None
    best_score = 0.0

    for entry in knowledge_entries:
        cached_query, cached_answer = _parse_cache_entry(entry["content"])
        if cached_query is None:
            continue  # malformed entry, skip

        score = _similarity(query, cached_query)
        if score > best_score:
            best_score = score
            best_match = cached_answer

    if best_score >= FUZZY_MATCH_THRESHOLD:
        return best_match
    return None


def save_to_cache(query, answer):
    """
    Saves a research finding to the knowledge cache. Called after
    the Research Engine successfully finds something new — so the
    NEXT time someone asks something similar, it hits the cache
    instead of hitting Wikipedia again.
    """
    entry = f"{query}::{answer}"
    db.save_memory(entry, category=CACHE_CATEGORY)
