import tempfile
import unittest
import sqlite3
import os
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from streamlit.util import calc_hash


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit_app.py"


class StreamlitAppTests(unittest.TestCase):
    def test_maintenance_requires_login_and_password_rotation_invalidates_session(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge.db"
            password_file = Path(directory) / "admin_password"
            password = "administrator-test-password-123"
            password_file.write_text(password)
            with patch("database.DEFAULT_DB_PATH", path), patch.dict(
                os.environ,
                {"INFODESK_ADMIN_PASSWORD_FILE": str(password_file), "INFODESK_REQUIRE_ADMIN_PASSWORD": "true"},
            ):
                app = AppTest.from_file(str(APP_PATH))
                # AppTest only offers public navigation for file-based pages;
                # callable pages use the URL hash in this pinned Streamlit version.
                app._page_hash = calc_hash("knowledge-maintenance")
                app.run(timeout=15)
                self.assertEqual(list(app.exception), [])
                self.assertFalse(any(button.label == "保存草稿" for button in app.button))
                next(field for field in app.text_input if field.label == "管理员密码").set_value("wrong")
                next(button for button in app.button if button.label == "登录").click().run()
                self.assertTrue(any("密码不正确" in error.value for error in app.error))
                self.assertFalse(any(button.label == "保存草稿" for button in app.button))

                next(field for field in app.text_input if field.label == "管理员密码").set_value(password)
                next(button for button in app.button if button.label == "登录").click().run()
                self.assertEqual(list(app.exception), [])
                self.assertTrue(any(button.label == "保存草稿" for button in app.button))

                password_file.write_text("new-administrator-password-456")
                app.run()
                self.assertFalse(any(button.label == "保存草稿" for button in app.button))
                app.session_state._database.close()

    def test_search_uses_populated_database_without_modifying_it(self):
        bundled = APP_PATH.parent / "data" / "info_service.db"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "copy.db"
            source = sqlite3.connect(f"{bundled.as_uri()}?mode=ro", uri=True)
            target = sqlite3.connect(path)
            source.backup(target)
            target.close()
            source.close()
            with patch("database.DEFAULT_DB_PATH", path):
                app = AppTest.from_file(str(APP_PATH)).run(timeout=15)
                app.text_input(key="search_input").set_value("校园网连不上怎么办")
                next(button for button in app.button if button.label == "搜索").click().run()
                self.assertEqual(list(app.exception), [])
                self.assertEqual(app.session_state.selected_candidate_id, "campus-network")
                self.assertEqual(len(app.radio[0].options), 10)
                self.assertTrue(any("96%" in option for option in app.radio[0].options))
                self.assertTrue(any("96%" not in option for option in app.radio[0].options))
                app.session_state._database.close()

    def test_home_search_and_unmatched_state(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("database.DEFAULT_DB_PATH", Path(directory) / "knowledge.db"):
                app = AppTest.from_file(str(APP_PATH)).run(timeout=15)
                self.assertEqual(list(app.exception), [])
                app.text_input(key="search_input").set_value("校园网连不上怎么办")
                next(button for button in app.button if button.label == "搜索").click().run()
                self.assertEqual(list(app.exception), [])
                self.assertEqual(app.session_state.selected_candidate_id, "campus-network")
                self.assertEqual(len(app.radio), 1)

                app.text_input(key="search_input").set_value("今天中午吃什么")
                next(button for button in app.button if button.label == "搜索").click().run()
                self.assertEqual(list(app.exception), [])
                self.assertEqual(len(app.radio), 0)
                self.assertTrue(any("暂无相关知识" in item.value for item in app.info))
                app.session_state._database.close()
