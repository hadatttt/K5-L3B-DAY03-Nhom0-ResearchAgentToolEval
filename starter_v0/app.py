from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)

SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
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
}

EXAMPLE_PROMPTS = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tweet mới nhất của Sam Altman là gì?",
    "VinUni là trường đại học nào?",
    "Đăng bản tin AI lên Telegram giúp mình",
]

st.set_page_config(page_title="Research Agent", layout="centered")

st.markdown(
    """
    <style>
    :root {
        --ink: #1a1d21; --ink-2: #4a5158; --ink-3: #8a9199;
        --surface: #f4f5f6; --hairline: rgba(26, 29, 33, 0.08);
        --accent: #1b5cc4;
        --ok: #1d7a45; --warn: #b8860b; --err: #b3261e;
    }
    .tool-chip {
        display: inline-flex; align-items: center; gap: 6px;
        font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
        font-size: 12px; line-height: 20px;
        padding: 2px 8px; border-radius: 6px;
        background: var(--surface); color: var(--ink-2);
        border: 1px solid var(--hairline);
        margin: 2px 8px 2px 0;
    }
    .tool-chip .dot {
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--ink-3); flex: none;
    }
    .tool-chip.clarify { border-color: rgba(184, 134, 11, 0.4); }
    .tool-chip.clarify .dot { background: var(--warn); }
    .tool-chip.send-ok .dot { background: var(--ok); }
    .tool-chip.error .dot { background: var(--err); }
    .tool-chip b { color: var(--ink); font-weight: 500; }
    .tool-chip .sep { color: var(--ink-3); }
    .ask-note {
        font-size: 12px; color: var(--ink-2);
        border-left: 2px solid var(--warn);
        padding: 4px 8px; margin-top: 4px;
    }
    .sources { font-size: 12px; color: var(--ink-3); margin-top: 2px; }
    .sources a { color: var(--accent); text-decoration: none; }
    .tool-list code {
        font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
        font-size: 12px; color: var(--ink);
    }
    .tool-list div { margin: 4px 0; color: var(--ink-2); font-size: 13px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_tool_schema() -> list[dict]:
    return to_openai_tools(load_tool_declarations(TOOLS_PATH))


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
        parts = [f'<span class="dot"></span>', f"<b>{name}</b>"]
        if args_preview:
            parts.append(f'(<span class="sep">{args_preview}</span>)')
        if label:
            parts.append(f'<span class="sep">— {label}</span>')
        st.markdown(f'<span class="tool-chip {chip_class}">' + " ".join(parts) + "</span>", unsafe_allow_html=True)
        if urls:
            st.markdown(
                '<div class="sources">Nguồn: ' + " · ".join(f'<a href="{u}">{u.split("//")[1][:40]}</a>' for u in urls) + "</div>",
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
            "model": st.session_state.get("model_override") or None,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "turns": [],
        }
    return st.session_state.transcript


def process_user_turn(user_text: str) -> None:
    history = st.session_state.history
    transcript = get_session_transcript()

    turn_record = {"user": user_text, "status": "started"}
    try:
        with st.spinner("Đang gọi tool…"):
            result = run_model_tool_loop(
                provider=get_provider(st.session_state.provider),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")},
                    *trim_history(history, HISTORY_WINDOW),
                    {"role": "user", "content": user_text},
                ],
                tools=get_tool_schema(),
                model=st.session_state.get("model_override") or None,
                max_tool_rounds=MAX_TOOL_ROUNDS,
            )
        assistant_text = result["assistant_text"] or "(không có nội dung trả lời)"
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_text,
            "tool_events": result["tool_events"],
            "status": result["status"],
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
    st.session_state.provider = st.selectbox(
        "Provider", ["mistral", "openrouter", "openai", "anthropic", "gemini", "ollama"], index=0
    )
    st.session_state.model_override = st.text_input("Model override (tuỳ chọn)", value="").strip() or None
    st.session_state.save_transcript = st.toggle("Lưu transcript (thư mục transcripts/)", value=True)

    st.divider()
    st.subheader("Tools")
    for name, desc in TOOL_META.items():
        st.markdown(f'<div class="tool-list"><div><code>{name}</code> — {desc}</div></div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Câu hỏi mẫu")
    for prompt in EXAMPLE_PROMPTS:
        if st.button(prompt, key=f"example::{prompt}", use_container_width=True):
            st.session_state.queued_prompt = prompt

# ---------------- Main chat ----------------

st.title("Research Agent")
st.caption("Agent chọn tool, chạy tool thật rồi tổng hợp câu trả lời — hỏi lại khi thiếu thông tin, xác nhận trước khi gửi")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Research agent với 11 tool: tin tức, tweet, paper, Wikipedia, policy nội bộ, và gửi Telegram sau xác nhận. Bấm một câu hỏi mẫu ở sidebar hoặc gõ yêu cầu của bạn", "tool_events": [], "status": "greeting"}
    ]
if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_events"):
            render_tool_events(msg["tool_events"])
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
