import unittest
import asyncio
from unittest.mock import patch
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

    @patch("app.services.ai_orchestrator.aiohttp.ClientSession.post")
    def test_call_llm_timeout(self, mock_post):
        mock_post.side_effect = asyncio.TimeoutError("Timeout")
        result = asyncio.run(self.orchestrator._call_llm([{"role": "user", "content": "test"}]))
        self.assertIsNone(result)

    @patch("app.services.ai_orchestrator.aiohttp.ClientSession.post")
    def test_call_llm_client_error(self, mock_post):
        import aiohttp
        mock_post.side_effect = aiohttp.ClientError("Client error")
        result = asyncio.run(self.orchestrator._call_llm([{"role": "user", "content": "test"}]))
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()

    @patch("app.services.ai_orchestrator.sqlite3.connect")
    def test_cache_hit(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('{"filename": "test.txt", "delete": true, "confidence": 3, "reasoning": "cached"}',)

        result = self.orchestrator._get_from_cache("dummy_hash")

        self.assertIsNotNone(result)
        self.assertEqual(result["confidence"], 3)
        self.assertEqual(result["reasoning"], "cached")
        mock_cursor.execute.assert_called_once_with("SELECT result FROM file_assessments WHERE hash = ?", ("dummy_hash",))

    @patch("app.services.ai_orchestrator.sqlite3.connect")
    def test_cache_miss(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = self.orchestrator._get_from_cache("dummy_hash")

        self.assertIsNone(result)
        mock_cursor.execute.assert_called_once_with("SELECT result FROM file_assessments WHERE hash = ?", ("dummy_hash",))

    @patch("app.services.ai_orchestrator.sqlite3.connect")
    def test_save_to_cache(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        self.orchestrator._save_to_cache("dummy_hash", {"test": "data"})

        mock_cursor.execute.assert_called_once_with("INSERT OR REPLACE INTO file_assessments (hash, result) VALUES (?, ?)", ("dummy_hash", '{"test": "data"}'))
        mock_conn.commit.assert_called_once()

    @patch("app.services.ai_orchestrator.AIOrchestrator._call_llm")
    def test_tier_1_evaluation_success(self, mock_call_llm):
        mock_call_llm.return_value = '```json\n[{"filename": "file1.txt", "delete": true, "confidence": 3, "reasoning": "junk"}]\n```'

        result = asyncio.run(self.orchestrator.tier_1_evaluation(["file1.txt"]))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["filename"], "file1.txt")
        self.assertTrue(result[0]["delete"])

    @patch("app.services.ai_orchestrator.AIOrchestrator._call_llm")
    def test_tier_1_evaluation_invalid_json(self, mock_call_llm):
        mock_call_llm.return_value = 'This is not json'

        result = asyncio.run(self.orchestrator.tier_1_evaluation(["file1.txt"]))

        self.assertEqual(len(result), 0)
