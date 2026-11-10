from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"
MODELS_URL = "https://huggingface.co/api/models"
SUPPORTED_SORTS = {"downloads", "likes", "trending"}
# Hugging Face API sort keys
SORT_KEYS = {"downloads": "downloads", "likes": "likes", "trending": "trendingScore"}
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


def hf_model_search(query: str = "", sort: str = "downloads", task: str = "", max_results: int = 5) -> dict[str, Any]:
    """Tìm model trên Hugging Face Hub (public API, keyless).

    - query rỗng / không phải chuỗi -> error dict, không gọi mạng
    - sort ngoài {downloads, likes, trending} -> error dict
    - task (tuỳ chọn) lọc theo pipeline_tag, vd "text-generation"
    - max_results sai kiểu / < 1 -> mặc định 5; > 20 -> giới hạn 20
    """
    try:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(sort, str) or sort.strip().lower() not in SUPPORTED_SORTS:
            raise ValueError(f"sort must be one of {sorted(SUPPORTED_SORTS)}")
        sort = sort.strip().lower()
        limit = _clamp_limit(max_results)
        params: dict[str, Any] = {"search": query.strip(), "sort": SORT_KEYS[sort], "direction": -1, "limit": limit}
        if isinstance(task, str) and task.strip():
            params["pipeline_tag"] = task.strip()

        response = requests.get(MODELS_URL, headers={"User-Agent": USER_AGENT}, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("unexpected response shape from Hugging Face API")
        items = []
        for model in data[:limit]:
            model_id = model.get("id") or model.get("modelId") or ""
            items.append({
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}" if model_id else "",
                "source": "huggingface.co",
                "summary": f"{model.get('pipeline_tag') or 'unknown task'} · {model.get('downloads') or 0} downloads · {model.get('likes') or 0} likes",
                "task": model.get("pipeline_tag"),
                "downloads": model.get("downloads"),
                "likes": model.get("likes"),
            })
        return {"tool": "hf_model_search", "query": query.strip(), "sort": sort, "item_count": len(items), "items": items}
    except Exception as exc:
        return err("hf_model_search", exc)
