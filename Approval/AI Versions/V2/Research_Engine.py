# ======================================================
# ================ RESEARCH ENGINE (0.09) =================
# ======================================================
# Wikipedia only, for now — zero API cost, matches the local-first
# philosophy. No separate "does this need research" LLM call: we
# just TRY a Wikipedia lookup first, and cleanly fall back to a
# normal brain reply if nothing good comes back. Simpler and more
# robust than asking the reasoning layer to guess in advance.

import wikipedia


def try_research(query):
    """
    Attempts a Wikipedia lookup for the given query. Returns a
    summary string on success, or None if nothing usable was found —
    the caller (conversation_engine.handle_message) should fall back
    to a normal brain reply when this returns None.

    Handles Wikipedia's three real failure modes explicitly:
      - DisambiguationError: query matches multiple possible topics
      - PageError: no article exists for this query at all
      - Anything else (network issues, library errors): fail safe
    """
    try:
        summary = wikipedia.summary(query, sentences=3, auto_suggest=True)
        return summary.strip()

    except wikipedia.exceptions.DisambiguationError as e:
        # Query is ambiguous (e.g. "Mercury" -> planet or element or
        # Roman god). Try the FIRST suggested option automatically
        # rather than giving up — most of the time the top option is
        # actually what the user meant.
        if e.options:
            try:
                summary = wikipedia.summary(e.options[0], sentences=3, auto_suggest=False)
                return summary.strip()
            except Exception:
                return None
        return None

    except wikipedia.exceptions.PageError:
        return None  # no article exists, let the brain answer normally

    except Exception:
        # Network failure, library quirk, whatever — never let a
        # research failure crash the conversation. Silent fallback.
        return None
