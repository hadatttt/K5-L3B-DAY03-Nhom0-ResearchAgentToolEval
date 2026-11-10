from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"
SEARCH_URL = "https://api.github.com/search/repositories"
SUPPORTED_SORTS = {"stars", "updated"}
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


def github_repo_search(query: str = "", sort: str = "stars", language: str = "", max_results: int = 5) -> dict[str, Any]:
    """Tìm repository open-source trên GitHub (REST search API, keyless, ~10 request/phút).

    - query rỗng / không phải chuỗi -> error dict, không gọi mạng
    - sort ngoài {stars, updated} -> error dict
    - language (tuỳ chọn) được thêm vào query dạng `language:<x>`
    - max_results sai kiểu / < 1 -> mặc định 5; > 20 -> giới hạn 20
    """
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(sort, str) or sort.strip().lower() not in SUPPORTED_SORTS:
            raise ValueError(f"sort must be one of {sorted(SUPPORTED_SORTS)}")
        sort = sort.strip().lower()
        limit = _clamp_limit(max_results)
        q = query.strip()
        if isinstance(language, str) and language.strip():
            q = f"{q} language:{language.strip()}"

        response = requests.get(
            SEARCH_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
            params={"q": q, "sort": sort, "order": "desc", "per_page": limit},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for repo in response.json().get("items", [])[:limit]:
            items.append({
                "title": repo.get("full_name") or "",
                "url": repo.get("html_url") or "",
                "source": "github.com",
                "summary": (repo.get("description") or "").strip(),
                "stars": repo.get("stargazers_count"),
                "language": repo.get("language"),
                "date": repo.get("updated_at"),
            })
        return {"tool": "github_repo_search", "query": q, "sort": sort, "item_count": len(items), "items": items}
    except Exception as exc:
        return err("github_repo_search", exc)
