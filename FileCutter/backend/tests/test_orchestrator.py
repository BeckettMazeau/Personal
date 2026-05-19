import asyncio
import json
import sqlite3
import unittest
from unittest.mock import AsyncMock, patch

from app.services.ai_orchestrator import AIOrchestrator
from app.core.cache import SQLiteCache


def _run(coro):
    return asyncio.run(coro)


def _make_orch(db_path=None):
    """Construct an orchestrator with a controllable cache."""
    if db_path is None:
        import tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        db_path = tmp.name
    return AIOrchestrator(cache=SQLiteCache(db_path=str(db_path)))


class TestTier2Protection(unittest.TestCase):
    def setUp(self):
        self.orchestrator = _make_orch()

    def test_protects_homework_in_filename(self):
        self.orchestrator._extract_text = lambda filepath, max_words=500: "some text"
        result, cacheable = _run(
            self.orchestrator.tier_2_evaluation("/docs/homework_q3.pdf")
        )
        self.assertFalse(result["delete"])
        self.assertEqual(result["confidence"], 1)
        self.assertIn("Protected item", result["reasoning"])
        self.assertTrue(cacheable)

    def test_protects_report_in_filename(self):
        self.orchestrator._extract_text = lambda filepath, max_words=500: "some text"
        result, _ = _run(
            self.orchestrator.tier_2_evaluation("/docs/annual_report.pdf")
        )
        self.assertFalse(result["delete"])
        self.assertIn("Protected item", result["reasoning"])

    def test_does_NOT_protect_report_only_in_content(self):
        """'report' in content alone must NOT trigger the protected rule."""
        self.orchestrator._extract_text = (
            lambda filepath, max_words=500: "Annual financial report"
        )
        with patch.object(
            self.orchestrator, "_call_llm", new=AsyncMock(return_value=None)
        ):
            result, cacheable = _run(
                self.orchestrator.tier_2_evaluation("/docs/doc1.pdf")
            )
        self.assertNotIn("Protected item", result["reasoning"])
        self.assertFalse(cacheable)

    def test_protects_homework_in_content(self):
        self.orchestrator._extract_text = (
            lambda filepath, max_words=500: "Please complete the homework before Friday."
        )
        result, _ = _run(self.orchestrator.tier_2_evaluation("/docs/doc1.pdf"))
        self.assertIn("Protected item", result["reasoning"])

    def test_word_boundary_not_substring(self):
        """'reporter_bio.pdf' contains 'report' as a substring but not at a
        word boundary in the basename — should NOT trigger."""
        self.orchestrator._extract_text = lambda filepath, max_words=500: ""
        result, _ = _run(self.orchestrator.tier_2_evaluation("/docs/reporter_bio.pdf"))
        self.assertNotIn("Protected item", result["reasoning"])


class TestCallLLM(unittest.TestCase):
    def setUp(self):
        self.orchestrator = _make_orch()

    @patch("app.services.ai_orchestrator.aiohttp.ClientSession.post")
    def test_call_llm_timeout(self, mock_post):
        mock_post.side_effect = asyncio.TimeoutError("Timeout")
        result = _run(
            self.orchestrator._call_llm([{"role": "user", "content": "test"}])
        )
        self.assertIsNone(result)

    @patch("app.services.ai_orchestrator.aiohttp.ClientSession.post")
    def test_call_llm_client_error(self, mock_post):
        import aiohttp

        mock_post.side_effect = aiohttp.ClientError("boom")
        result = _run(
            self.orchestrator._call_llm([{"role": "user", "content": "test"}])
        )
        self.assertIsNone(result)


class TestTier1Evaluation(unittest.TestCase):
    def setUp(self):
        self.orchestrator = _make_orch()

    def test_happy_path(self):
        with patch.object(
            self.orchestrator,
            "_call_llm",
            new=AsyncMock(
                return_value=json.dumps(
                    {
                        "results": [
                            {"id": 0, "delete": True, "confidence": 3, "reasoning": "junk"}
                        ]
                    }
                )
            ),
        ):
            result = _run(self.orchestrator.tier_1_evaluation([(0, "file1.txt")]))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 0)
        self.assertTrue(result[0]["delete"])

    def test_drops_unknown_id(self):
        with patch.object(
            self.orchestrator,
            "_call_llm",
            new=AsyncMock(
                return_value=json.dumps(
                    {
                        "results": [
                            {"id": 0, "delete": True, "confidence": 3, "reasoning": "ok"},
                            {"id": 999, "delete": True, "confidence": 3, "reasoning": "ghost"},
                        ]
                    }
                )
            ),
        ):
            result = _run(self.orchestrator.tier_1_evaluation([(0, "file1.txt")]))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], 0)

    def test_drops_invalid_schema(self):
        with patch.object(
            self.orchestrator,
            "_call_llm",
            new=AsyncMock(
                return_value=json.dumps(
                    {"results": [{"id": 0, "delete": True, "confidence": 5}]}
                )
            ),
        ):
            result = _run(self.orchestrator.tier_1_evaluation([(0, "file1.txt")]))
        self.assertEqual(result, [])

    def test_invalid_json(self):
        with patch.object(
            self.orchestrator, "_call_llm", new=AsyncMock(return_value="not json")
        ):
            result = _run(self.orchestrator.tier_1_evaluation([(0, "file1.txt")]))
        self.assertEqual(result, [])


class TestProcessFiles(unittest.TestCase):
    def test_duplicate_basenames_in_different_dirs(self):
        import tempfile, pathlib

        with tempfile.TemporaryDirectory() as td:
            tdp = pathlib.Path(td)
            d1, d2 = tdp / "a", tdp / "b"
            d1.mkdir(); d2.mkdir()
            f1 = d1 / "doc.txt"; f1.write_text("alpha")
            f2 = d2 / "doc.txt"; f2.write_text("beta")
            db = tdp / "cache.db"
            orch = _make_orch(db)

            llm_response = json.dumps({
                "results": [
                    {"id": 0, "delete": True, "confidence": 3, "reasoning": "junk0"},
                    {"id": 1, "delete": False, "confidence": 3, "reasoning": "keep1"},
                ]
            })
            with patch.object(orch, "_call_llm", new=AsyncMock(return_value=llm_response)):
                results = _run(orch.process_files([str(f1), str(f2)]))

            self.assertEqual(len(results), 2)
            delete_flags = sorted(r["delete"] for r in results)
            self.assertEqual(delete_flags, [False, True])

    def test_hallucinated_id_dropped(self):
        import tempfile, pathlib

        with tempfile.TemporaryDirectory() as td:
            tdp = pathlib.Path(td)
            f = tdp / "real.txt"; f.write_text("x")
            db = tdp / "cache.db"
            orch = _make_orch(db)

            llm_response = json.dumps({
                "results": [
                    {"id": 0, "delete": True, "confidence": 3, "reasoning": "ok"},
                    {"id": 42, "delete": True, "confidence": 3, "reasoning": "ghost"},
                ]
            })
            with patch.object(orch, "_call_llm", new=AsyncMock(return_value=llm_response)):
                results = _run(orch.process_files([str(f)]))

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["filename"], "real.txt")

    def test_tier2_failure_not_cached(self):
        """A Tier-2 LLM failure must not write to the cache."""
        import tempfile, pathlib

        with tempfile.TemporaryDirectory() as td:
            tdp = pathlib.Path(td)
            f = tdp / "doc.txt"; f.write_text("some real content here")
            db = tdp / "cache.db"
            orch = _make_orch(db)

            call_count = {"n": 0}

            async def fake_call(messages, response_format=None):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return json.dumps({
                        "results": [
                            {"id": 0, "delete": True, "confidence": 1, "reasoning": "maybe"}
                        ]
                    })
                return None

            with patch.object(orch, "_call_llm", new=AsyncMock(side_effect=fake_call)):
                _run(orch.process_files([str(f)]))

            conn = sqlite3.connect(str(db))
            try:
                row_count = conn.execute(
                    "SELECT COUNT(*) FROM file_assessments"
                ).fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(row_count, 0)

    def test_tier2_success_is_cached(self):
        import tempfile, pathlib

        with tempfile.TemporaryDirectory() as td:
            tdp = pathlib.Path(td)
            f = tdp / "doc.txt"; f.write_text("some real content here")
            db = tdp / "cache.db"
            orch = _make_orch(db)

            call_count = {"n": 0}

            async def fake_call(messages, response_format=None):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return json.dumps({
                        "results": [
                            {"id": 0, "delete": True, "confidence": 1, "reasoning": "maybe"}
                        ]
                    })
                return json.dumps({"delete": True, "confidence": 3, "reasoning": "garbage"})

            with patch.object(orch, "_call_llm", new=AsyncMock(side_effect=fake_call)):
                _run(orch.process_files([str(f)]))

            conn = sqlite3.connect(str(db))
            try:
                row_count = conn.execute(
                    "SELECT COUNT(*) FROM file_assessments"
                ).fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(row_count, 1)


if __name__ == "__main__":
    unittest.main()
