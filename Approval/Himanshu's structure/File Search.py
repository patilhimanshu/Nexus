import os


# Bug fix / new feature: "where is this file" search. Scans the
# folders someone's actually likely to have put a file in — Desktop,
# Downloads, Documents — rather than just the one folder Nexus
# watches for auto-organizing. This is what Charlie's Conversation
# Engine will call when the user asks "where is my resume" etc.

SEARCH_FOLDERS = [
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Documents"),
]


def find_file(query, max_results=10):
    """
    Searches Desktop, Downloads, and Documents for files whose name
    contains `query` (case-insensitive substring match). Returns a
    list of full paths, capped at max_results so a very common word
    doesn't return hundreds of matches.

    Skips folders that don't exist on this machine instead of
    crashing — not every OS/user has all three folders.
    """
    matches = []
    query_lower = query.lower()

    for folder in SEARCH_FOLDERS:
        if not os.path.exists(folder):
            continue

        for root, dirs, files in os.walk(folder):
            for name in files:
                if query_lower in name.lower():
                    matches.append(os.path.join(root, name))
                    if len(matches) >= max_results:
                        return matches

    return matches
