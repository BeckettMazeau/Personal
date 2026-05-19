from pathlib import Path


def get_data_dir() -> Path:
    d = Path.home() / ".filecutter"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_cache_db_path() -> Path:
    return get_data_dir() / "cache.db"
