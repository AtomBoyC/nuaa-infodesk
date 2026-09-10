import tempfile
import unittest
from pathlib import Path

from database import (
    add_knowledge_item,
    bootstrap_database,
    feedback_summary,
    list_knowledge_items,
    record_feedback,
    replace_imported_site_items,
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

    def test_replaces_only_imported_website_items(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "assistant.db"
            connection = bootstrap_database(db_path)
            item = KnowledgeItem(
                id="xxhc-test-page",
                title="官网条目",
                category="服务指南",
                audience="全校师生",
                summary="官网摘要",
                answer="官网答案",
                steps=("查看官网。",),
                source="官网",
                owner="信息化处",
                updated="2026-09-01",
                tags=("官网",),
            )
            replace_imported_site_items(connection, [item])

            ids = {entry.id for entry in list_knowledge_items(connection)}
            self.assertIn("xxhc-test-page", ids)
            self.assertIn("campus-network", ids)

    def test_normalizes_service_hall_category_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "assistant.db"
            connection = bootstrap_database(db_path)
            item = KnowledgeItem(
                id="service-hall-test",
                title="测试办事流程",
                category="办事大厅",
                audience="全校师生",
                summary="测试摘要",
                answer="测试答案",
                steps=("办理测试。",),
                source="单元测试",
                owner="测试岗",
                updated="2026-09-03",
                tags=("测试",),
            )
            add_knowledge_item(connection, item)

            saved = next(entry for entry in list_knowledge_items(connection) if entry.id == item.id)
            self.assertEqual(saved.category, "服务大厅")


if __name__ == "__main__":
    unittest.main()
