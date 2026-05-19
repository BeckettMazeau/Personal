import platform
import subprocess
from typing import List
from app.models.schemas import FileObject

def get_optimal_batch_size() -> int:
    os_name = platform.system()
    suggested_batch_size = 1

    try:
        if os_name == "Darwin":
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True)
            if "Apple" in result.stdout:
                mem_result = subprocess.run(["sysctl", "hw.memsize"], capture_output=True, text=True)
                if mem_result.stdout:
                    mem_bytes = int(mem_result.stdout.split(":")[1].strip())
                    mem_gb = mem_bytes / (1024**3)
                    if mem_gb >= 18:
                        suggested_batch_size = 8
                    elif mem_gb >= 16:
                        suggested_batch_size = 4
                    elif mem_gb >= 8:
                        suggested_batch_size = 2
        elif os_name in ("Linux", "Windows"):
            try:
                result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
                if result.stdout.strip():
                    parts = result.stdout.strip().split(",")
                    if len(parts) == 2:
                        gpu_info = parts[0].strip()
                        vram_str = parts[1].strip()
                        vram_mb = int(vram_str.replace("MiB", "").strip())
                        if "RTX 5070" in gpu_info:
                            suggested_batch_size = 8
                        elif vram_mb >= 12000:
                            suggested_batch_size = 8
                        elif vram_mb >= 8000:
                            suggested_batch_size = 4
                        elif vram_mb >= 4000:
                            suggested_batch_size = 2
            except FileNotFoundError:
                pass
    except Exception:
        pass

    return suggested_batch_size

def batch_files(files: List[FileObject], batch_size: int = 20) -> List[List[FileObject]]:
    """Chunks a list of files into batches of a specified size."""
    return [files[i:i + batch_size] for i in range(0, len(files), batch_size)]

from pathlib import Path
def get_downloads_directory() -> Path:
    return Path.home() / "Downloads"

import json
import re
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:json|JSON)?\s*\n?", re.IGNORECASE)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    m = _FENCE_RE.match(stripped)
    if m:
        stripped = stripped[m.end():]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
    return stripped.strip()


def _extract_balanced(text: str) -> Optional[str]:
    """Return the largest brace- or bracket-balanced substring, or None."""
    best: Optional[str] = None
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        while start != -1:
            depth = 0
            in_str = False
            esc = False
            for i in range(start, len(text)):
                ch = text[i]
                if in_str:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        in_str = False
                    continue
                if ch == '"':
                    in_str = True
                elif ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i + 1]
                        if best is None or len(candidate) > len(best):
                            best = candidate
                        break
            start = text.find(open_ch, start + 1)
    return best


def clean_and_parse_json(content: Optional[str]) -> Optional[Any]:
    """Robustly parse JSON from an LLM response.

    Tries direct parse, then strips ```json / ``` fences, then extracts
    the largest balanced brace/bracket substring. Returns None on failure.
    """
    if not content:
        return None

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    unfenced = _strip_code_fence(content)
    if unfenced != content.strip():
        try:
            return json.loads(unfenced)
        except json.JSONDecodeError:
            pass

    candidate = _extract_balanced(unfenced) or _extract_balanced(content)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    snippet = content[:200].replace("\n", " ")
    logger.warning(f"Failed to parse JSON response. Snippet: {snippet!r}")
    return None
