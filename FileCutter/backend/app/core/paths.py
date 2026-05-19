"""Path containment helpers.

Used to ensure that any path passed to a destructive operation lives inside
an allowed root, even after resolving symlinks.
"""

from __future__ import annotations

from pathlib import Path


def is_within(path: Path, root: Path) -> bool:
    """Return True iff `path`, fully resolved, lives inside `root`."""
    try:
        resolved = path.resolve(strict=False)
        resolved_root = root.resolve(strict=False)
    except (OSError, RuntimeError):
        return False
    return resolved == resolved_root or resolved.is_relative_to(resolved_root)


def safe_resolve(path: str, allowed_root: Path) -> Path:
    """Resolve `path` and verify it stays inside `allowed_root`.

    Raises ValueError if the resolved path (after following symlinks) escapes
    the allowed root, or if the path is malformed.
    """
    if not isinstance(path, str) or not path:
        raise ValueError("Path must be a non-empty string.")
    candidate = Path(path)
    try:
        resolved = candidate.resolve(strict=False)
        resolved_root = allowed_root.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Could not resolve path: {path}") from e
    if not (resolved == resolved_root or resolved.is_relative_to(resolved_root)):
        raise ValueError(
            f"Path {path!r} resolves outside allowed root {str(allowed_root)!r}."
        )
    return resolved
