import unittest
import asyncio
from app.services.ai_orchestrator import AIOrchestrator

class TestAIOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = AIOrchestrator()

    def test_deep_pass_protects_homework_in_path(self):
        # We need to create a dummy file to pass the _extract_text check
        # For testing the static rule, we can just mock _extract_text
        self.orchestrator._extract_text = lambda filepath: "some text"
        result = asyncio.run(self.orchestrator.tier_2_evaluation("/docs/math_homework.pdf"))
        self.assertEqual(result["delete"], False)
        self.assertEqual(result["confidence"], 1)
        self.assertIn("Protected item", result["reasoning"])

    def test_deep_pass_protects_report_in_content(self):
        self.orchestrator._extract_text = lambda filepath: "Annual financial report"
        result = asyncio.run(self.orchestrator.tier_2_evaluation("/docs/doc1.pdf"))
        self.assertEqual(result["delete"], False)
        self.assertEqual(result["confidence"], 1)
        self.assertIn("Protected item", result["reasoning"])

if __name__ == "__main__":
    unittest.main()
