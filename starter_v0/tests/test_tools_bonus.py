"""Unit tests for the bonus tools written by Hà Văn Khánh Đạt: hackernews, github, hf_models.

Offline only: HTTP is mocked with `fake_http` (conftest blocks real network).
Each tool has: happy path (request + mapping), bad input from the model, failure path.
"""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

hackernews_tool = TOOL_FUNCTIONS["hackernews"]
github_tool = TOOL_FUNCTIONS["github"]
hf_models_tool = TOOL_FUNCTIONS["hf_models"]


# ---------------- hackernews ----------------

def test_hackernews_sends_expected_request_and_maps_results(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "101", "title": "LLM agents in prod", "url": "https://blog.example.com/agents",
         "author": "alice", "points": 320, "num_comments": 88, "created_at": "2026-11-01T10:00:00Z"},
        {"objectID": "102", "title": "Ask HN: agent eval?", "url": None,
         "author": "bob", "points": 12, "num_comments": 5, "created_at": "2026-11-02T10:00:00Z"},
    ]}))

    result = hackernews_tool(query=" LLM agents ", max_results=2)

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "LLM agents", "tags": "story", "hitsPerPage": 2}
    assert "User-Agent" in calls[0]["headers"]
    assert result["item_count"] == 2
    first, ask_hn = result["items"]
    assert first["url"] == "https://blog.example.com/agents"
    assert first["discussion_url"] == "https://news.ycombinator.com/item?id=101"
    assert first["summary"] == "320 points, 88 comments, by alice"
    # Ask HN has no external link -> falls back to the HN thread
    assert ask_hn["url"] == "https://news.ycombinator.com/item?id=102"


def test_hackernews_sort_date_uses_search_by_date_endpoint(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    result = hackernews_tool(query="Rust", sort=" Date ")

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert result["sort"] == "date"


def test_hackernews_bad_input_returns_error_dict_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))

    for bad in ({"query": ""}, {"query": "   "}, {"query": None}, {"query": "AI", "sort": "popular"}):
        result = hackernews_tool(**bad)
        assert result["tool"] == "hackernews_search"
        assert result["error"] == "ValueError"
    assert calls == []


def test_hackernews_clamps_bad_max_results(fake_http) -> None:
    for given, expected in (("abc", 5), (0, 5), (-3, 5), (999, 20), ("7", 7)):
        calls = fake_http(FakeResponse({"hits": []}))
        hackernews_tool(query="AI", max_results=given)
        assert calls[0]["params"]["hitsPerPage"] == expected


def test_hackernews_http_error_returns_error_dict_not_raise(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert hackernews_tool(query="AI")["error"] == "HTTPError"

    fake_http(requests.Timeout("timed out"))
    assert hackernews_tool(query="AI")["error"] == "Timeout"


# ---------------- github ----------------

def test_github_sends_expected_request_and_maps_results(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": [
        {"full_name": "org/agent-kit", "html_url": "https://github.com/org/agent-kit",
         "description": "  An agent framework  ", "stargazers_count": 1234,
         "language": "Python", "updated_at": "2026-11-09T00:00:00Z"},
    ]}))

    result = github_tool(query="agent framework", language="Python", max_results=3)

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "agent framework language:Python", "sort": "stars", "order": "desc", "per_page": 3}
    assert calls[0]["headers"]["Accept"] == "application/vnd.github+json"
    assert result["items"][0] == {
        "title": "org/agent-kit", "url": "https://github.com/org/agent-kit", "source": "github.com",
        "summary": "An agent framework", "stars": 1234, "language": "Python",
        "date": "2026-11-09T00:00:00Z",
    }


def test_github_without_language_keeps_plain_query_and_sort_updated(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": []}))

    github_tool(query="rag", sort="UPDATED", language="  ")

    assert calls[0]["params"]["q"] == "rag"
    assert calls[0]["params"]["sort"] == "updated"


def test_github_bad_input_returns_error_dict_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": []}))

    for bad in ({"query": ""}, {"query": 42}, {"query": "rag", "sort": "forks"}):
        result = github_tool(**bad)
        assert result["tool"] == "github_repo_search"
        assert result["error"] == "ValueError"
    assert calls == []


def test_github_rate_limit_returns_error_dict_not_raise(fake_http) -> None:
    fake_http(FakeResponse({"message": "API rate limit exceeded"}, status_code=403))
    result = github_tool(query="rag")
    assert result["error"] == "HTTPError"
    assert "403" in result["message"]


# ---------------- hf_models ----------------

def test_hf_models_sends_expected_request_and_maps_results(fake_http) -> None:
    calls = fake_http(FakeResponse([
        {"id": "Qwen/Qwen3-0.6B", "downloads": 2000, "likes": 50, "pipeline_tag": "text-generation"},
        {"modelId": "acme/tiny", "downloads": None, "likes": None, "pipeline_tag": None},
    ]))

    result = hf_models_tool(query="qwen", task="text-generation", max_results=2)

    assert calls[0]["url"] == "https://huggingface.co/api/models"
    assert calls[0]["params"] == {
        "search": "qwen", "sort": "downloads", "direction": -1, "limit": 2, "pipeline_tag": "text-generation",
    }
    first, second = result["items"]
    assert first["url"] == "https://huggingface.co/Qwen/Qwen3-0.6B"
    assert first["summary"] == "text-generation · 2000 downloads · 50 likes"
    # falls back to modelId and tolerates missing numbers
    assert second["title"] == "acme/tiny"
    assert second["summary"] == "unknown task · 0 downloads · 0 likes"


def test_hf_models_trending_maps_to_api_sort_key(fake_http) -> None:
    calls = fake_http(FakeResponse([]))

    hf_models_tool(query="whisper", sort="trending")

    assert calls[0]["params"]["sort"] == "trendingScore"
    assert "pipeline_tag" not in calls[0]["params"]


def test_hf_models_bad_input_returns_error_dict_without_network(fake_http) -> None:
    calls = fake_http(FakeResponse([]))

    for bad in ({"query": ""}, {"query": ["qwen"]}, {"query": "qwen", "sort": "newest"}):
        result = hf_models_tool(**bad)
        assert result["tool"] == "hf_model_search"
        assert result["error"] == "ValueError"
    assert calls == []


def test_hf_models_unexpected_shape_or_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse({"error": "something changed"}))
    assert hf_models_tool(query="qwen")["error"] == "ValueError"

    fake_http(FakeResponse(status_code=500))
    assert hf_models_tool(query="qwen")["error"] == "HTTPError"
