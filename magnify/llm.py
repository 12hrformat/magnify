"""Optional AI pivot engine.

Talks to any OpenAI-compatible /chat/completions endpoint:
  - local Ollama        MAGNIFY_LLM_URL=http://localhost:11434/v1
  - LM Studio, llama.cpp server, vLLM, etc.
  - OpenAI/Anthropic-compatible proxies

Config:
  MAGNIFY_LLM_URL     base URL including /v1 (required to enable)
  MAGNIFY_LLM_MODEL   model name (default: llama3.1)
  MAGNIFY_LLM_KEY     optional API key

Privacy: nothing is sent anywhere unless the user enables this and
sets MAGNIFY_LLM_URL. Findings JSON is the only payload.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request

UA = "magnify/0.1"

SYSTEM_PROMPT = (
    "You are an OSINT analyst assistant. Given structured findings from "
    "an authorized reconnaissance run, produce: (1) a short summary of "
    "what was found, (2) up to 5 concrete next-step pivots, (3) up to 8 "
    "additional Google dorks using the same identifiers. Respond ONLY "
    "with JSON: {\"summary\": str, \"pivots\": [str], \"dorks\": [str]}"
)


def enabled() -> bool:
    return bool(os.environ.get("MAGNIFY_LLM_URL"))


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text


def ask(findings: dict) -> dict:
    """Send findings to the LLM; returns parsed notes dict."""
    base = os.environ.get("MAGNIFY_LLM_URL", "").rstrip("/")
    if not base:
        return {"error": "MAGNIFY_LLM_URL not set (AI disabled)"}
    model = os.environ.get("MAGNIFY_LLM_MODEL", "llama3.1")
    key = os.environ.get("MAGNIFY_LLM_KEY", "")

    payload = {
        "model": model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(findings, default=str)[:12000]},
        ],
    }
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90.0) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_fences(content))
        if isinstance(parsed, dict):
            parsed["model"] = model
            return parsed
        return {"error": "LLM returned non-object JSON"}
    except json.JSONDecodeError:
        return {"error": "LLM returned unparseable JSON", "model": model}
    except (OSError, KeyError, IndexError, ValueError) as exc:
        return {"error": f"LLM request failed: {exc}"}
