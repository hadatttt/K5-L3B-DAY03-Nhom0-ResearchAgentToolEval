"""Rebuild the v1 system_prompt.md (never committed during the lab) by inverting
the three v1->v2 edits, then verify against the sha256 recorded in the v1 run JSON."""
import hashlib

v2 = open("scripts/_v2_prompt.tmp", encoding="utf-8").read()

old1 = """## Core rule: ask, never guess — but only when something is truly missing

Call `clarify` ONLY when a required piece of information is genuinely missing. If the user already gave the account, URL, or topic, do NOT clarify and do NOT ask for permission — just call the right tool immediately.

Clarify when:
- "Tóm tắt 5 tweet mới nhất" without saying WHOSE tweets → ask which account (handle).
- "Tóm tắt bài viết này" without a URL → ask for the link.
- "Tìm tin" without any topic → ask what topic they want.

Do NOT clarify when the request is already actionable:
- "Tweet mới nhất của Sam Altman" → account is known (sama), call `timeline` right away.
- A message that already contains a URL → call `fetch` right away.
- "Tweet phổ biến/top về OpenAI" → keyword and search type are known, call `social_search` with `search_type: "Top"` right away; never ask for a timeframe.

Never substitute a well-known account (e.g. Sam Altman) or a plausible URL (e.g. arxiv.org) when the user did not specify one.

`clarify` conventions:
- `response_type: "yes_no"` — confirmation before a write action (send).
- `response_type: "text"` — asking for a missing value (handle, URL, topic)."""
new1 = """## Core rule: ask, never guess

If the request is missing a required piece of information, DO NOT guess or invent a value. Call the `clarify` tool with a short, specific question instead.

- "Tóm tắt 5 tweet mới nhất" without saying WHOSE tweets → clarify: ask which account (handle).
- "Tóm tắt bài viết này" without a URL → clarify: ask for the link.
- "Tìm tin hôm nay" without a topic → clarify: ask what topic they want.

Never substitute a well-known account (e.g. Sam Altman) or a plausible URL (e.g. arxiv.org) when the user did not specify one."""

old2 = 'First call `clarify` with `response_type: "yes_no"` showing the exact text you intend to send (never `response_type: "text"` for this), and only send after the user explicitly confirms.'
new2 = 'First call `clarify` with `response_type: "yes_no"` showing the exact text you intend to send, and only send after the user explicitly confirms.'

old3 = """## Parallel calls

Only call multiple tools in one turn when the user EXPLICITLY asks for more than one source (e.g. "tìm trên web VÀ tìm thêm tweet về AI", "cả web lẫn Twitter"). A request for web news alone → only `lookup`. A request for tweets alone → only `timeline` or `social_search`."""
new3 = """## Parallel calls

If one request needs more than one source (e.g. web news AND tweets about the same topic), make all needed tool calls in the same turn instead of picking just one."""

for old in (old1, old2, old3):
    assert old in v2, "mot khoi v2 khong tim thay"
v1 = v2.replace(old1, new1).replace(old2, new2).replace(old3, new3)

h = hashlib.sha256(v1.encode("utf-8")).hexdigest()
target = "5138c3df1f4b3772fa699a60892ba9216800e184a8db50d45c2aaff7f8ec84a7"
print("v1 reconstructed:", h)
print("target (run JSON) :", target)
print("MATCH!" if h == target else "KHONG KHOP")
open("scripts/_v1_prompt.tmp", "w", encoding="utf-8", newline="").write(v1)
