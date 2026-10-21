"""Read-only checks for a populated or newly created knowledge database."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sqlite3

from database import DEFAULT_DB_PATH
from knowledge_dedup import normalized_title


def check_database(path: Path) -> dict:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        integrity = [row[0] for row in connection.execute("PRAGMA integrity_check")]
        rows = connection.execute("SELECT id, title, category, answer FROM knowledge_items").fetchall()
        groups = defaultdict(list)
        missing = []
        for row in rows:
            groups[normalized_title(row["title"])].append(row["id"])
            if not all(row[field].strip() for field in ("title", "category", "answer")):
                missing.append(row["id"])
        duplicates = [ids for ids in groups.values() if len(ids) > 1]
        return {
            "ok": integrity == ["ok"] and bool(rows) and not missing and not duplicates,
            "integrity": integrity,
            "knowledge_items": len(rows),
            "categories": dict(sorted(Counter(row["category"] for row in rows).items())),
            "missing_required_fields": missing,
            "duplicate_title_groups": duplicates,
        }
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    try:
        result = check_database(args.db)
    except sqlite3.Error as error:
        parser.exit(1, f"Database check failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
