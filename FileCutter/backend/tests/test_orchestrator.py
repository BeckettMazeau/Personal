import unittest
from app.core.orchestrator import AIOrchestrator


class TestAIOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AIOrchestrator()

    def test_deep_pass_protects_homework_in_path(self):
        result = self.orchestrator.deep_pass(file_path="/docs/math_homework.pdf")
        self.assertEqual(result["suggested_action"], "protect")
        self.assertEqual(result["confidence_score"], 1)

    def test_deep_pass_protects_report_in_content(self):
        result = self.orchestrator.deep_pass(
            file_path="/docs/doc1.pdf", content="Annual financial report"
        )
        self.assertEqual(result["suggested_action"], "protect")
        self.assertEqual(result["confidence_score"], 1)

    def test_deep_pass_no_protection(self):
        result = self.orchestrator.deep_pass(
            file_path="/docs/random_notes.txt", content="just some notes"
        )
        self.assertEqual(result["suggested_action"], "review")
        self.assertEqual(result["confidence_score"], 2)


if __name__ == "__main__":
    unittest.main()
