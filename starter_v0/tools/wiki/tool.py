from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

SUPPORTED_LANGS = {"vi", "en"}
DEFAULT_MAX_RESULTS = 3
MAX_ALLOWED_RESULTS = 10


def wiki_search(query: str = "", lang: str = "vi", max_results: int = 3) -> dict[str, Any]:
    """Tra cứu Wikipedia: tìm bài theo từ khóa và trả về tiêu đề + link + đoạn tóm tắt.

    Keyless (API công khai của Wikimedia). Xử lý input xấu từ model:
    - query rỗng / không phải chuỗi -> error dict
    - lang ngoài {vi, en} -> error dict (tự normalize " VI " -> "vi")
    - max_results sai kiểu / < 1 -> dùng mặc định 3; > 10 -> giới hạn về 10
    """
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(lang, str) or lang.strip().lower() not in SUPPORTED_LANGS:
            raise ValueError(f"lang must be one of {sorted(SUPPORTED_LANGS)}")
        lang = lang.strip().lower()
        try:
            limit = int(max_results)
        except (TypeError, ValueError):
            limit = DEFAULT_MAX_RESULTS
        if limit < 1:
            limit = DEFAULT_MAX_RESULTS
        limit = min(limit, MAX_ALLOWED_RESULTS)

        response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            # Wikimedia chặn UA mặc định của python-requests (403) — cần UA mô tả.
            headers={"User-Agent": "AI20k-Day03-Research-Agent/1.0 (educational lab)"},
            params={
                "action": "query",
                "list": "search",
                "srsearch": query.strip(),
                "srlimit": limit,
                "format": "json",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        items = []
        for hit in data.get("query", {}).get("search", []):
            title = hit.get("title", "")
            snippet = html.unescape(re.sub(r"<[^>]+>", "", hit.get("snippet", "")))
            items.append({
                "title": title,
                "url": f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                "source": f"{lang}.wikipedia.org",
                "summary": snippet,
            })
        return {
            "tool": "wiki_search",
            "query": query.strip(),
            "lang": lang,
            "item_count": len(items),
            "items": items,
        }
    except Exception as exc:
        return err("wiki_search", exc)
