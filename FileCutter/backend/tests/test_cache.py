import sqlite3
import concurrent.futures
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.cache import SQLiteCache


def make_cache(tmp_path) -> SQLiteCache:
    return SQLiteCache(db_path=str(tmp_path / "test_cache.db"))


# --- Basic round-trip ---

def test_set_then_get_returns_same_dict(tmp_path):
    cache = make_cache(tmp_path)
    data = {"risk": "high", "score": 0.95, "tags": ["pii"]}
    cache.set("abc123", data)
    assert cache.get("abc123") == data


def test_missing_hash_returns_none(tmp_path):
    cache = make_cache(tmp_path)
    assert cache.get("does_not_exist") is None


# --- Edge cases ---

def test_empty_hash_get_returns_none(tmp_path):
    cache = make_cache(tmp_path)
    assert cache.get("") is None


def test_empty_hash_set_is_noop(tmp_path):
    cache = make_cache(tmp_path)
    cache.set("", {"should": "not be stored"})
    conn = sqlite3.connect(str(tmp_path / "test_cache.db"))
    count = conn.execute("SELECT COUNT(*) FROM file_assessments").fetchone()[0]
    conn.close()
    assert count == 0


def test_corrupt_json_returns_none(tmp_path):
    db = str(tmp_path / "test_cache.db")
    cache = SQLiteCache(db_path=db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT OR REPLACE INTO file_assessments (hash, result) VALUES (?, ?)",
        ("badhash", "{{not valid json{{"),
    )
    conn.commit()
    conn.close()
    assert cache.get("badhash") is None


# --- Concurrency ---

def test_concurrent_writes_both_succeed(tmp_path):
    cache = make_cache(tmp_path)
    hashes = [f"hash{i}" for i in range(20)]
    results = [{"index": i} for i in range(20)]

    def write(args):
        h, r = args
        cache.set(h, r)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, zip(hashes, results)))

    for h, r in zip(hashes, results):
        assert cache.get(h) == r


# --- WAL mode ---

def test_wal_mode_enabled(tmp_path):
    db = str(tmp_path / "wal_test.db")
    SQLiteCache(db_path=db)
    conn = sqlite3.connect(db)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode == "wal"


# --- Default path ---

def test_default_path_under_home(tmp_path, monkeypatch):
    fake_home = tmp_path / "fakehome"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    # Patch settings so cache_db_path looks like the bare default
    with patch("app.core.cache.settings") as mock_settings:
        mock_settings.cache_db_path = "file_cache.db"
        cache = SQLiteCache()

    assert Path(cache.db_path).parent == fake_home / ".filecutter"
