"""Spreadsheet <-> curated JSON, so venues can be filled in a spreadsheet instead of by hand.

Usage (from backend/):
  python scripts/curated_from_csv.py export curated.csv   # write a CSV with one row per curated id
  python scripts/curated_from_csv.py import curated.csv   # copy filled-in facts back into the JSON

Only factual columns are imported (name, address, url, verified_on, cost_cad, travel_minutes,
duration_hours, diet_tags). Empty cells stay null. diet_tags are separated by ';'.
Category, mode and social flags stay as defined in the JSON.
"""

import csv
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import config  # noqa: E402

COLUMNS = ["id", "what_to_find", "category", "name", "address", "url", "verified_on",
           "cost_cad", "travel_minutes", "duration_hours", "diet_tags"]
NUMBERS = {"cost_cad": lambda v: round(float(v)), "travel_minutes": lambda v: round(float(v)), "duration_hours": float}


def export(path: Path, entries: list[dict]) -> None:
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for e in entries:
            row = {c: e.get(c) for c in COLUMNS}
            row["name"] = "" if str(e["name"]).startswith("TODO") else e["name"]
            row["diet_tags"] = ";".join(e.get("diet_tags") or [])
            w.writerow({k: "" if v is None else v for k, v in row.items()})
    print(f"Wrote {len(entries)} rows to {path}. Fill name, address, url (https://), verified_on (YYYY-MM-DD), the rest if known.")


def parse_row(row: dict) -> dict:
    out = {}
    for col in ("name", "address", "url", "verified_on"):
        val = (row.get(col) or "").strip()
        if val:
            out[col] = val
    if "url" in out and not out["url"].startswith("https://"):
        raise ValueError(f"url must start with https:// ({out['url']})")
    if "verified_on" in out:
        datetime.date.fromisoformat(out["verified_on"])
    for col, typ in NUMBERS.items():
        val = (row.get(col) or "").strip().lstrip("$")
        if val:
            out[col] = typ(val)
    tags = [t.strip() for t in (row.get("diet_tags") or "").split(";") if t.strip()]
    if tags:
        out["diet_tags"] = tags
    return out


def import_(path: Path, data: dict) -> tuple[int, int]:
    by_id = {e["id"]: e for e in data["entries"]}
    errors = updated = 0
    with path.open(newline="") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            entry = by_id.get((row.get("id") or "").strip())
            if entry is None:
                print(f"  row {n}: unknown id {row.get('id')!r}, skipped")
                errors += 1
                continue
            try:
                facts = parse_row(row)
            except ValueError as e:
                print(f"  row {n} ({entry['id']}): {e}")
                errors += 1
                continue
            if facts:
                entry.update(facts)
                if all(entry.get(k) for k in ("url", "address", "verified_on")):
                    entry["verification"] = "user_verified"
                updated += 1
    print(f"Updated {updated} entries, {errors} row(s) with problems (fix them and import again).")
    return updated, errors


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("export", "import"):
        print(__doc__)
        return 2
    json_path = config.DATA_DIR / config.CITY["curated_file"]
    data = json.loads(json_path.read_text())
    csv_path = Path(sys.argv[2])
    if sys.argv[1] == "export":
        export(csv_path, data["entries"])
        return 0
    updated, errors = import_(csv_path, data)
    if updated:
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print("Now run: python scripts/validate_curated.py")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
