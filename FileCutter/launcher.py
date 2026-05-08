import os
import subprocess
import platform
import sys

def check_hardware():
    print("--- Hardware Configuration Wizard ---")
    os_name = platform.system()
    gpu_info = "Unknown"
    vram_info = "Unknown"
    suggested_batch_size = 1

    try:
        if os_name == "Darwin":
            # Check for Apple Silicon
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True)
            if "Apple" in result.stdout:
                gpu_info = "Apple Silicon (e.g., M3 Pro)"
                # Extract memory (unified memory for Apple Silicon)
                mem_result = subprocess.run(["sysctl", "hw.memsize"], capture_output=True, text=True)
                if mem_result.stdout:
                    mem_bytes = int(mem_result.stdout.split(":")[1].strip())
                    mem_gb = mem_bytes / (1024**3)
                    vram_info = f"{mem_gb:.1f} GB Unified Memory"
                    if mem_gb >= 18:  # Typical for M3 Pro
                        suggested_batch_size = 8
                    elif mem_gb >= 16:
                        suggested_batch_size = 4
                    elif mem_gb >= 8:
                        suggested_batch_size = 2
        elif os_name in ("Linux", "Windows"):
            # Check for NVIDIA GPU
            try:
                result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True)
                if result.stdout.strip():
                    parts = result.stdout.strip().split(",")
                    if len(parts) == 2:
                        gpu_info = parts[0].strip()
                        vram_str = parts[1].strip()
                        vram_info = vram_str
                        # Parse VRAM to suggest batch size
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
                gpu_info = "No NVIDIA GPU found (nvidia-smi not available)"
    except Exception as e:
        print(f"Error detecting hardware: {e}")

    print(f"Detected GPU: {gpu_info}")
    print(f"Available VRAM / Memory: {vram_info}")
    print(f"Suggested Batch Size: {suggested_batch_size}")
    print("-------------------------------------\n")
    return suggested_batch_size


def setup_dependencies():
    print("--- Environment Automation ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    # Install Backend Dependencies
    print("Installing backend dependencies...")
    req_file = os.path.join(backend_dir, "requirements.txt")
    if os.path.exists(req_file):
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
            print("Backend dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install backend dependencies: {e}")
            sys.exit(1)
    else:
        print(f"Warning: requirements.txt not found at {req_file}")

    # Install Frontend Dependencies
    print("Installing frontend dependencies...")
    if os.path.exists(os.path.join(frontend_dir, "package.json")):
        npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
        try:
            subprocess.run([npm_cmd, "install"], cwd=frontend_dir, check=True)
            print("Frontend dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install frontend dependencies: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("Warning: npm not found. Please install Node.js to run the frontend.")
            sys.exit(1)
    else:
        print(f"Warning: package.json not found in {frontend_dir}")
    print("------------------------------\n")

def launch_services():
    print("--- Launching Services ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")

    # Launch Backend
    print("Starting FastAPI backend...")
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = backend_dir
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload"],
        cwd=backend_dir,
        env=backend_env
    )

    # Launch Frontend
    print("Starting React frontend...")
    npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
    frontend_process = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir
    )

    try:
        # Wait for both processes to complete (or for the user to interrupt)
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Services stopped successfully.")

def main():
    setup_dependencies()
    check_hardware()
    launch_services()

if __name__ == "__main__":
    main()
