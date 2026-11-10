from __future__ import annotations

import csv
import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import streamlit as st

from chat import run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)

SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
VERSIONS_DIR = ROOT / "artifacts" / "versions"
VERSION_LOG_PATH = ROOT / "artifacts" / "version_log.csv"
CURRENT_VERSION = "current"
TRANSCRIPTS_DIR = ROOT / "transcripts"

HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

TOOL_META = {
    # name: one-line description for the sidebar
    "lookup": "Tìm web / tin tức (Tavily)",
    "timeline": "Bài đăng gần đây của một tài khoản",
    "social_search": "Tìm bài đăng theo từ khóa",
    "fetch": "Đọc nội dung một URL",
    "format": "Trình bày kết quả thành digest",
    "clarify": "Hỏi lại khi thiếu thông tin",
    "send": "Gửi lên Telegram (sau xác nhận)",
    "policy": "Tra policy nội bộ",
    "papers": "Tìm paper arXiv",
    "paper_text": "Đọc text paper arXiv",
    "wiki": "Tra Wikipedia (kiến thức nền)",
    "hackernews": "Thảo luận trên Hacker News",
    "github": "Tìm repo open-source trên GitHub",
    "hf_models": "Tìm model trên Hugging Face",
}

# Public demo: anonymous visitors must not be able to post to the team's Telegram channel.
DISABLED_TOOLS = {"send"}
DEMO_PROMPT_NOTE = (
    "\n\n## Demo UI note\nThe `send` tool is disabled in this public demo. If the user asks to post to Telegram, "
    "say that sending is disabled here and offer the formatted text so they can copy it."
)

EXAMPLE_PROMPTS = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tweet mới nhất của Sam Altman là gì?",
    "VinUni là trường đại học nào?",
    "Hacker News đang bàn gì về LLM agents?",
    "Model Whisper nào được tải nhiều nhất trên Hugging Face?",
]

st.set_page_config(page_title="Research Agent", layout="centered")

st.markdown(
    """
    <style>
    /* Theme-neutral: text inherits the Streamlit theme colour (light or dark),
       surfaces are translucent grey so they read on both backgrounds. */
    :root {
        --ink: inherit;
        --surface: rgba(128, 128, 128, 0.12); --hairline: rgba(128, 128, 128, 0.28);
        --accent: #4a8fe7;
        --ok: #2e9e5b; --warn: #d4a017; --err: #e0524a;
    }
    .tool-chip {
        display: inline-flex; align-items: center; gap: 6px;
        font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
        font-size: 12px; line-height: 20px;
        padding: 2px 8px; border-radius: 6px;
        background: var(--surface); color: inherit;
        border: 1px solid var(--hairline);
        margin: 2px 8px 2px 0;
    }
    .tool-chip .dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: currentColor; opacity: 0.45; flex: none;
    }
    .tool-chip.clarify { border-color: rgba(184, 134, 11, 0.4); }
    .tool-chip.clarify .dot { background: var(--warn); opacity: 1; }
    .tool-chip.send-ok .dot { background: var(--ok); opacity: 1; }
    .tool-chip.error .dot { background: var(--err); opacity: 1; }
    .tool-chip b { color: inherit; font-weight: 600; white-space: nowrap; flex: none; }
    .tool-chip .sep { opacity: 0.7; }
    .ask-note {
        font-size: 12px; opacity: 0.85;
        border-left: 2px solid var(--warn);
        padding: 4px 8px; margin-top: 4px;
    }
    .sources { font-size: 12px; opacity: 0.8; margin-top: 2px; }
    .sources a { color: var(--accent); text-decoration: none; }
    .tool-list code {
        font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
        font-size: 12px; color: inherit;
        background: var(--surface); border: 1px solid var(--hairline);
        padding: 0 4px; border-radius: 4px;
    }
    .tool-list div { margin: 4px 0; color: inherit; opacity: 0.9; font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def available_versions() -> list[str]:
    """`current` (artifacts/) first, then snapshots in artifacts/versions/vN/, newest first."""
    snapshots = [
        d.name for d in VERSIONS_DIR.glob("v*")
        if d.is_dir() and (d / "system_prompt.md").exists() and (d / "tools.yaml").exists()
    ] if VERSIONS_DIR.exists() else []
    snapshots.sort(key=lambda name: int(name[1:]) if name[1:].isdigit() else -1, reverse=True)
    return [CURRENT_VERSION, *snapshots]


def version_paths(version: str) -> tuple[Path, Path]:
    if version == CURRENT_VERSION:
        return SYSTEM_PROMPT_PATH, TOOLS_PATH
    folder = VERSIONS_DIR / version
    return folder / "system_prompt.md", folder / "tools.yaml"


@st.cache_data
def version_log() -> dict[str, dict]:
    if not VERSION_LOG_PATH.exists():
        return {}
    with VERSION_LOG_PATH.open(encoding="utf-8", newline="") as f:
        return {row["version"].strip(): row for row in csv.DictReader(f) if row.get("version")}


def version_label(version: str) -> str:
    if version == CURRENT_VERSION:
        return "Hiện tại — artifacts/ (bản mới nhất)"
    row = version_log().get(version, {})
    changed = (row.get("changed_artifact") or "").strip()
    return f"{version} — {changed[:45]}" if changed else version


@st.cache_resource
def get_tool_declarations(version: str = CURRENT_VERSION) -> list[dict]:
    _, tools_path = version_paths(version)
    return [d for d in load_tool_declarations(tools_path) if d["name"] not in DISABLED_TOOLS]


@st.cache_resource
def get_tool_schema(version: str = CURRENT_VERSION) -> list[dict]:
    return to_openai_tools(get_tool_declarations(version))


def short_description(decl: dict) -> str:
    """Sidebar text: curated one-liner, else the first sentence of the tools.yaml description."""
    if decl["name"] in TOOL_META:
        return TOOL_META[decl["name"]]
    first = " ".join(str(decl.get("description", "")).split()).split(". ")[0]
    return first[:70] + ("…" if len(first) > 70 else "")


def link_label(url: str) -> str:
    """Readable link text: decode %XX so Vietnamese titles show as text, drop scheme."""
    label = unquote(url.split("//", 1)[-1])
    return label[:48] + ("…" if len(label) > 48 else "")


@st.cache_resource
def get_provider(provider_name: str):
    return make_provider(provider_name)


def main_arg_preview(args: dict) -> str:
    for key in ("query", "screenname", "url", "arxiv_url", "question", "text"):
        if args.get(key):
            value = str(args[key])
            return f"{key}={value[:48]}{'…' if len(value) > 48 else ''}"
    for key, value in args.items():
        return f"{key}={str(value)[:48]}"
    return ""


def result_summary(result: dict) -> tuple[str, str, list[str]]:
    """Return (chip_class, label, source_urls) for a tool result."""
    if not isinstance(result, dict):
        return "", "ok", []
    if result.get("error"):
        return "error", f"lỗi: {str(result.get('message', result['error']))[:80]}", []
    if result.get("awaiting_user"):
        return "clarify", "agent hỏi lại — trả lời ở ô chat bên dưới", []
    items = result.get("items") or []
    urls = [it.get("url") for it in items if isinstance(it, dict) and it.get("url")][:5]
    label = ""
    if result.get("status") == "sent":
        return "send-ok", "đã gửi lên Telegram", []
    if result.get("markdown"):
        label = "digest đã tạo"
    elif items:
        label = f"{len(items)} kết quả" + (f" — {items[0].get('title', '')[:60]}" if items and isinstance(items[0], dict) else "")
    elif result.get("facts"):
        label = f"{len(result['facts'])} mục policy"
    return "", label, urls


def render_tool_events(events: list[dict]) -> None:
    for event in events:
        name = event.get("tool", "?")
        chip_class, label, urls = result_summary(event.get("result", {}))
        args_preview = main_arg_preview(event.get("args", {}))
        parts = ['<span class="dot"></span>', f"<b>{html.escape(name)}</b>"]
        if args_preview:
            parts.append(f'(<span class="sep">{html.escape(args_preview)}</span>)')
        if label:
            parts.append(f'<span class="sep">— {html.escape(label)}</span>')
        st.markdown(f'<span class="tool-chip {chip_class}">' + " ".join(parts) + "</span>", unsafe_allow_html=True)
        if urls:
            st.markdown(
                '<div class="sources">Nguồn: ' + " · ".join(f'<a href="{html.escape(u, quote=True)}" target="_blank">{html.escape(link_label(u))}</a>' for u in urls) + "</div>",
                unsafe_allow_html=True,
            )
        result = event.get("result", {})
        if isinstance(result, dict) and result.get("markdown"):
            with st.expander("Xem digest"):
                st.markdown(result["markdown"])
        elif isinstance(result, dict) and not (result.get("awaiting_user") or result.get("error")):
            with st.expander("Xem kết quả thô"):
                st.json(result)


def get_session_transcript() -> dict | None:
    if not st.session_state.get("save_transcript", True):
        return None
    if "transcript" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        transcript_id = f"ui_{safe_slug(st.session_state.provider)}_{timestamp}"
        st.session_state.transcript = {
            "transcript_id": transcript_id,
            "provider": st.session_state.provider,
            "version": st.session_state.version,
            "model": st.session_state.get("model_override") or None,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "turns": [],
        }
    return st.session_state.transcript


def process_user_turn(user_text: str) -> None:
    history = st.session_state.history
    transcript = get_session_transcript()

    turn_record = {"user": user_text, "version": st.session_state.version, "status": "started"}
    try:
        with st.spinner("Đang gọi tool…"):
            result = run_model_tool_loop(
                provider=get_provider(st.session_state.provider),
                messages=[
                    {"role": "system", "content": version_paths(st.session_state.version)[0].read_text(encoding="utf-8") + DEMO_PROMPT_NOTE},
                    *trim_history(history, HISTORY_WINDOW),
                    {"role": "user", "content": user_text},
                ],
                tools=get_tool_schema(st.session_state.version),
                model=st.session_state.get("model_override") or None,
                max_tool_rounds=MAX_TOOL_ROUNDS,
            )
        assistant_text = result["assistant_text"] or "(không có nội dung trả lời)"
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": result["tool_events"],
            "status": result["status"],
            "version": st.session_state.version,
        })
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": assistant_text})
        turn_record.update({k: result[k] for k in ("status", "rounds", "tool_events")})
    except Exception as exc:
        error_text = f"Lỗi provider: {type(exc).__name__}: {exc}"
        st.session_state.messages.append({"role": "assistant", "content": error_text, "tool_events": [], "status": "provider_error"})
        turn_record.update({"status": "provider_error", "error": error_text})

    if transcript is not None:
        transcript["turns"].append(turn_record)
        write_transcript(TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json", transcript)


# ---------------- Sidebar ----------------

with st.sidebar:
    st.header("Cấu hình")
    versions = available_versions()
    st.session_state.version = st.selectbox(
        "Version (prompt + tools)", versions, index=0, format_func=version_label,
        help="Chọn snapshot trong artifacts/versions/ để so sánh hành vi các version trong version_log.csv.",
    )
    log_row = version_log().get(st.session_state.version, {})
    if st.session_state.version == CURRENT_VERSION:
        st.caption("Đang dùng `artifacts/system_prompt.md` + `artifacts/tools.yaml`.")
    elif log_row:
        st.caption(
            f"**Giả thuyết:** {log_row.get('hypothesis') or log_row.get('reason') or '—'}  \n"
            f"**Kết quả eval:** {log_row.get('metric_after') or '—'}"
        )
    if st.session_state.version == "v0":
        st.warning("v0 là prompt starter cố tình xấu: đoán bừa thay vì hỏi lại. Dùng để so sánh với bản sau.")
    if "v1" not in versions and "v1" in version_log():
        st.caption("v1 không có snapshot (prompt v1 chưa từng được commit).")
    st.session_state.provider = st.selectbox(
        "Provider", ["mistral", "openrouter", "openai", "anthropic", "gemini", "ollama"], index=0
    )
    st.session_state.model_override = st.text_input("Model override (tuỳ chọn)", value="").strip() or None
    st.session_state.save_transcript = st.toggle("Lưu transcript (thư mục transcripts/)", value=True)

    st.divider()
    st.subheader("Tools")
    for decl in get_tool_declarations(st.session_state.version):
        st.markdown(
            f'<div class="tool-list"><div><code>{html.escape(decl["name"])}</code> — {html.escape(short_description(decl))}</div></div>',
            unsafe_allow_html=True,
        )
    st.caption("Tool `send` (Telegram) bị tắt trên bản demo công khai.")

    st.divider()
    st.subheader("Câu hỏi mẫu")
    for prompt in EXAMPLE_PROMPTS:
        if st.button(prompt, key=f"example::{prompt}", use_container_width=True):
            st.session_state.queued_prompt = prompt

# ---------------- Main chat ----------------

st.title("Research Agent")
st.caption("Agent chọn tool, chạy tool thật rồi tổng hợp câu trả lời — hỏi lại khi thiếu thông tin")

if st.session_state.get("active_version") not in (None, st.session_state.version):
    for key in ("messages", "history", "transcript"):
        st.session_state.pop(key, None)
st.session_state.active_version = st.session_state.version

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"[{version_label(st.session_state.version)}] Research agent với {len(get_tool_declarations(st.session_state.version))} tool ({', '.join(d['name'] for d in get_tool_declarations(st.session_state.version))}). Bấm một câu hỏi mẫu ở sidebar hoặc gõ yêu cầu của bạn.", "tool_events": [], "status": "greeting"}
    ]
if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_events"):
            render_tool_events(msg["tool_events"])
        if msg["role"] == "assistant" and msg.get("version"):
            st.caption(f"version: {msg['version']}")
        if msg.get("status") == "waiting_for_user":
            st.markdown('<div class="ask-note">Agent chờ câu trả lời của bạn — gõ vào ô chat bên dưới</div>', unsafe_allow_html=True)

# Example buttons queue a prompt; otherwise wait for chat input.
user_text = st.session_state.pop("queued_prompt", None) or st.chat_input("Nhập câu hỏi / yêu cầu của bạn…")
if user_text:
    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})
    process_user_turn(user_text)
    st.rerun()
