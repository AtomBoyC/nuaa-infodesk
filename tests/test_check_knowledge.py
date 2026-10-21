import sqlite3
import tempfile
import unittest
from pathlib import Path

from check_knowledge import check_database
from database import bootstrap_database


class KnowledgeCheckTests(unittest.TestCase):
    def test_check_is_read_only_and_detects_missing_fields_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge.db"
            connection = bootstrap_database(path)
            connection.execute(
                """INSERT INTO knowledge_items
                    SELECT 'duplicate-id', title, category, audience, summary, '', steps,
                           source, owner, updated, tags, link, is_seed, is_published, created_at
                    FROM knowledge_items WHERE id = 'campus-network'"""
            )
            connection.commit()
            connection.close()
            before = path.read_bytes()
            result = check_database(path)
            self.assertFalse(result["ok"])
            self.assertEqual(result["missing_required_fields"], ["duplicate-id"])
            self.assertEqual(len(result["duplicate_title_groups"]), 1)
            self.assertEqual(before, path.read_bytes())

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.db"
            with self.assertRaises(sqlite3.Error):
                check_database(path)
            self.assertFalse(path.exists())
