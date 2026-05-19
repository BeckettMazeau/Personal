"""In-memory, single-use nonce store for delete authorization.

The frontend requests a nonce bound to the exact set of paths it intends to
delete, then submits that nonce alongside the delete request. The nonce is
single-use and expires after a short TTL. This is the authorization
mechanism for delete operations on the localhost API; the typed-DELETE
confirmation in the UI is UX-only.
"""

from __future__ import annotations

import secrets
import threading
import time
from typing import Iterable

NONCE_TTL_SECONDS = 60


def _normalize(paths: Iterable[str]) -> frozenset[str]:
    return frozenset(paths)


class NonceStore:
    def __init__(self, ttl_seconds: int = NONCE_TTL_SECONDS, clock=time.monotonic):
        self._ttl = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[frozenset[str], float]] = {}

    def issue(self, paths: Iterable[str]) -> str:
        nonce = secrets.token_urlsafe(32)
        expires_at = self._clock() + self._ttl
        with self._lock:
            self._purge_expired_locked()
            self._entries[nonce] = (_normalize(paths), expires_at)
        return nonce

    def consume(self, nonce: str, paths: Iterable[str]) -> bool:
        if not isinstance(nonce, str) or not nonce:
            return False
        target = _normalize(paths)
        with self._lock:
            entry = self._entries.pop(nonce, None)
            if entry is None:
                return False
            stored_paths, expires_at = entry
            if self._clock() >= expires_at:
                return False
            return stored_paths == target

    def _purge_expired_locked(self) -> None:
        now = self._clock()
        expired = [n for n, (_, exp) in self._entries.items() if now >= exp]
        for n in expired:
            self._entries.pop(n, None)


nonce_store = NonceStore()
