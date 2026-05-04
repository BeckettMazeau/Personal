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
