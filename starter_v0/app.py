from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parent
load_lab_env(ROOT)

SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"


@st.cache_resource
def get_tool_schema() -> list[dict]:
    declarations = load_tool_declarations(TOOLS_PATH)
    return to_openai_tools(declarations)


@st.cache_resource
def get_provider(provider_name: str):
    return make_provider(provider_name)


def execute_tool_call(call):
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {"tool": call.name, "args": call.args, "result": {"error": "unknown_tool"}}
    try:
        return {"tool": call.name, "args": call.args, "result": func(**call.args)}
    except Exception as exc:  # pragma: no cover - UI guardrail
        return {
            "tool": call.name,
            "args": call.args,
            "result": {"error": type(exc).__name__, "message": str(exc)},
        }


def run_agent_turn(provider_name: str, model_override: str | None, history: list[dict[str, str]]) -> tuple[str, list[dict]]:
    provider = get_provider(provider_name)
    tools = get_tool_schema()
    prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    messages = [{"role": "system", "content": prompt}, *history]
    response = provider.complete(messages, tools, model=model_override or None, temperature=0.0)

    tool_events: list[dict] = []
    if response.tool_calls:
        for call in response.tool_calls:
            tool_events.append(execute_tool_call(call))

        tool_payload = json.dumps(tool_events, ensure_ascii=False, indent=2)
        follow_up = {
            "role": "user",
            "content": (
                "TOOL_RESULTS_JSON:\n"
                f"{tool_payload}\n\n"
                "Use only these tool results. If the user asked for a digest and the items are ready, "
                "call the formatting tool. Otherwise answer directly with cited sources when available."
            ),
        }
        second_response = provider.complete(
            messages + [{"role": "assistant", "content": response.text or "I will use the selected tool(s)."}, follow_up],
            tools,
            model=model_override or None,
            temperature=0.0,
        )
        final_text = second_response.text or "I finished the task using the tool results."
        return final_text, tool_events

    final_text = response.text or "I don’t have a direct answer yet."
    return final_text, tool_events


st.set_page_config(page_title="Research Agent Demo", page_icon="🔎")
st.title("🔎 Research Agent Demo")
st.caption("Demo UI for the Day 03 research agent. Works with the same system prompt and tool registry as the lab.")

with st.sidebar:
    st.header("Config")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini", "ollama"], index=0)
    model_override = st.text_input("Model override (optional)", value="")
    st.markdown("- Prompt: `artifacts/system_prompt.md`")
    st.markdown("- Tools: `artifacts/tools.yaml`")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào! Hỏi tôi về tin tức, policy, timeline, tìm bài nghiên cứu, hoặc đọc URL."}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Nhập câu hỏi / yêu cầu của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    with st.spinner("Agent đang suy nghĩ và gọi tool..."):
        answer, tool_events = run_agent_turn(provider_name, model_override.strip() or None, history)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)

    if tool_events:
        with st.expander("Tool calls / results"):
            st.json(tool_events)
