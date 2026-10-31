"""Live check against real Qloo. Needs QLOO_API_KEY and the qloo CLI (Node >= 22.19).

Usage (from backend/): QLOO_API_KEY=... python scripts/smoke_live.py
Runs: version check, one search, one recommendation call; prints observed shapes; exits non-zero on failure.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402
from app.qloo_adapter import QlooAdapter, QlooError  # noqa: E402


def shape(obj, depth=0):
    if isinstance(obj, dict):
        return {k: shape(v, depth + 1) for k, v in list(obj.items())[:25]} if depth < 3 else "{...}"
    if isinstance(obj, list):
        return [shape(obj[0], depth + 1)] if obj else []
    return type(obj).__name__


async def main() -> int:
    if not os.getenv("QLOO_API_KEY"):
        print("FAIL: QLOO_API_KEY is not set. Live path not verified.")
        return 2
    try:
        version = subprocess.run([config.qloo_bin(), "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except FileNotFoundError:
        print("FAIL: qloo CLI not found")
        return 2
    print("qloo version:", version)

    adapter = QlooAdapter(mode="live", cache_dir=Path(tempfile.mkdtemp()))  # fresh cache: force real calls
    try:
        found = await adapter.search_entities("Coke Studio", "artist", 3)
        print(f"search 'Coke Studio' (artist): {len(found)} results")
        if not found:
            print("FAIL: search returned nothing")
            return 1
        print("first result:", found[0].name, found[0].entity_id)
        print("raw shape:", json.dumps(shape(found[0].raw), indent=2))

        recs = await adapter.recommend([found[0].entity_id], "place", config.CITY["qloo_location_query"], 5)
        print(f"\ninsights place in {config.CITY['name']} seeded by {found[0].name}: {len(recs)} results")
        for r in recs:
            print(f"  {r.rank}. {r.name}  affinity={r.affinity}  address={r.address}")
        if recs:
            print("raw shape:", json.dumps(shape(recs[0].raw), indent=2))
        else:
            print("FAIL: recommendation call returned nothing")
            return 1
    except QlooError as e:
        print(f"FAIL: {e.code}: {e.user_message} ({e.detail})")
        return 1
    print(f"\nOK. Qloo calls used: {adapter.calls_used}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
