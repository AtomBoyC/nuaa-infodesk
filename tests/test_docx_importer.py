import unittest
from pathlib import Path

from docx_importer import (
    QuestionAnswer,
    classify_question,
    deduplicate_document_entries,
    normalize_question,
    parse_question_answers,
)


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
        self.assertEqual(classify_question("校园卡丢失怎么办？", "信息系统知识库问答版.docx"), "服务大厅")
        self.assertEqual(classify_question("i.南航 APP 如何登录？", "信息系统知识库问答版.docx"), "信息系统")

    def test_normalizes_question_spacing_and_punctuation(self):
        self.assertEqual(normalize_question("如何使用 VPN？"), normalize_question("如何使用vpn"))

    def test_deduplicates_questions_and_prefers_newer_document_version(self):
        old_shared = QuestionAnswer("新账号该如何登录？", ("2023 年答案",))
        old_unique = QuestionAnswer("旧版独有问题？", ("保留此答案",))
        new_shared = QuestionAnswer("新账号该如何登录", ("2024 年答案",))

        entries = deduplicate_document_entries(
            (
                (Path("信息系统知识库问答版(2023).docx"), (old_shared, old_unique)),
                (Path("信息系统知识库问答版(2024).docx"), (new_shared,)),
            )
        )

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0][0].name, "信息系统知识库问答版(2024).docx")
        self.assertEqual(entries[0][1].answer_lines, ("2024 年答案",))
        self.assertEqual(entries[1][1], old_unique)


if __name__ == "__main__":
    unittest.main()
