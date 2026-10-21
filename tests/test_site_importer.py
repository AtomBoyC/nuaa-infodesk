import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from info_service_assistant import KnowledgeItem
from site_importer import Page, PageParser, classify_page, crawl_public_pages, deduplicate_items, import_site, normalized_url, page_to_knowledge_item


class SiteImporterTests(unittest.TestCase):
    def test_normalized_url_keeps_only_public_html_in_same_site(self):
        base = "https://xxhc.nuaa.edu.cn/"
        self.assertEqual(
            normalized_url(base, "/info/123.html?from=home#title"),
            "https://xxhc.nuaa.edu.cn/info/123.html",
        )
        self.assertIsNone(normalized_url(base, "https://example.com/page.html"))
        self.assertIsNone(normalized_url(base, "/_upload/notice.pdf"))
        self.assertEqual(
            normalized_url(base, "/_t2236/2025/0402/c17983a371521/page.htm"),
            "https://xxhc.nuaa.edu.cn/2025/0402/c17983a371521/page.htm",
        )

    def test_classifies_network_service_page(self):
        self.assertEqual(
            classify_page("如何登录校园网", "https://xxhc.nuaa.edu.cn/a.html", "校园网服务指南"),
            "网络服务",
        )
        self.assertEqual(
            classify_page("校外访问校内途径", "https://xxhc.nuaa.edu.cn/a.html", "使用 VPN 客户端访问"),
            "网络服务",
        )

    def test_title_rules_override_unrelated_body_keywords(self):
        self.assertEqual(
            classify_page("电子邮件", "https://xxhc.nuaa.edu.cn/a.html", "统一身份认证账号登录"),
            "协同办公",
        )
        self.assertEqual(
            classify_page("我校入选网络安全教育案例", "https://xxhc.nuaa.edu.cn/a.html", "网络安全实践"),
            "新闻动态",
        )

    def test_converts_public_page_to_knowledge_item(self):
        page = Page(
            url="https://xxhc.nuaa.edu.cn/service/vpn.html",
            title="校外访问校内途径 - 信息化处",
            text="校外访问校内途径\n师生可使用 VPN 安全访问校内资源。\n请使用统一身份认证账号登录。",
            links=(),
            article_text="师生可使用 VPN 安全访问校内资源。\n请使用统一身份认证账号登录。",
        )
        item = page_to_knowledge_item(page)
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item.category, "网络服务")
        self.assertEqual(item.link, page.url)
        self.assertTrue(item.id.startswith("xxhc-"))

    def test_extracts_paragraphs_from_website_article_container(self):
        parser = PageParser()
        parser.feed(
            "<div class='wp_articlecontent'><p>第一项说明。</p><p>第二项说明。</p></div>"
        )
        self.assertEqual(parser.article_text, "第一项说明。\n第二项说明。")

    def test_deduplicates_repeated_website_titles(self):
        short = KnowledgeItem("one", "校园卡", "服务大厅", "", "简短", "简短", (), "官网", "", "", (), "https://xxhc.nuaa.edu.cn/a.htm")
        detailed = KnowledgeItem("two", "校园卡", "服务大厅", "", "详细", "这是更完整的官网说明。", (), "官网", "", "", (), "https://xxhc.nuaa.edu.cn/b.htm")

        items = deduplicate_items((short, detailed))

        self.assertEqual([item.id for item in items], ["two"])

    def test_nested_article_divs_do_not_truncate_following_paragraphs(self):
        parser = PageParser()
        parser.feed(
            "<div class='wp_articlecontent'><div>第一项说明。</div>"
            "<p>第二项说明。<br/>第三项说明。</p></div><p>正文外的页脚。</p>"
        )
        self.assertEqual(parser.article_text, "第一项说明。\n第二项说明。\n第三项说明。")

    def test_dry_run_does_not_create_or_modify_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge.db"
            with patch("site_importer.crawl_public_pages", return_value=[]):
                import_site("https://xxhc.nuaa.edu.cn/", str(path), 3, 0, True, 50)
                self.assertFalse(path.exists())
                path.write_bytes(b"existing database is untouched")
                import_site("https://xxhc.nuaa.edu.cn/", str(path), 3, 0, True, 50)
                self.assertEqual(path.read_bytes(), b"existing database is untouched")

    def test_failed_crawl_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "knowledge.db"
            with patch("site_importer.crawl_public_pages", return_value=[]):
                with self.assertRaises(RuntimeError):
                    import_site("https://xxhc.nuaa.edu.cn/", str(path), 3, 0, False, 50)
            self.assertFalse(path.exists())

    def test_crawl_resolves_relative_links_against_current_page(self):
        base = "https://xxhc.nuaa.edu.cn/"
        urls = []

        def fetch(url):
            urls.append(url)
            links = ("/service/start.htm",) if url == base else ("next.htm",)
            return Page(url, "页面", "正文", links)

        with patch("site_importer.fetch_page", side_effect=fetch):
            list(crawl_public_pages(base, 3, 0))
        self.assertEqual(urls[-1], "https://xxhc.nuaa.edu.cn/service/next.htm")


if __name__ == "__main__":
    unittest.main()
