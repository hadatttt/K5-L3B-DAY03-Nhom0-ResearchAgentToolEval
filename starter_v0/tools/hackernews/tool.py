from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"
SORT_ENDPOINTS = {
    "relevance": "https://hn.algolia.com/api/v1/search",
    "date": "https://hn.algolia.com/api/v1/search_by_date",
}
DEFAULT_MAX_RESULTS = 5
MAX_ALLOWED_RESULTS = 20


def _clamp_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_RESULTS
    if limit < 1:
        return DEFAULT_MAX_RESULTS
    return min(limit, MAX_ALLOWED_RESULTS)


def hackernews_search(query: str = "", sort: str = "relevance", max_results: int = 5) -> dict[str, Any]:
    """Tìm story trên Hacker News (Algolia HN Search API, keyless).

    - query rỗng / không phải chuỗi -> error dict, không gọi mạng
    - sort ngoài {relevance, date} -> error dict (tự normalize " Date " -> "date")
    - max_results sai kiểu / < 1 -> mặc định 5; > 20 -> giới hạn 20
    """
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(sort, str) or sort.strip().lower() not in SORT_ENDPOINTS:
            raise ValueError(f"sort must be one of {sorted(SORT_ENDPOINTS)}")
        sort = sort.strip().lower()
        limit = _clamp_limit(max_results)

        response = requests.get(
            SORT_ENDPOINTS[sort],
            headers={"User-Agent": USER_AGENT},
            params={"query": query.strip(), "tags": "story", "hitsPerPage": limit},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", [])[:limit]:
            story_id = hit.get("objectID") or ""
            discussion = f"https://news.ycombinator.com/item?id={story_id}" if story_id else ""
            items.append({
                "title": hit.get("title") or "",
                # Ask HN / Show HN text posts have no external url -> fall back to the HN thread.
                "url": hit.get("url") or discussion,
                "source": "news.ycombinator.com",
                "summary": f"{hit.get('points') or 0} points, {hit.get('num_comments') or 0} comments, by {hit.get('author') or 'unknown'}",
                "discussion_url": discussion,
                "date": hit.get("created_at"),
                "points": hit.get("points"),
                "num_comments": hit.get("num_comments"),
            })
        return {"tool": "hackernews_search", "query": query.strip(), "sort": sort, "item_count": len(items), "items": items}
    except Exception as exc:
        return err("hackernews_search", exc)
