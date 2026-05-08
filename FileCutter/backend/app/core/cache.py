import sqlite3
import json
from typing import Dict, Any, Optional
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class SQLiteCache:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.cache_db_path
        self._init_cache()

    def _init_cache(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_assessments (
                hash TEXT PRIMARY KEY,
                result TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get(self, file_hash: str) -> Optional[Dict[str, Any]]:
        if not file_hash:
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT result FROM file_assessments WHERE hash = ?", (file_hash,))
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                return json.loads(row[0])
            except Exception as e:
                logger.error(f"Failed to load cached result for {file_hash}: {e}")
                pass
        return None

    def set(self, file_hash: str, result: Dict[str, Any]):
        if not file_hash:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO file_assessments (hash, result) VALUES (?, ?)", (file_hash, json.dumps(result)))
        conn.commit()
        conn.close()
