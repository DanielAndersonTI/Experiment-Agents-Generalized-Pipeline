"""
Diagnóstico da integração com a API da Anthropic (Claude).
Rode a partir da raiz do projeto: python Interface/tests/testar_claude.py
"""

import os
import sys
import traceback
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from dotenv import load_dotenv

# Raiz do projeto: sobe de tests -> Interface -> raiz
raiz_projeto = Path(__file__).resolve().parents[2]

candidatos = [
    raiz_projeto / "Experimento_Multiagente" / ".env",
    raiz_projeto / ".env",
    Path(__file__).resolve().parent / ".env",
    Path.cwd() / ".env",
]

env_path = None
for p in candidatos:
    if p.is_file():
        env_path = p
        break

if env_path is None:
    print("✗ Nenhum .env encontrado. Testei:")
    for p in candidatos:
        print(f"   - {p}")
    sys.exit(1)

print(f"Arquivo .env encontrado em: {env_path}")
load_dotenv(env_path)

API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

print("=" * 70)
print("DIAGNÓSTICO — INTEGRAÇÃO CLAUDE (ANTHROPIC)")
print("=" * 70)
print(f"API key definida? {'SIM' if API_KEY else 'NÃO'}")
print(f"API key primeiros 12 chars: {API_KEY[:12] if API_KEY else '-'}")
print(f"Model name: {MODEL_NAME}")
print(f"Max tokens: {MAX_TOKENS}")
print()

if not API_KEY:
    print("✗ ANTHROPIC_API_KEY não foi carregada.")
    sys.exit(1)

# --- Teste 1: SDK Anthropic cru ---
print("-" * 70)
print("TESTE 1 — SDK Anthropic cru")
print("-" * 70)
try:
    import anthropic
    print(f"Versão do anthropic: {anthropic.__version__}")
except ImportError:
    print("✗ SDK 'anthropic' não está instalado.")
    anthropic = None

if anthropic:
    try:
        client = anthropic.Anthropic(api_key=API_KEY)
        r = client.messages.create(
            model=MODEL_NAME,
            max_tokens=64,
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
        )
        print(f"✓ Resposta: {r.content[0].text!r}")
    except Exception as e:
        print(f"✗ FALHOU: {type(e).__name__}: {e}")
        traceback.print_exc()

# --- Teste 2: SDK com temperature ---
print()
print("-" * 70)
print("TESTE 2 — SDK Anthropic + temperature=0.0")
print("-" * 70)
if anthropic:
    try:
        client = anthropic.Anthropic(api_key=API_KEY)
        r = client.messages.create(
            model=MODEL_NAME,
            max_tokens=64,
            temperature=0.0,
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
        )
        print(f"✓ Resposta: {r.content[0].text!r}")
    except Exception as e:
        print(f"✗ FALHOU: {type(e).__name__}: {e}")
        traceback.print_exc()

# --- Teste 3: CrewAI sem temperature ---
print()
print("-" * 70)
print("TESTE 3 — CrewAI LLM (sem temperature)")
print("-" * 70)
try:
    from crewai import LLM
except ImportError:
    print("✗ crewai não instalado.")
    LLM = None

if LLM:
    try:
        llm = LLM(model=f"anthropic/{MODEL_NAME}", api_key=API_KEY, max_tokens=64)
        print(f"✓ Resposta: {llm.call('Responda apenas: OK')!r}")
    except Exception as e:
        print(f"✗ FALHOU: {type(e).__name__}: {e}")
        traceback.print_exc()

# --- Teste 4: CrewAI com temperature ---
print()
print("-" * 70)
print("TESTE 4 — CrewAI LLM (com temperature=0.0)")
print("-" * 70)
if LLM:
    try:
        llm = LLM(
            model=f"anthropic/{MODEL_NAME}",
            api_key=API_KEY,
            temperature=0.0,
            max_tokens=64,
        )
        print(f"✓ Resposta: {llm.call('Responda apenas: OK')!r}")
    except Exception as e:
        print(f"✗ FALHOU: {type(e).__name__}: {e}")
        traceback.print_exc()

print()
print("=" * 70)
print("FIM DO DIAGNÓSTICO")
print("=" * 70)