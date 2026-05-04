import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
import aiohttp
import fitz  # PyMuPDF
from pptx import Presentation
import os
import sqlite3
import hashlib
from app.core.config import settings
from app.core.utils import get_optimal_batch_size, batch_files

logger = logging.getLogger(__name__)


import json
import os

class SettingsManager:
    def __init__(self, config_file: str = "config.json"):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.config_file = os.path.join(base_dir, config_file)

    def get_selected_model(self) -> str:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    return data.get("selected_model", "local-model")
            except Exception as e:
                logger.error(f"Error reading config: {e}")
        return "local-model"

    def set_selected_model(self, model_id: str):
        data = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        data["selected_model"] = model_id
        try:
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

class AIOrchestrator:
    def __init__(self, lm_studio_url: str = settings.lm_studio_url):
        self.lm_studio_url = lm_studio_url
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.cache_db = "file_cache.db"
        self.settings_manager = SettingsManager()
        self._init_cache()

    def _init_cache(self):
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_assessments (
                hash TEXT PRIMARY KEY,
                result TEXT
            )
        ''')
        conn.commit()
        conn.close()


    async def get_available_models(self) -> List[str]:
        # lm_studio_url is typically http://localhost:1234/v1/chat/completions
        # we need to get http://localhost:1234/v1/models
        from urllib.parse import urlparse

        parsed_url = urlparse(self.lm_studio_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        models_url = f"{base_url}/v1/models"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(models_url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    models = [model["id"] for model in data.get("data", []) if "id" in model]
                    return models
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return ["local-model"]

    def _get_file_hash(self, filepath: str) -> str:
        if not os.path.exists(filepath):
            return ""
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing {filepath}: {e}")
            return ""

    def _get_from_cache(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("SELECT result FROM file_assessments WHERE hash = ?", (file_hash,))
        row = cursor.fetchone()
        conn.close()
        if row:
            try:
                return json.loads(row[0])
            except:
                pass
        return None

    def _save_to_cache(self, file_hash: str, result: Dict[str, Any]):
        if not file_hash:
            return
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO file_assessments (hash, result) VALUES (?, ?)", (file_hash, json.dumps(result)))
        conn.commit()
        conn.close()

    async def _call_llm(self, messages: List[Dict[str, str]], response_format: Optional[Dict] = None) -> Optional[str]:
        """Helper to call LM Studio REST API with error handling and timeout."""
        selected_model = self.settings_manager.get_selected_model()
        payload = {
            "model": selected_model,
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

        if not content:
            return []

        try:
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]

            result = json.loads(clean_content)
            if isinstance(result, list):
                return result
            else:
                logger.error(f"LLM returned JSON, but it's not a list: {result}")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Tier 1 JSON response: {e}\nContent: {content}")
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

        if not content:
            return {
                "filename": os.path.basename(filepath),
                "delete": False,
                "confidence": 1,
                "reasoning": "LLM failed to respond during deep pass."
            }

        try:
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]

            result = json.loads(clean_content)
            result["filename"] = os.path.basename(filepath)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Tier 2 JSON response: {e}\nContent: {content}")
            return {
                "filename": os.path.basename(filepath),
                "delete": False,
                "confidence": 1,
                "reasoning": "Failed to parse LLM response format."
            }

    async def process_files(self, filepaths: List[str]) -> List[Dict[str, Any]]:
        """Run the complete 2-tier evaluation pipeline."""
        final_results = []
        uncached_filepaths = []
        filepath_hash_map = {}

        for filepath in filepaths:
            file_hash = self._get_file_hash(filepath)
            filepath_hash_map[filepath] = file_hash
            cached_result = self._get_from_cache(file_hash)
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
                    self._save_to_cache(filepath_hash_map[filepath_map[filename]], item)

        if tier_2_tasks:
            tier_2_outputs = await asyncio.gather(*tier_2_tasks)
            for (filepath, original_item), tier_2_result in zip(tier_2_items, tier_2_outputs):
                tier_2_result["reasoning"] = f"Tier 1 reasoning: {original_item.get('reasoning')}. Tier 2 reasoning: {tier_2_result.get('reasoning')}"
                final_results.append(tier_2_result)
                self._save_to_cache(filepath_hash_map[filepath], tier_2_result)

        return final_results
