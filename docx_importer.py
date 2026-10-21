from __future__ import annotations

"""Import question-and-answer paragraphs from local Word documents into SQLite."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha1
from pathlib import Path
import re
from typing import Iterable
import unicodedata
from xml.etree import ElementTree
from zipfile import ZipFile

from database import DEFAULT_DB_PATH, bootstrap_database, replace_imported_document_items
from info_service_assistant import KnowledgeItem
from knowledge_taxonomy import canonical_category


WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
QUESTION_PREFIX = re.compile(r"^问\s*[：:]+\s*")
ANSWER_PREFIX = re.compile(r"^答\s*[：:;；]+\s*")
DOCUMENT_YEAR = re.compile(r"(?:19|20)\d{2}")


@dataclass(frozen=True)
class QuestionAnswer:
    question: str
    answer_lines: tuple[str, ...]


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_question(value: str) -> str:
    """Build a stable key so cosmetic punctuation and spacing do not create duplicates."""
    normalized = unicodedata.normalize("NFKC", compact_text(value)).casefold()
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def document_version(path: Path) -> int:
    years = [int(value) for value in DOCUMENT_YEAR.findall(path.name)]
    return max(years, default=0)


def deduplicate_document_entries(
    documents: Iterable[tuple[Path, Iterable[QuestionAnswer]]],
) -> list[tuple[Path, QuestionAnswer]]:
    """Merge repeated questions, preferring newer named editions and then later inputs."""
    selected: dict[
        str,
        tuple[tuple[int, int], int, Path, QuestionAnswer],
    ] = {}
    next_position = 0

    for source_order, (path, entries) in enumerate(documents):
        priority = (document_version(path), source_order)
        for entry in entries:
            key = normalize_question(entry.question)
            current = selected.get(key)
            if current is None:
                selected[key] = (priority, next_position, path, entry)
                next_position += 1
            elif priority >= current[0]:
                selected[key] = (priority, current[1], path, entry)

    return [
        (path, entry)
        for _, _, path, entry in sorted(selected.values(), key=lambda value: value[1])
    ]


def read_docx_paragraphs(path: Path) -> list[str]:
    """Read Word paragraphs with the standard library, avoiding extra dependencies."""
    with ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NAMESPACE}t" and node.text:
                parts.append(node.text)
            elif node.tag in {f"{WORD_NAMESPACE}br", f"{WORD_NAMESPACE}cr"}:
                parts.append("\n")
            elif node.tag == f"{WORD_NAMESPACE}tab":
                parts.append(" ")
        value = compact_text("".join(parts))
        if value:
            paragraphs.append(value)
    return paragraphs


def parse_question_answers(paragraphs: Iterable[str]) -> list[QuestionAnswer]:
    entries: list[QuestionAnswer] = []
    question = ""
    answer_lines: list[str] = []
    answer_started = False

    def save_current() -> None:
        nonlocal question, answer_lines, answer_started
        if question and answer_lines:
            entries.append(QuestionAnswer(question, tuple(answer_lines)))
        question = ""
        answer_lines = []
        answer_started = False

    for paragraph in paragraphs:
        value = compact_text(paragraph)
        if QUESTION_PREFIX.match(value):
            save_current()
            question = QUESTION_PREFIX.sub("", value).rstrip("=＝").strip()
            continue
        if question and ANSWER_PREFIX.match(value):
            answer = ANSWER_PREFIX.sub("", value)
            if answer:
                answer_lines.append(answer)
            answer_started = True
            continue
        if question and answer_started:
            answer_lines.append(value)
    save_current()
    return entries


def classify_question(question: str, source_name: str) -> str:
    text = question.lower()
    if "网络知识库" in source_name:
        return "网络服务"
    rules = (
        ("网络服务", ("vpn", "校外", "网络", "无线", "校园网", "5g")),
        ("软件服务", ("正版软件", "软件")),
        ("协同办公", ("邮箱", "邮件", "云盘", "oa")),
        ("账号与安全", ("统一身份认证", "账号", "密码", "企业号", "人脸")),
        ("校园服务", ("校园卡", "门禁", "电费", "照片")),
        ("业务系统", ("财务", "教务", "教师个人主页", "i.南航app")),
    )
    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            return canonical_category(category)
    return canonical_category("信息系统服务")


def question_tags(question: str, category: str, source_name: str) -> tuple[str, ...]:
    keywords = [category, source_name.replace(".docx", ""), question]
    for token in re.findall(r"[A-Za-z0-9.]+|[\u4e00-\u9fff]{2,}", question):
        if token not in {"怎么办", "如何", "怎么", "哪里", "什么"}:
            keywords.append(token)
    return tuple(dict.fromkeys(keywords))


def entries_to_items(entries: Iterable[QuestionAnswer], source_path: Path) -> list[KnowledgeItem]:
    source_name = source_path.name
    updated = datetime.fromtimestamp(source_path.stat().st_mtime).date().isoformat()
    items: list[KnowledgeItem] = []
    for entry in entries:
        answer = "\n".join(entry.answer_lines)
        category = classify_question(entry.question, source_name)
        item_id = sha1(f"{source_name}\n{entry.question}".encode("utf-8")).hexdigest()[:16]
        items.append(
            KnowledgeItem(
                id=f"docx-{item_id}",
                title=entry.question,
                category=category,
                audience="全校师生",
                summary=compact_text(answer)[:150],
                answer=answer,
                steps=entry.answer_lines,
                source=f"本地问答资料：{source_name}",
                owner="信息化处知识库管理员",
                updated=updated,
                tags=question_tags(entry.question, category, source_name),
            )
        )
    return items


def import_documents(paths: Iterable[Path], db_path: Path | str, *, dry_run: bool = False) -> list[KnowledgeItem]:
    documents: list[tuple[Path, list[QuestionAnswer]]] = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"document not found: {path}")
        entries = parse_question_answers(read_docx_paragraphs(path))
        if len(entries) < 5:
            raise ValueError(f"only {len(entries)} Q&A entries found in {path.name}; import aborted")
        documents.append((path, entries))

    if not documents:
        raise ValueError("no documents supplied; existing knowledge was not changed")

    all_items = [
        entries_to_items((entry,), source_path)[0]
        for source_path, entry in deduplicate_document_entries(documents)
    ]

    if not dry_run:
        connection = bootstrap_database(db_path)
        try:
            replace_imported_document_items(connection, all_items)
        finally:
            connection.close()
    return all_items


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import local DOCX Q&A documents into SQLite.")
    parser.add_argument("documents", nargs="+", type=Path, help="one or more .docx files")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    items = import_documents(args.documents, args.db, dry_run=args.dry_run)
    action = "would import" if args.dry_run else "imported"
    for item in items:
        print(f"{item.category} | {item.title}")
    print(f"Finished: {action} {len(items)} DOCX knowledge items.")


if __name__ == "__main__":
    main()
