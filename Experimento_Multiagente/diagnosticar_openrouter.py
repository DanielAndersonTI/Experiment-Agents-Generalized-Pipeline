"""Diagnose DeepSeek configuration without running the full DAVINCI pipeline."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"


def result(label: str, ok: bool, detail: str) -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {detail}")


def main() -> int:
    print("DAVINCI DeepSeek diagnostic")
    print(f"Python: {sys.executable}")
    print(f"Working directory: {Path.cwd()}")
    print(f".env path: {ENV_PATH}")

    if not ENV_PATH.is_file():
        result(".env", False, "file not found")
        return 1
    load_dotenv(ENV_PATH, override=True)
    result(".env", True, "loaded")

    # OpenRouter configuration retained for historical diagnostics:
    # api_key = os.getenv("OPENROUTER_API_KEY", "")
    # model = os.getenv("OPENROUTER_MODEL", "")
    # max_tokens_text = os.getenv("OPENROUTER_MAX_TOKENS", "512")
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    max_tokens_text = os.getenv("DEEPSEEK_MAX_TOKENS", "512")
    try:
        max_tokens = int(max_tokens_text)
    except ValueError:
        result("max_tokens", False, f"invalid integer: {max_tokens_text!r}")
        return 1

    result("API key", bool(api_key), "configured (value hidden)" if api_key else "missing")
    result("model", bool(model), model or "missing")
    result("max_tokens", 0 < max_tokens <= 525, f"{max_tokens} (available balance previously reported: 525)")
    if not api_key or not model or max_tokens <= 0:
        return 1

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly OK."}],
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        result("DeepSeek request", bool(content), f"HTTP 200; response={content!r}")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        result("DeepSeek request", False, f"HTTP {error.code}; {body[:600]}")
        return 1
    except Exception as error:
        result("DeepSeek request", False, f"{type(error).__name__}: {error}")
        return 1

    sys.path.insert(0, str(ROOT))
    try:
        import main_fewshot

        llm = main_fewshot.criar_llm()
        llm_model = getattr(llm, "model", None)
        llm_ok = llm_model in {model, f"deepseek/{model}"}
        result("CrewAI LLM", llm_ok, f"model={llm_model!r}; max_tokens={getattr(llm, 'max_tokens', None)!r}")
        result("C3 executor", callable(getattr(main_fewshot, "executar_pipeline_c3", None)), "imported")
    except Exception as error:
        result("CrewAI/pipeline import", False, f"{type(error).__name__}: {error}")
        return 1

    print("Diagnosis complete: configuration and a minimal API request are working.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
