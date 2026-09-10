"""Local DeepSeek configuration test; does not contact the API."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"


def check(label: str, ok: bool, detail: str) -> bool:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {detail}")
    return ok


def main() -> int:
    print("DAVINCI local DeepSeek test (no API request)")
    print(f".env: {ENV_PATH}")

    checks = []
    checks.append(check(".env exists", ENV_PATH.is_file(), "found" if ENV_PATH.is_file() else "not found"))
    if not ENV_PATH.is_file():
        return 1

    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    model = os.getenv("DEEPSEEK_MODEL", "").strip()
    max_tokens_text = os.getenv("DEEPSEEK_MAX_TOKENS", "512").strip()

    key_format_ok = bool(re.fullmatch(r"sk-[A-Za-z0-9_-]{20,}", api_key))
    checks.append(check("DEEPSEEK_API_KEY", key_format_ok, "format looks valid (value hidden)" if key_format_ok else "missing or unexpected format"))
    checks.append(check("DEEPSEEK_MODEL", model == "deepseek-chat", repr(model) if model else "missing; expected deepseek-chat"))

    try:
        max_tokens = int(max_tokens_text)
        token_ok = 1 <= max_tokens <= 512
    except ValueError:
        max_tokens = 0
        token_ok = False
    checks.append(check("DEEPSEEK_MAX_TOKENS", token_ok, f"{max_tokens} (no API call made)"))

    sys.path.insert(0, str(ROOT))
    try:
        import main_fewshot

        llm = main_fewshot.criar_llm()
        llm_model = getattr(llm, "model", None)
        model_ok = llm_model in {model, f"deepseek/{model}"}
        checks.append(check("CrewAI LLM", model_ok, f"model={llm_model!r}; max_tokens={getattr(llm, 'max_tokens', None)!r}"))
        checks.append(check("C3 executor", callable(getattr(main_fewshot, "executar_pipeline_c3", None)), "imported"))
    except Exception as error:
        checks.append(check("CrewAI setup", False, f"{type(error).__name__}: {error}"))

    print()
    if all(checks):
        print("LOCAL TEST PASSED: configuration is ready; no API request was made.")
        print("A real request can still fail if the DeepSeek account has no balance or access.")
        return 0
    print("LOCAL TEST FAILED: fix the items marked FAIL before using the API.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
