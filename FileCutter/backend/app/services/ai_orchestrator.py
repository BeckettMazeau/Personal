import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp
import fitz  # PyMuPDF
from pptx import Presentation
import os
import hashlib
from app.core.config import settings
from app.core.utils import get_optimal_batch_size, clean_and_parse_json
from app.core.cache import SQLiteCache

logger = logging.getLogger(__name__)

class AIOrchestrator:
    def __init__(self, lm_studio_url: str = settings.lm_studio_url):
        self.lm_studio_url = lm_studio_url
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.cache = SQLiteCache()

    def _get_file_hash(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            return ""
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {filepath}: {e}")
            return ""

    async def _call_llm(self, messages: List[Dict[str, str]], response_format: Optional[Dict] = None) -> Optional[str]:
        """Helper to call LM Studio REST API with error handling and timeout."""
        payload = {
            "model": "local-model",
            "messages": messages,
            "temperature": 0.1,
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.lm_studio_url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
        except asyncio.TimeoutError:
            logger.error("LLM request timed out. The local LLM might be unresponsive.")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"Client error during LLM request: {e}")
            return None
        except KeyError as e:
            logger.error(f"Unexpected response format from LLM: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM request: {e}")
            return None

    async def tier_1_evaluation(self, filenames: List[str]) -> List[Dict[str, Any]]:
        """Shallow Pass: Analyze filenames to suggest deletions."""
        if not filenames:
            return []

        system_prompt = (
            "Triage files for deletion. Return JSON array of objects: "
            "'filename'(str), 'delete'(boolean, true if garbage/download, false if user-made), "
            "'confidence'(int 1-3), 'reasoning'(str). ONLY JSON."
        )

        user_prompt = "Filenames:\n" + "\n".join(filenames)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        content = await self._call_llm(messages)
        result = clean_and_parse_json(content)

        if isinstance(result, list):
            return result

        logger.error(f"LLM returned JSON, but it's not a list: {result}")
        return []

    def _extract_text(self, filepath: str, max_words: int = 500) -> str:
        """Extract up to max_words from a PDF or PPTX file."""
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return ""

        ext = os.path.splitext(filepath)[1].lower()
        text = ""

        try:
            if ext == ".pdf":
                doc = fitz.open(filepath)
                for page in doc:
                    text += page.get_text() + " "
                    if len(text.split()) >= max_words:
                        break
                doc.close()
            elif ext in [".pptx", ".ppt"]:
                prs = Presentation(filepath)
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text += shape.text + " "
                            if len(text.split()) >= max_words:
                                break
                    if len(text.split()) >= max_words:
                        break
            else:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(max_words * 6)
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {e}")
            return ""

        words = text.split()
        return " ".join(words[:max_words])

    async def tier_2_evaluation(self, filepath: str) -> Dict[str, Any]:
        """Deep Pass: Extract text and evaluate content contextually."""
        text = await asyncio.to_thread(self._extract_text, filepath)

        lower_path = filepath.lower()
        lower_content = text.lower()
        if "homework" in lower_path or "homework" in lower_content or "report" in lower_path or "report" in lower_content:
            logger.info(f"Protected item detected: {filepath}")
            return {"filename": os.path.basename(filepath), "delete": False, "confidence": 1, "reasoning": "Protected item detected by static rule (homework/report)."}

        if not text.strip():
            return {
                "filename": os.path.basename(filepath),
                "delete": False,
                "confidence": 1,
                "reasoning": "Could not extract text for analysis."
            }

        system_prompt = (
            "You are an AI assistant helping to evaluate document content. "
            "Read the extracted text from a document and determine if it is a "
            "'unique user-generated report/homework' (do not delete) OR "
            "'generic downloaded documentation/garbage' (can be deleted). "
            "Return a JSON object with keys: "
            "'delete' (boolean, true if garbage/downloaded doc, false if user-generated), "
            "'confidence' (integer 1-3), and 'reasoning' (string). "
            "Respond ONLY with the JSON object."
        )

        user_prompt = f"Extracted Text:\n{text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        content = await self._call_llm(messages)
        result = clean_and_parse_json(content)

        if result and isinstance(result, dict):
            result["filename"] = os.path.basename(filepath)
            return result

        return {
            "filename": os.path.basename(filepath),
            "delete": False,
            "confidence": 1,
            "reasoning": "Failed to parse LLM response format." if content else "LLM failed to respond during deep pass."
        }

    async def process_files(self, filepaths: List[str]) -> List[Dict[str, Any]]:
        """Run the complete 2-tier evaluation pipeline."""
        final_results = []
        uncached_filepaths = []
        filepath_hash_map = {}

        for filepath in filepaths:
            file_hash = self._get_file_hash(filepath)
            filepath_hash_map[filepath] = file_hash
            cached_result = self.cache.get(file_hash)
            if cached_result:
                final_results.append(cached_result)
            else:
                uncached_filepaths.append(filepath)

        if not uncached_filepaths:
            return final_results

        filenames = [os.path.basename(p) for p in uncached_filepaths]
        filepath_map = {os.path.basename(p): p for p in uncached_filepaths}

        batch_size = get_optimal_batch_size()
        # chunk filenames instead of FileObject list, so we can't use batch_files directly
        # or we adapt batch_files
        filename_batches = [filenames[i:i + batch_size] for i in range(0, len(filenames), batch_size)]

        tier_1_results = []
        for batch in filename_batches:
            batch_results = await self.tier_1_evaluation(batch)
            tier_1_results.extend(batch_results)

        tier_2_tasks = []
        tier_2_items = []

        for item in tier_1_results:
            confidence = item.get("confidence", 1)
            filename = item.get("filename", "")

            if confidence < 3 and filename in filepath_map:
                filepath = filepath_map[filename]
                tier_2_tasks.append(self.tier_2_evaluation(filepath))
                tier_2_items.append((filepath, item))
            else:
                final_results.append(item)
                if filename in filepath_map:
                    self.cache.set(filepath_hash_map[filepath_map[filename]], item)

        if tier_2_tasks:
            tier_2_outputs = await asyncio.gather(*tier_2_tasks)
            for (filepath, original_item), tier_2_result in zip(tier_2_items, tier_2_outputs):
                tier_2_result["reasoning"] = f"Tier 1 reasoning: {original_item.get('reasoning')}. Tier 2 reasoning: {tier_2_result.get('reasoning')}"
                final_results.append(tier_2_result)
                self.cache.set(filepath_hash_map[filepath], tier_2_result)

        return final_results
