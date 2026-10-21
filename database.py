from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Iterable

from info_service_assistant import KNOWLEDGE_BASE, KnowledgeItem
from knowledge_taxonomy import CATEGORY_ALIASES, canonical_category


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "info_service.db"


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            audience TEXT NOT NULL,
            summary TEXT NOT NULL,
            answer TEXT NOT NULL,
            steps TEXT NOT NULL,
            source TEXT NOT NULL,
            owner TEXT NOT NULL,
            updated TEXT NOT NULL,
            tags TEXT NOT NULL,
            link TEXT NOT NULL DEFAULT '',
            is_seed INTEGER NOT NULL DEFAULT 0,
            is_published INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS feedback_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_type TEXT NOT NULL CHECK (feedback_type IN ('helpful', 'manual')),
            question TEXT NOT NULL DEFAULT '',
            knowledge_item_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_knowledge_category
            ON knowledge_items(category);

        CREATE INDEX IF NOT EXISTS idx_feedback_type
            ON feedback_events(feedback_type);
        """
    )
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(knowledge_items)")}
    if "is_published" not in columns:
        connection.execute(
            "ALTER TABLE knowledge_items ADD COLUMN is_published INTEGER NOT NULL DEFAULT 1"
        )
        connection.execute(
            "UPDATE knowledge_items SET is_published = 0 WHERE id LIKE 'custom-%'"
        )
    connection.commit()


def serialize_values(values: Iterable[str]) -> str:
    return "\n".join(value.strip() for value in values if value.strip())


def deserialize_values(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.splitlines() if part.strip())


def row_to_knowledge_item(row: sqlite3.Row) -> KnowledgeItem:
    return KnowledgeItem(
        id=row["id"],
        title=row["title"],
        category=row["category"],
        audience=row["audience"],
        summary=row["summary"],
        answer=row["answer"],
        steps=deserialize_values(row["steps"]),
        source=row["source"],
        owner=row["owner"],
        updated=row["updated"],
        tags=deserialize_values(row["tags"]),
        link=row["link"],
    )


def upsert_knowledge_item(
    connection: sqlite3.Connection,
    item: KnowledgeItem,
    *,
    is_seed: bool = False,
    is_published: bool = True,
    commit: bool = True,
) -> None:
    connection.execute(
        """
        INSERT INTO knowledge_items (
            id, title, category, audience, summary, answer, steps, source,
            owner, updated, tags, link, is_seed, is_published
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            category = excluded.category,
            audience = excluded.audience,
            summary = excluded.summary,
            answer = excluded.answer,
            steps = excluded.steps,
            source = excluded.source,
            owner = excluded.owner,
            updated = excluded.updated,
            tags = excluded.tags,
            link = excluded.link,
            is_seed = excluded.is_seed,
            is_published = excluded.is_published
        """,
        (
            item.id,
            item.title,
            canonical_category(item.category),
            item.audience,
            item.summary,
            item.answer,
            serialize_values(item.steps),
            item.source,
            item.owner,
            item.updated,
            serialize_values(item.tags),
            item.link,
            1 if is_seed else 0,
            1 if is_published else 0,
        ),
    )
    if commit:
        connection.commit()


def replace_imported_site_items(
    connection: sqlite3.Connection,
    items: Iterable[KnowledgeItem],
) -> None:
    """Atomically replace rows created by the public website importer."""
    with connection:
        connection.execute("DELETE FROM knowledge_items WHERE id LIKE 'xxhc-%'")
        for item in items:
            upsert_knowledge_item(connection, item, is_seed=False, commit=False)


def replace_imported_document_items(
    connection: sqlite3.Connection,
    items: Iterable[KnowledgeItem],
) -> None:
    """Atomically replace rows created by the local DOCX question bank importer."""
    with connection:
        connection.execute("DELETE FROM knowledge_items WHERE id LIKE 'docx-%'")
        for item in items:
            upsert_knowledge_item(connection, item, is_seed=False, commit=False)


def seed_default_knowledge(connection: sqlite3.Connection) -> None:
    for item in KNOWLEDGE_BASE:
        existing = connection.execute(
            "SELECT 1 FROM knowledge_items WHERE id = ?",
            (item.id,),
        ).fetchone()
        if existing is None:
            upsert_knowledge_item(connection, item, is_seed=True)


def normalize_knowledge_categories(connection: sqlite3.Connection) -> None:
    """Migrate historical labels to the compact category system used by the UI."""
    for old_category, new_category in CATEGORY_ALIASES.items():
        connection.execute(
            "UPDATE knowledge_items SET category = ? WHERE category = ?",
            (new_category, old_category),
        )
    connection.commit()


def bootstrap_database(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = connect(db_path)
    init_db(connection)
    seed_default_knowledge(connection)
    normalize_knowledge_categories(connection)
    return connection


def list_knowledge_items(
    connection: sqlite3.Connection, *, include_drafts: bool = True
) -> list[KnowledgeItem]:
    rows = connection.execute(
        """
        SELECT *
        FROM knowledge_items
        WHERE is_published = 1 OR ?
        ORDER BY is_seed ASC, created_at DESC, title ASC
        """,
        (include_drafts,),
    ).fetchall()
    return [row_to_knowledge_item(row) for row in rows]


def add_knowledge_item(connection: sqlite3.Connection, item: KnowledgeItem) -> None:
    upsert_knowledge_item(connection, item, is_seed=False, is_published=False)


def publish_knowledge_item(connection: sqlite3.Connection, item_id: str) -> None:
    with connection:
        result = connection.execute(
            "UPDATE knowledge_items SET is_published = 1 WHERE id = ? AND is_published = 0",
            (item_id,),
        )
        if result.rowcount != 1:
            raise ValueError("draft was not found")


def record_feedback(
    connection: sqlite3.Connection,
    feedback_type: str,
    *,
    question: str = "",
    knowledge_item_id: str = "",
) -> None:
    connection.execute(
        """
        INSERT INTO feedback_events (feedback_type, question, knowledge_item_id)
        VALUES (?, ?, ?)
        """,
        (feedback_type, question, knowledge_item_id),
    )
    connection.commit()


def feedback_summary(connection: sqlite3.Connection) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT feedback_type, COUNT(*) AS count
        FROM feedback_events
        GROUP BY feedback_type
        """
    ).fetchall()
    summary = {"helpful": 0, "manual": 0}
    for row in rows:
        summary[row["feedback_type"]] = row["count"]
    return summary
