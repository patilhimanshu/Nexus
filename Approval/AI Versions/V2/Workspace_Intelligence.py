# ======================================================
# ============= WORKSPACE INTELLIGENCE (0.08) ============
# ======================================================
# Goes beyond "where is this file" (0.07) into actually understanding
# the workspace as a whole: duplicates, clutter, large files, and
# organization suggestions.
#
# Duplicate detection uses CONTENT HASHING, not filename matching —
# catches real duplicates even if renamed (e.g. "resume.pdf" and
# "resume_final_v2.pdf" being byte-identical). This is genuinely
# more useful than filename matching, but costs more to compute.
#
# PERFORMANCE NOTE: hashing full file content means reading every
# byte of every scanned file. On folders with large videos/installers
# this can be slow. Two mitigations built in:
#   1. Only hash files below a size ceiling by default (configurable)
#   2. Quick pre-filter by file SIZE first — files with a unique size
#      can't possibly be duplicates, so we skip hashing those entirely
#      and only hash files that share a size with at least one other

import os
import hashlib
from collections import defaultdict
from datetime import datetime, timezone

SEARCH_FOLDERS = [
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Documents"),
]

LARGE_FILE_THRESHOLD_MB = 500
HASH_SIZE_CEILING_MB = 2000  # don't hash anything bigger than this, too slow
CHUNK_SIZE = 65536  # read files in 64kb chunks, not all at once


def _hash_file(filepath):
    """
    Returns a SHA-256 hash of file content, or None if the file can't
    be read (permissions, file got deleted mid-scan, etc). Reads in
    chunks so a large file doesn't get loaded fully into memory at once.
    """
    try:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None


def _walk_all_files():
    """
    Yields (filepath, size_bytes) for every file across all search
    folders that exist on this machine. Skips folders that don't
    exist instead of crashing.
    """
    for folder in SEARCH_FOLDERS:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for name in files:
                filepath = os.path.join(root, name)
                try:
                    size = os.path.getsize(filepath)
                    yield filepath, size
                except OSError:
                    continue  # file vanished mid-scan, skip it


def find_duplicates():
    """
    Returns a list of duplicate groups: [{"hash": "...", "size_mb": ..,
    "files": [path1, path2, ...]}, ...]. Each group is a set of files
    that are byte-identical.

    Two-pass approach for speed:
      Pass 1: group files by SIZE (cheap, no reading required).
              Any size with only one file can't have a duplicate —
              skip hashing those entirely.
      Pass 2: within each size-group with 2+ files, hash the content
              and group by hash. Only actual duplicates survive.
    """
    size_groups = defaultdict(list)

    for filepath, size in _walk_all_files():
        if size == 0:
            continue  # empty files aren't meaningful duplicates
        if size > HASH_SIZE_CEILING_MB * 1024 * 1024:
            continue  # too big, skip for performance
        size_groups[size].append(filepath)

    hash_groups = defaultdict(list)
    for size, filepaths in size_groups.items():
        if len(filepaths) < 2:
            continue  # unique size, impossible to be a duplicate

        for filepath in filepaths:
            file_hash = _hash_file(filepath)
            if file_hash:
                hash_groups[file_hash].append(filepath)

    duplicates = []
    for file_hash, filepaths in hash_groups.items():
        if len(filepaths) >= 2:
            size_mb = round(os.path.getsize(filepaths[0]) / (1024 * 1024), 2)
            duplicates.append({
                "hash": file_hash,
                "size_mb": size_mb,
                "files": filepaths,
            })

    return duplicates


def find_large_files(threshold_mb=None):
    """
    Returns files at or above threshold_mb, sorted biggest first.
    If threshold_mb isn't passed, reads LARGE_FILE_THRESHOLD_MB fresh
    from the module at call time — NOT bound at function definition,
    so changing the module constant after import actually takes effect.
    """
    if threshold_mb is None:
        threshold_mb = LARGE_FILE_THRESHOLD_MB

    large = []
    for filepath, size in _walk_all_files():
        size_mb = size / (1024 * 1024)
        if size_mb >= threshold_mb:
            large.append({"path": filepath, "size_mb": round(size_mb, 2)})

    large.sort(key=lambda f: f["size_mb"], reverse=True)
    return large


def analyze_clutter():
    """
    Returns basic clutter stats per folder: total file count and
    total size. A high file count in Downloads specifically is a
    strong clutter signal — that folder is rarely organized by hand.
    """
    stats = {}
    for folder in SEARCH_FOLDERS:
        if not os.path.exists(folder):
            continue

        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(folder):
            for name in files:
                filepath = os.path.join(root, name)
                try:
                    total_size += os.path.getsize(filepath)
                    file_count += 1
                except OSError:
                    continue

        stats[os.path.basename(folder)] = {
            "file_count": file_count,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    return stats


def generate_suggestions():
    """
    Runs all three analyses and turns them into human-readable
    suggestion strings. This is what gets fed into Charlie's startup
    flow or an on-demand "how's my workspace" query.
    """
    suggestions = []

    duplicates = find_duplicates()
    if duplicates:
        total_wasted_mb = sum(d["size_mb"] * (len(d["files"]) - 1) for d in duplicates)
        suggestions.append(
            f"🗂️ Found {len(duplicates)} set(s) of duplicate files, "
            f"wasting about {round(total_wasted_mb, 1)}MB of space."
        )

    large_files = find_large_files()
    if large_files:
        suggestions.append(
            f"📦 You have {len(large_files)} file(s) over "
            f"{LARGE_FILE_THRESHOLD_MB}MB. Biggest: "
            f"{os.path.basename(large_files[0]['path'])} "
            f"({large_files[0]['size_mb']}MB)."
        )

    clutter = analyze_clutter()
    downloads_stats = clutter.get("Downloads")
    if downloads_stats and downloads_stats["file_count"] > 100:
        suggestions.append(
            f"📥 Your Downloads folder has {downloads_stats['file_count']} files "
            f"({downloads_stats['total_size_mb']}MB). Might be worth organizing."
        )

    return suggestions
