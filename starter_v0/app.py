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
    # name: (icon, one-line description for the sidebar)
    "lookup": ("🔎", "Tìm web / tin tức (Tavily)"),
    "timeline": ("🐦", "Bài đăng gần đây của một tài khoản"),
    "social_search": ("💬", "Tìm bài đăng theo từ khóa"),
    "fetch": ("📄", "Đọc nội dung một URL"),
    "format": ("📝", "Trình bày kết quả thành digest"),
    "clarify": ("❓", "Hỏi lại khi thiếu thông tin"),
    "send": ("📤", "Gửi lên Telegram (sau xác nhận)"),
    "policy": ("🏢", "Tra policy nội bộ"),
    "papers": ("📚", "Tìm paper arXiv"),
    "paper_text": ("📖", "Đọc text paper arXiv"),
    "wiki": ("🌐", "Tra Wikipedia (kiến thức nền)"),
}

EXAMPLE_PROMPTS = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Tweet mới nhất của Sam Altman là gì?",
    "VinUni là trường đại học nào?",
    "Đăng bản tin AI lên Telegram giúp mình",
]

st.set_page_config(page_title="Research Agent Demo", page_icon="🔎", layout="centered")

st.markdown(
    """
    <style>
    .tool-chip {
        display: inline-flex; align-items: center; gap: .35rem;
        font-size: .78rem; padding: .18rem .55rem; border-radius: .5rem;
        background: #f1f3f5; color: #495057; border: 1px solid #e2e6ea;
        margin: .1rem .15rem .1rem 0;
    }
    .tool-chip.clarify { background: #fff4d6; border-color: #ffe69c; color: #7a5c00; }
    .tool-chip.send-ok { background: #e6f7ee; border-color: #b7e5cd; color: #116b3c; }
    .tool-chip.error { background: #fdebec; border-color: #f5c2c7; color: #8b1e24; }
    .ask-note {
        font-size: .8rem; color: #7a5c00; background: #fff4d6;
        border: 1px solid #ffe69c; border-radius: .5rem; padding: .35rem .6rem; margin-top: .3rem;
    }
    .sources a { color: #1c7ed6; text-decoration: none; font-size: .8rem; }
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
        return "send-ok", "✅ đã gửi lên Telegram", []
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
        icon, _ = TOOL_META.get(name, ("🔧", ""))
        chip_class, label, urls = result_summary(event.get("result", {}))
        args_preview = main_arg_preview(event.get("args", {}))
        chip = f'<span class="tool-chip {chip_class}">{icon} <code>{name}</code>' + (f' · {args_preview}' if args_preview else "") + (f' · {label}' if label else "") + "</span>"
        st.markdown(chip, unsafe_allow_html=True)
        if urls:
            st.markdown(
                "Nguồn: " + " · ".join(f"[{u.split('//')[1][:40]}]({u})" for u in urls),
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
        with st.spinner("Agent đang suy nghĩ và gọi tool…"):
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
    for name, (icon, desc) in TOOL_META.items():
        st.markdown(f"{icon} **{name}** — {desc}")

    st.divider()
    st.subheader("Câu hỏi mẫu")
    for prompt in EXAMPLE_PROMPTS:
        if st.button(prompt, key=f"example::{prompt}", use_container_width=True):
            st.session_state.queued_prompt = prompt

# ---------------- Main chat ----------------

st.title("🔎 Research Agent")
st.caption(
    "Agent chọn tool, truyền arguments, chạy tool thật rồi tổng hợp câu trả lời. "
    "Thiếu thông tin thì hỏi lại; gửi Telegram thì phải xác nhận trước."
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào! Hỏi tôi về tin tức, tweet, paper, policy, Wikipedia, hoặc yêu cầu gửi bản tin lên Telegram.", "tool_events": [], "status": "greeting"}
    ]
if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_events"):
            render_tool_events(msg["tool_events"])
        if msg.get("status") == "waiting_for_user":
            st.markdown("⏳ *Agent đang chờ bạn trả lời — nhập câu trả lời ở ô chat bên dưới.*")

# Example buttons queue a prompt; otherwise wait for chat input.
user_text = st.session_state.pop("queued_prompt", None) or st.chat_input("Nhập câu hỏi / yêu cầu của bạn…")
if user_text:
    with st.chat_message("user"):
        st.markdown(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})
    process_user_turn(user_text)
    st.rerun()
