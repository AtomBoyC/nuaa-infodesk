import tempfile
import unittest
from pathlib import Path

from database import (
    add_knowledge_item,
    bootstrap_database,
    feedback_summary,
    list_knowledge_items,
    record_feedback,
)
from info_service_assistant import KnowledgeItem


class DatabaseTests(unittest.TestCase):
    def test_bootstrap_seeds_default_knowledge(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "assistant.db"

            connection = bootstrap_database(db_path)
            items = list_knowledge_items(connection)

            self.assertGreaterEqual(len(items), 19)
            self.assertTrue(any(item.id == "campus-network" for item in items))

    def test_adds_custom_knowledge_and_feedback(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "assistant.db"
            connection = bootstrap_database(db_path)
            item = KnowledgeItem(
                id="custom-test",
                title="测试条目",
                category="临时知识",
                audience="内部维护",
                summary="测试摘要",
                answer="测试答案",
                steps=("审核后发布。",),
                source="单元测试",
                owner="测试岗",
                updated="2026-09-01",
                tags=("测试",),
            )

            add_knowledge_item(connection, item)
            record_feedback(
                connection,
                "helpful",
                question="测试问题",
                knowledge_item_id="custom-test",
            )

            items = list_knowledge_items(connection)
            summary = feedback_summary(connection)
            self.assertTrue(any(entry.id == "custom-test" for entry in items))
            self.assertEqual(summary["helpful"], 1)
            self.assertEqual(summary["manual"], 0)


if __name__ == "__main__":
    unittest.main()
