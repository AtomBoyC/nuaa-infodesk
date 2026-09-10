import unittest

from docx_importer import classify_question, parse_question_answers


class DocxImporterTests(unittest.TestCase):
    def test_parses_multi_paragraph_answer(self):
        entries = parse_question_answers(
            (
                "问：校园网连不上怎么办？",
                "答：先检查网线。",
                "再更换端口测试。",
                "问：如何使用 VPN？",
                "答：访问 VPN 门户登录。",
            )
        )

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].question, "校园网连不上怎么办？")
        self.assertEqual(entries[0].answer_lines, ("先检查网线。", "再更换端口测试。"))

    def test_classifies_network_and_email_questions(self):
        self.assertEqual(classify_question("校园网连不上怎么办？", "网络知识库问答版.docx"), "网络服务")
        self.assertEqual(classify_question("如何申请学校邮箱？", "信息系统知识库问答版.docx"), "协同办公")


if __name__ == "__main__":
    unittest.main()
