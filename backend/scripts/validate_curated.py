"""Check data/curated_toronto.json. An entry is 'curated' only if url, address and verified_on are set.

Usage (from backend/): python scripts/validate_curated.py   (exit 1 on schema errors)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402
from app.candidates import curated_label, load_curated  # noqa: E402

FACT_FIELDS = ["name", "address", "url", "verified_on", "cost_cad", "travel_minutes", "duration_hours", "diet_tags"]


def main() -> int:
    path = config.DATA_DIR / config.CITY["curated_file"]
    entries = json.loads(path.read_text())["entries"]
    try:
        load_curated(path)
    except Exception as e:  # schema problem
        print(f"SCHEMA ERROR: {e}")
        return 1

    problems = 0
    for e in entries:
        label = curated_label(e)
        missing = [f for f in FACT_FIELDS if e.get(f) in (None, [], "") or (f == "name" and str(e["name"]).startswith("TODO"))]
        if e.get("url") and not str(e["url"]).startswith("https://"):
            print(f"  ! {e['id']}: url should start with https://")
            problems += 1
        print(f"{label.upper():10} {e['id']:26} missing: {', '.join(missing) or '-'}")
    n_cur = sum(curated_label(e) == "curated" for e in entries)
    print(f"\n{n_cur}/{len(entries)} entries are verified (shown as Curated); the rest are shown as Unverified.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
