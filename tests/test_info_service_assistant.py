import unittest

from info_service_assistant import KNOWLEDGE_BASE, build_answer, match_knowledge


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


if __name__ == "__main__":
    unittest.main()
