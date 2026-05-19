import sqlite3
import json
import threading
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.data_dir import get_cache_db_path

logger = logging.getLogger(__name__)

_DEFAULT_RELATIVE = "file_cache.db"


class SQLiteCache:
    def __init__(self, db_path: str | None = None):
        if db_path is not None:
            self.db_path = str(db_path)
        else:
            configured = getattr(settings, "cache_db_path", None)
            if configured and configured != _DEFAULT_RELATIVE:
                self.db_path = configured
            else:
                self.db_path = str(get_cache_db_path())
        self._lock = threading.Lock()
        self._init_cache()

    def _init_cache(self):
        with sqlite3.connect(self.db_path, timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_assessments (
                    hash TEXT PRIMARY KEY,
                    result TEXT
                )
                """
            )

    def get(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                row = conn.execute(
                    "SELECT result FROM file_assessments WHERE hash = ?",
                    (file_hash,),
                ).fetchone()
        except sqlite3.Error as e:
            logger.error(f"Cache read failed for {file_hash}: {e}")
            return None
        if not row:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt cache entry for {file_hash}: {e}")
            return None

    def set(self, file_hash: str, result: Dict[str, Any]) -> None:
        if not file_hash:
            return
        payload = json.dumps(result)
        with self._lock:
            try:
                with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO file_assessments (hash, result) VALUES (?, ?)",
                        (file_hash, payload),
                    )
            except sqlite3.Error as e:
                logger.error(f"Cache write failed for {file_hash}: {e}")
