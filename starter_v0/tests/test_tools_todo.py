"""TODO CP3 (student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO CP3 (student): implement this test"


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    # Call clarify with response_type="choice" and 2 options.
    # Assert: options are returned unchanged, awaiting_user is True.
    pytest.skip(TODO)


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    # Items with section "A", "B", "A" -> markdown has exactly one "## A" and one "## B".
    pytest.skip(TODO)


def test_format_thread_numbers_items() -> None:
    # template="thread" -> lines start with "1/", "2/", ...
    pytest.skip(TODO)


def test_format_empty_items_does_not_crash() -> None:
    # items=None and items=[] -> item_count == 0, no exception.
    pytest.skip(TODO)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    # Set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, mock HTTP.
    # Assert: exactly one POST, URL contains the token, json has chat_id + text, status == "sent".
    pytest.skip(TODO)


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    pytest.skip(TODO)


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    # timeframe=None -> request body has no "time_range" key.
    pytest.skip(TODO)


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    # Mock {"data": {"markdown": "...", "metadata": {"title": "T", "sourceURL": "https://..."}}}
    # Assert title/url/source/summary in result["items"][0].
    pytest.skip(TODO)


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    pytest.skip(TODO)


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    # Mock {"timeline": [...]} with 1 item missing tweet_id and 6 valid items, limit=3.
    # Assert 3 items, and each url looks like https://x.com/<handle>/status/<id>.
    pytest.skip(TODO)


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    # Assert the request params carry the query and search_type ("Top" / "Latest").
    pytest.skip(TODO)


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    pytest.skip(TODO)


def test_policy_area_filter_only_returns_that_area() -> None:
    # policy_area="data_privacy" -> every result has policy_area == "data_privacy".
    pytest.skip(TODO)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # One policy file contains a quoted line that tries to give the assistant orders.
    # Query that section (source_citation) and assert: that line is in untrusted_text, NOT in facts.
    pytest.skip(TODO)


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

wiki_tool = TOOL_FUNCTIONS["wiki"]


def test_wiki_sends_expected_request_and_maps_results(fake_http) -> None:
    """Happy path: gọi MediaWiki search API và map kết quả về items chuẩn."""
    calls = fake_http(FakeResponse({"query": {"search": [
        {"title": "VinUni", "snippet": "<b>VinUni</b> là trường đại học &quot;tư thục&quot; tại Hà Nội"},
        {"title": "VinFast", "snippet": "<span>VinFast</span> là hãng xe điện"},
    ]}}))

    result = wiki_tool(query="VinUni", lang="vi", max_results=2)

    # Request gửi đi đúng endpoint MediaWiki với params chuẩn
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"
    assert calls[0]["params"]["srsearch"] == "VinUni"
    assert calls[0]["params"]["srlimit"] == 2
    assert calls[0]["params"]["list"] == "search"
    assert calls[0]["params"]["format"] == "json"
    # Kết quả map đúng: bỏ thẻ HTML, unescape entity, url chuẩn
    assert result["tool"] == "wiki_search"
    assert result["item_count"] == 2
    first = result["items"][0]
    assert first["title"] == "VinUni"
    assert first["url"] == "https://vi.wikipedia.org/wiki/VinUni"
    assert first["source"] == "vi.wikipedia.org"
    assert "<b>" not in first["summary"]
    assert '"tư thục"' in first["summary"]


def test_wiki_empty_or_bad_query_returns_error_dict_without_network(fake_http) -> None:
    """Model gửi query rỗng / sai kiểu -> error dict, không gọi mạng."""
    calls = fake_http(FakeResponse({"query": {"search": []}}))

    for bad in ["", "   ", None, 123]:
        result = wiki_tool(query=bad)
        assert result["error"] == "ValueError"
        assert "query" in result["message"]

    assert calls == []


def test_wiki_lang_outside_enum_returns_error_dict(fake_http) -> None:
    """lang ngoài {vi, en} -> error dict; lang hợp lệ nhưng viết xấu được normalize."""
    calls = fake_http(FakeResponse({"query": {"search": []}}))

    assert wiki_tool(query="X", lang="fr")["error"] == "ValueError"
    assert calls == []  # lang sai bị chặn trước khi gọi API

    # " VI " -> normalize thành "vi" rồi mới gọi
    wiki_tool(query="X", lang=" VI ")
    assert calls[0]["url"] == "https://vi.wikipedia.org/w/api.php"


def test_wiki_clamps_bad_max_results_to_valid_range(fake_http) -> None:
    """max_results sai kiểu / < 1 về mặc định 3; > 10 bị giới hạn về 10."""
    calls = fake_http(FakeResponse({"query": {"search": []}}))

    wiki_tool(query="AI", max_results=0)
    assert calls[0]["params"]["srlimit"] == 3

    wiki_tool(query="AI", max_results="5")  # model gửi số dạng chuỗi
    assert calls[1]["params"]["srlimit"] == 5

    wiki_tool(query="AI", max_results=99)
    assert calls[2]["params"]["srlimit"] == 10


def test_wiki_http_error_returns_error_dict_not_raise(fake_http) -> None:
    """HTTP 500 từ API -> error dict, không raise exception."""
    fake_http(FakeResponse(status_code=500))

    result = wiki_tool(query="VinUni")

    assert result["error"] == "HTTPError"
    assert result["tool"] == "wiki_search"
