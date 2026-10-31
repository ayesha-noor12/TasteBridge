"""One LLM call to check LLM_* settings. Prints why it failed, never the key.

Usage (from backend/): set -a; source .env; set +a; .venv/bin/python scripts/smoke_llm.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402
from app.explain import error_reason, make_client  # noqa: E402


async def main() -> int:
    s = config.llm_settings()
    print(f"llm_mode={config.llm_mode()} base_url={s['base_url']} model={s['model']} key={'set' if s['api_key'] else 'missing'}")
    if config.llm_mode() != "on":
        print("LLM is off: set LLM_MODE=on and LLM_API_KEY.")
        return 2
    try:
        resp = await make_client().chat.completions.create(
            model=s["model"],
            messages=[{"role": "user", "content": 'Reply with JSON only: {"ok": true}'}],
            max_tokens=500,
        )
    except Exception as e:
        print(f"FAILED: {config.redact(error_reason(e))}")
        return 1
    text = (resp.choices[0].message.content or "").strip()
    print(f"OK, reply: {text[:200]!r}" if text else "Call worked but the answer was empty (raise max_tokens or try another model).")
    return 0 if text else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
