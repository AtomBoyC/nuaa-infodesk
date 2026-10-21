"""Back up the live SQLite database using its online backup API."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from database import DEFAULT_DB_PATH


def backup_database(source_path: Path, output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"Backup already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(f"{source_path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(output_path)
        try:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Backup integrity check failed.")
        finally:
            target.close()
    finally:
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = args.output or args.db.parent / "backups" / f"info_service_{timestamp}.db"
    backup_database(args.db, output)
    print(f"Backup saved: {output}")


if __name__ == "__main__":
    main()
