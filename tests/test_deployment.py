import os
from pathlib import Path
import sqlite3
import tempfile
import tarfile
import unittest
from unittest.mock import patch

from database import bootstrap_database
from deploy.database_backup import backup_database
from deploy.setup import initialize_deployment
from deploy.package import DEPLOYMENT_FILES, package_project
from maintenance_auth import admin_password, password_matches


class DeploymentTests(unittest.TestCase):
    def test_package_contains_database_snapshot_but_excludes_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            for name in DEPLOYMENT_FILES:
                path = project / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n")
            connection = bootstrap_database(project / "data" / "info_service.db")
            connection.close()
            (project / ".env").write_text("PRIVATE_CONFIGURATION=yes\n")
            (project / ".secrets").mkdir()
            (project / ".secrets" / "admin_password").write_text("do-not-package-me")
            output = Path(directory) / "deploy.tar.gz"
            package_project(project, output)
            with tarfile.open(output) as archive:
                names = set(archive.getnames())
                self.assertEqual(names, set(DEPLOYMENT_FILES) | {"data/info_service.db"})
                snapshot = Path(directory) / "snapshot.db"
                snapshot.write_bytes(archive.extractfile("data/info_service.db").read())
            connection = sqlite3.connect(snapshot)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertGreaterEqual(connection.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0], 19)
            connection.close()
            with self.assertRaises(FileExistsError):
                package_project(project, output)

    def test_password_file_is_required_and_missing_configuration_fails_closed(self):
        with patch.dict(os.environ, {"INFODESK_REQUIRE_ADMIN_PASSWORD": "true"}, clear=True):
            with self.assertRaises(RuntimeError):
                admin_password()
            with patch.dict(os.environ, {"INFODESK_ADMIN_PASSWORD_FILE": "/missing/secret"}):
                with self.assertRaises(RuntimeError):
                    admin_password()

    def test_password_file_supports_unicode_and_rejects_short_passwords(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "password"
            with patch.dict(os.environ, {"INFODESK_ADMIN_PASSWORD_FILE": str(path)}, clear=True):
                path.write_text("too-short", encoding="utf-8")
                with self.assertRaises(RuntimeError):
                    admin_password()
                expected = "管理员密码足够长的测试字符串123456"
                path.write_text(expected + "\n", encoding="utf-8")
                self.assertEqual(admin_password(), expected)
                self.assertTrue(password_matches(expected, admin_password()))
                self.assertFalse(password_matches("incorrect", admin_password()))

    def test_local_mode_remains_available_without_deployment_auth_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(admin_password())

    def test_setup_does_not_replace_existing_password_or_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".env.example").write_text("INFODESK_PORT=8501\n")
            initialize_deployment(project)
            password_file = project / ".secrets" / "admin_password"
            password = password_file.read_text()
            self.assertGreaterEqual(len(password.strip()), 32)
            (project / ".env").write_text("INFODESK_PORT=9000\n")
            self.assertEqual(initialize_deployment(project), [])
            self.assertEqual(password_file.read_text(), password)
            self.assertEqual((project / ".env").read_text(), "INFODESK_PORT=9000\n")
            self.assertEqual(password_file.stat().st_mode & 0o777, 0o444)
            self.assertEqual(password_file.parent.stat().st_mode & 0o777, 0o700)

    def test_database_backup_is_consistent_and_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "source.db"
            backup_path = Path(directory) / "backups" / "backup.db"
            source = bootstrap_database(source_path)
            expected = source.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
            backup_database(source_path, backup_path)
            target = sqlite3.connect(backup_path)
            self.assertEqual(target.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0], expected)
            self.assertEqual(target.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            target.close()
            with self.assertRaises(FileExistsError):
                backup_database(source_path, backup_path)
            source.close()
