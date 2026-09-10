from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re
import sqlite3
import unicodedata


@dataclass(frozen=True)
class DeduplicationResult:
    duplicate_groups: int
    removed_items: int
    kept_ids: tuple[str, ...]


def normalized_title(title: str) -> str:
    value = unicodedata.normalize("NFKC", title).lower()
    return re.sub(r"[\s\W_]+", "", value, flags=re.UNICODE)


def row_quality(row: sqlite3.Row) -> tuple[int, int, int, str, str]:
    link = row["link"] or ""
    is_canonical_link = int("/_t" not in link and "/_s" not in link)
    is_content_page = int(not link.endswith("/list.htm"))
    return (
        is_canonical_link,
        is_content_page,
        len(row["answer"]),
        row["updated"],
        row["id"],
    )


def remove_exact_website_duplicates(connection: sqlite3.Connection) -> DeduplicationResult:
    """Keep one best official-site row for each normalized duplicate title."""
    rows = connection.execute(
        "SELECT id, title, answer, link, updated FROM knowledge_items WHERE id LIKE 'xxhc-%'"
    ).fetchall()
    groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        groups[normalized_title(row["title"])].append(row)

    kept_ids: list[str] = []
    delete_ids: list[str] = []
    duplicate_groups = 0
    for group in groups.values():
        if len(group) == 1:
            continue
        duplicate_groups += 1
        preferred = max(group, key=row_quality)
        kept_ids.append(preferred["id"])
        delete_ids.extend(row["id"] for row in group if row["id"] != preferred["id"])

    with connection:
        connection.executemany(
            "DELETE FROM knowledge_items WHERE id = ?",
            ((item_id,) for item_id in delete_ids),
        )
    return DeduplicationResult(duplicate_groups, len(delete_ids), tuple(kept_ids))
