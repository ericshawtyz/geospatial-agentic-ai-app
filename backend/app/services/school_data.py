"""School data lookup service with fuzzy name matching.

Loads school records from data/schools.json at import time and provides
a similarity-based search over school names using difflib (stdlib).
"""

import json
import logging
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Resolve path: try repo-root data/ first, then backend/data/ (for Docker)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_PATH = _REPO_ROOT / "data" / "schools.json"
if not _DATA_PATH.exists():
    # In Docker, the file is copied to /app/data/schools.json
    _DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "schools.json"

# Pre-load all school records at import time (~337 records, ~6MB)
_schools: list[dict[str, Any]] = []
_school_names_upper: list[str] = []  # parallel list for matching


def _load() -> None:
    global _schools, _school_names_upper
    if not _DATA_PATH.exists():
        logger.warning("School data file not found: %s", _DATA_PATH)
        return
    with open(_DATA_PATH, encoding="utf-8") as f:
        _schools = json.load(f)
    _school_names_upper = [
        r.get("school_name", "").upper().strip() for r in _schools
    ]
    logger.info("Loaded %d school records from %s", len(_schools), _DATA_PATH)


_load()


def search_school(query: str, threshold: float = 0.5) -> dict[str, Any] | None:
    """Find the best-matching school by name using fuzzy similarity.

    Args:
        query: School name to search for (handles typos, short forms, etc.)
        threshold: Minimum similarity ratio (0-1) to accept a match.

    Returns:
        Dict with ``school`` (the full record) and ``similarity`` (float),
        or None if no match exceeds the threshold.
    """
    if not _schools:
        return None

    query_upper = query.upper().strip()
    best_score = 0.0
    best_idx = -1

    for i, name in enumerate(_school_names_upper):
        # Fast check: exact match
        if query_upper == name:
            return {"school": _schools[i], "similarity": 1.0}

        # Substring containment boost: require at least 5 chars to avoid
        # short queries like "RI" matching every name containing those letters
        if len(query_upper) >= 5 and (query_upper in name or name in query_upper):
            score = 0.85
        else:
            score = SequenceMatcher(None, query_upper, name).ratio()

        if score > best_score:
            best_score = score
            best_idx = i

    if best_score >= threshold and best_idx >= 0:
        return {"school": _schools[best_idx], "similarity": round(best_score, 3)}

    return None
