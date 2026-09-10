import unittest

from info_service_assistant import KNOWLEDGE_BASE, KnowledgeItem, build_answer, categories, match_knowledge, rank_knowledge


class InfoServiceAssistantTests(unittest.TestCase):
    def test_matches_campus_network_question(self):
        item, confidence, related = match_knowledge("校园网连不上怎么办")

        self.assertEqual(item.id, "campus-network")
        self.assertGreaterEqual(confidence, 60)
        self.assertEqual(related[0].id, "campus-network")

    def test_matches_software_download_question(self):
        item, confidence, _related = match_knowledge("正版软件平台怎么下载 Office")

        self.assertEqual(item.id, "software-license")
        self.assertGreaterEqual(confidence, 60)

    def test_matches_multimedia_classroom_question(self):
        item, confidence, _related = match_knowledge("多媒体教室投影坏了怎么报修")

        self.assertEqual(item.id, "classroom-multimedia")
        self.assertGreaterEqual(confidence, 60)

    def test_low_confidence_answer_is_marked_as_related_advice(self):
        item = KNOWLEDGE_BASE[0]
        answer = build_answer("饭卡在哪里补办", item, 42)

        self.assertIn("没有完全匹配", answer)
        self.assertIn(item.title, answer)

    def test_matches_unspaced_chinese_question_to_service_phrase(self):
        correct_item = KnowledgeItem(
            id="remote-access",
            title="校外访问校内途径",
            category="网络服务",
            audience="全校师生",
            summary="可通过 VPN 访问校内资源。",
            answer="使用 VPN 访问校内资源。",
            steps=("登录 VPN。",),
            source="测试",
            owner="测试",
            updated="2026-09-01",
            tags=("校外访问", "校内资源", "VPN"),
        )
        unrelated_item = KnowledgeItem(
            id="software-faq",
            title="如何下载安装 MathType",
            category="常见问题",
            audience="全校师生",
            summary="软件安装说明。",
            answer="下载安装说明。",
            steps=("下载软件。",),
            source="测试",
            owner="测试",
            updated="2026-09-01",
            tags=("如何", "软件"),
        )

        item, confidence, _related = match_knowledge(
            "如何在校外访问校内资源",
            (unrelated_item, correct_item),
        )

        self.assertEqual(item.id, "remote-access")
        self.assertGreaterEqual(confidence, 60)

    def test_orders_merged_categories_for_browsing(self):
        items = (
            KnowledgeItem("one", "一", "办事大厅", "", "", "", (), "", "", "", ()),
            KnowledgeItem("two", "二", "网络服务", "", "", "", (), "", "", "", ()),
            KnowledgeItem("three", "三", "业务系统", "", "", "", (), "", "", "", ()),
        )

        self.assertEqual(categories(items), ["全部", "网络服务", "服务大厅", "信息系统"])

    def test_returns_multiple_ranked_candidates(self):
        ranked = rank_knowledge("校园网无法连接", KNOWLEDGE_BASE, limit=5)

        self.assertEqual(len(ranked), 5)
        self.assertEqual(ranked[0][0].id, "campus-network")
        self.assertGreater(ranked[0][1], ranked[-1][1])


if __name__ == "__main__":
    unittest.main()
