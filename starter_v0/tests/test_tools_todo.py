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


clarify_tool = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send_tool = TOOL_FUNCTIONS["send"]
lookup_tool = TOOL_FUNCTIONS["lookup"]
fetch_tool = TOOL_FUNCTIONS["fetch"]
timeline_tool = TOOL_FUNCTIONS["timeline"]
social_search_tool = TOOL_FUNCTIONS["social_search"]
policy_tool = TOOL_FUNCTIONS["policy"]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    options = ["Tin tức trên web", "Tweet trên X"]
    result = clarify_tool(question="Bạn muốn nguồn nào?", response_type="choice", options=options)

    assert result["response_type"] == "choice"
    assert result["options"] == options
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]
    lines = markdown.splitlines()

    assert lines.count("## A") == 1
    assert lines.count("## B") == 1
    # both A items are grouped under the single "## A" heading, before "## B"
    a_block = markdown.split("## B")[0]
    assert "a1" in a_block and "a2" in a_block


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"Tin {i}", "url": f"https://example.com/{i}"} for i in range(3)]
    markdown = format_tool(items=items, template="thread")["markdown"]
    posts = markdown.split("\n\n")

    assert [post.split(" ")[0] for post in posts] == ["1/", "2/", "3/"]
    assert posts[0].startswith("1/ Tin 0")


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        for template in ("brief", "bullets", "thread", "daily_ai_vn", "sections"):
            result = format_tool(items=empty, template=template)
            assert result["item_count"] == 0
            assert isinstance(result["markdown"], str)


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "123:fake-token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-1001"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))

    result = send_tool(text="Bản tin AI", confirmed=True)

    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))

    result = lookup_tool(query="AI", timeframe=None)

    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI"
    assert result["items"] == []


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Nội dung bài",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post"},
    }}))

    result = fetch_tool(url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://www.example.com/post"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-test"
    assert result["items"][0] == {
        "title": "T",
        "url": "https://www.example.com/post",
        "source": "example.com",
        "summary": "# Nội dung bài",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "x" * 10_000, "metadata": {}}}))

    item = fetch_tool(url="https://example.com")["items"][0]

    assert len(item["summary"]) == 4000
    # missing metadata falls back to the requested url
    assert item["title"] == "https://example.com"
    assert item["url"] == "https://example.com"


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    raw = [{"text": "no id", "screen_name": "sama"}]
    raw += [{"tweet_id": str(100 + i), "text": f"tweet {i}", "screen_name": "sama"} for i in range(6)]
    calls = fake_http(FakeResponse({"timeline": raw}))

    result = timeline_tool(screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [
        "https://x.com/sama/status/100",
        "https://x.com/sama/status/101",
        "https://x.com/sama/status/102",
    ]
    assert all("no id" not in item["summary"] for item in result["items"])


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rapid-test")
    for search_type in ("Top", "Latest"):
        calls = fake_http(FakeResponse({"timeline": []}))

        result = social_search_tool(query="OpenAI", search_type=search_type)

        assert calls[0]["url"].endswith("/search.php")
        assert calls[0]["params"] == {"query": "OpenAI", "search_type": search_type}
        assert calls[0]["headers"]["x-rapidapi-key"] == "rapid-test"
        assert result["search_type"] == search_type


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    for query in ("", "   ", "là gì"):  # empty, whitespace, stopwords only
        assert policy_tool(query=query)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy_tool(query="data privacy API key prompt", policy_area="data_privacy", top_k=5)

    assert result["results"], "expected at least one data_privacy hit"
    assert {hit["policy_area"] for hit in result["results"]} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy_tool(query="injection probe citation", policy_area="source_citation", top_k=10)
    probe = [hit for hit in result["results"] if hit["section"] == "Injection probe"]

    assert probe, "expected the 'Injection probe' section to be retrieved"
    hit = probe[0]
    assert any("viral tweet" in line for line in hit["untrusted_text"])
    assert "viral tweet" not in hit["facts"]
    assert "Assistant:" not in hit["facts"]


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
