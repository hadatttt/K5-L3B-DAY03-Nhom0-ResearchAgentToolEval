"""Probe a single eval case end-to-end without running the whole suite.

Usage:
    python scripts/probe_case.py --provider mistral --eval-cases data/eval_base.json --case R12_confirm_before_send

Same agent + same grading logic as run_eval.py, but only one case — for fast
hypothesis testing during prompt/tool iteration.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from env_loader import load_lab_env
load_lab_env(ROOT)

from agent import ResearchAgent
from providers import make_provider
from run_eval import ARTIFACTS_DIR, case_messages, evaluate_phase_b, load_cases
from tools import load_tool_declarations, to_openai_tools


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one eval case through the agent and grade it.")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--eval-cases", type=Path, default=ROOT / "data" / "eval_base.json")
    parser.add_argument("--case", required=True, help="Case id to run, e.g. R12_confirm_before_send")
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("-n", "--repeat", type=int, default=1, help="Run the case N times to check stability")
    args = parser.parse_args()

    cases = {c["id"]: c for c in load_cases(args.eval_cases, "B")}
    if args.case not in cases:
        raise SystemExit(f"Case not found: {args.case}. Available: {', '.join(cases)}")
    case = cases[args.case]

    provider = make_provider(args.provider)
    tools = to_openai_tools(load_tool_declarations(args.tools))
    system_prompt = args.system_prompt.read_text(encoding="utf-8")

    for i in range(args.repeat):
        agent = ResearchAgent(provider, system_prompt=system_prompt, tools=tools, model=args.model)
        run = agent.run(case_messages(case))
        calls = [{"name": c.name, "args": c.args} for c in run.tool_calls]
        graded = evaluate_phase_b(case, calls, run.text)
        print(f"--- run {i + 1}/{args.repeat} ---")
        print(f"passed: {graded['passed']}")
        if graded["failures"]:
            print(f"failures: {graded['failures']}")
        for c in calls:
            print(f"call: {c['name']} {c['args']}")
        if run.text:
            print(f"text: {run.text[:200]}")


if __name__ == "__main__":
    main()
