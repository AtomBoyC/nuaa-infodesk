import unittest
from dataclasses import replace

from info_service_assistant import KNOWLEDGE_BASE, KnowledgeItem, build_answer, categories, confidence_for_score, match_knowledge, rank_knowledge


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

    def test_network_question_does_not_prefer_printer_with_generic_filler(self):
        printer = replace(
            KNOWLEDGE_BASE[1],
            id="printer",
            title="网络打印机连不上怎么办？",
            summary="检查打印机连接。",
            answer="检查打印机是否与设备处于同一局域网。",
            tags=("网络服务", "网络打印机连不上怎么办？"),
        )
        ranked = rank_knowledge("校园网连不上怎么办？", (printer, KNOWLEDGE_BASE[1]))
        self.assertEqual(ranked[0][0].id, "campus-network")
        self.assertGreater(ranked[0][1], ranked[1][1])
        self.assertGreater(confidence_for_score(ranked[0][1]), confidence_for_score(ranked[1][1]))

    def test_explicit_vpn_query_does_not_prefer_router_fault(self):
        router = replace(
            KNOWLEDGE_BASE[1],
            title="使用路由器上不了网怎么办？",
            tags=("路由器",),
        )
        ranked = rank_knowledge("VPN 连不上", (router, KNOWLEDGE_BASE[2]))
        self.assertEqual(ranked[0][0].id, "vpn-access")

    def test_unrelated_and_filler_questions_have_no_candidates(self):
        for question in ("今天中午吃什么", "怎么办", "asdfghjkl", ""):
            with self.subTest(question=question):
                self.assertEqual(rank_knowledge(question), [])
                item, confidence, related = match_knowledge(question)
                self.assertEqual(confidence, 0)
                self.assertEqual(related, [])
                self.assertNotIn(item.answer, build_answer(question, item, confidence))

    def test_empty_knowledge_base_has_clear_error(self):
        with self.assertRaisesRegex(ValueError, "knowledge base is empty"):
            match_knowledge("校园网", ())


if __name__ == "__main__":
    unittest.main()
