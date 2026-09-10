import tempfile
import unittest
from pathlib import Path

from database import add_knowledge_item, bootstrap_database, list_knowledge_items
from info_service_assistant import KnowledgeItem
from knowledge_dedup import remove_exact_website_duplicates


class KnowledgeDedupTests(unittest.TestCase):
    def test_removes_only_duplicate_website_titles(self):
        with tempfile.TemporaryDirectory() as directory:
            connection = bootstrap_database(Path(directory) / "assistant.db")
            for item in (
                KnowledgeItem("xxhc-duplicate-one", "校园卡", "服务大厅", "", "摘要", "短答案", (), "官网", "", "2026-09-01", (), "https://xxhc.nuaa.edu.cn/_t2236/card.htm"),
                KnowledgeItem("xxhc-duplicate-two", "校园卡", "服务大厅", "", "摘要", "内容更完整的答案", (), "官网", "", "2026-09-02", (), "https://xxhc.nuaa.edu.cn/card.htm"),
                KnowledgeItem("custom-same-title", "校园卡", "服务大厅", "", "摘要", "人工维护答案", (), "人工", "", "2026-09-03", ()),
            ):
                add_knowledge_item(connection, item)

            result = remove_exact_website_duplicates(connection)
            ids = {item.id for item in list_knowledge_items(connection)}

            self.assertEqual(result.duplicate_groups, 1)
            self.assertEqual(result.removed_items, 1)
            self.assertIn("xxhc-duplicate-two", ids)
            self.assertIn("custom-same-title", ids)


if __name__ == "__main__":
    unittest.main()
