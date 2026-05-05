import subprocess
import pathlib
import os
from typing import List, Optional, Union
from dataclasses import dataclass
from src.backend.exceptions import KiCadCLINotFoundError


@dataclass
class OperationResult:
    """
    Standardized result object for all backend and processing operations.
    As defined in ARCHITECTURE.md.
    """
    success: bool           # True if the operation completed without errors
    output_files: List[str] # List of absolute paths to the generated files
    error_message: Optional[str] # Description of the error if success is False
    logs: str               # Raw stdout/stderr from the CLI process


class KiCadCLIWrapper:
    """
    Wrapper for KiCad-CLI to perform exports and system checks.
    """

    def __init__(self, cli_path: str = "kicad-cli"):
        """
        Initialize the wrapper.
        
        Args:
            cli_path: The command or path to the KiCad-CLI executable.
        """
        self.cli_path = cli_path

    def check_kicad_cli(self) -> bool:
        """
        Verifies that kicad-cli is in the system PATH.
        
        Returns:
            True if found.
            
        Raises:
            KiCadCLINotFoundError: If the executable is missing.
        """
        try:
            # We use --version as a lightweight check
            subprocess.run(
                [self.cli_path, "--version"], 
                capture_output=True, 
                check=True,
                text=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            error_msg = (
                f"KiCad-CLI executable '{self.cli_path}' not found in system PATH.\n"
                "To resolve this issue:\n"
                "1. Ensure KiCad 8.0 or later is installed on your system.\n"
                "2. Add the KiCad bin directory (e.g., 'C:\\Program Files\\KiCad\\8.0\\bin' on Windows or '/usr/bin' on Linux) to your system's PATH environment variable.\n"
                "3. Alternatively, specify the full path to the executable in the application settings."
            )
            raise KiCadCLINotFoundError(error_msg)

    def _execute(self, args: List[str], output_paths: List[pathlib.Path]) -> OperationResult:
        """
        Internal helper to execute a KiCad-CLI command.
        
        Args:
            args: List of command line arguments (excluding the executable).
            output_paths: Expected output files to verify on success.
            
        Returns:
            An OperationResult instance.
        """
        try:
            result = subprocess.run(
                [self.cli_path] + args,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            
            # Verify that output files were actually created
            for p in output_paths:
                if not p.exists():
                    return OperationResult(
                        success=False,
                        output_files=[],
                        error_message=f"Export command reported success but output file was not found: {p}",
                        logs=f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                    )

            return OperationResult(
                success=True,
                output_files=[str(p.resolve()) for p in output_paths],
                error_message=None,
                logs=f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return OperationResult(
                success=False,
                output_files=[],
                error_message="KiCad-CLI operation timed out after 10 seconds.",
                logs=f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False,
                output_files=[],
                error_message=f"KiCad-CLI export failed (Exit Code {e.returncode}).",
                logs=f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                output_files=[],
                error_message=f"Unexpected error during CLI execution: {str(e)}",
                logs=""
            )

    def generate_symbol_preview(self, input_path: Union[str, pathlib.Path], output_svg_path: Union[str, pathlib.Path]) -> OperationResult:
        """
        Exports a KiCad symbol file to SVG.
        
        Args:
            input_path: Path to the .kicad_sym file.
            output_svg_path: Path where the SVG should be saved.
            
        Returns:
            OperationResult containing status and logs.
        """
        input_p = pathlib.Path(input_path).resolve()
        output_p = pathlib.Path(output_svg_path).resolve()
        
        # Ensure output directory exists (temp workspace is managed by Phase 1, but safety first)
        output_p.parent.mkdir(parents=True, exist_ok=True)
        
        args = ["sym", "export", "svg", "--output", str(output_p), str(input_p)]
        return self._execute(args, [output_p])

    def generate_footprint_preview(self, input_path: Union[str, pathlib.Path], output_svg_path: Union[str, pathlib.Path]) -> OperationResult:
        """
        Exports a KiCad footprint file to SVG.
        
        Args:
            input_path: Path to the .kicad_mod file.
            output_svg_path: Path where the SVG should be saved.
            
        Returns:
            OperationResult containing status and logs.
        """
        input_p = pathlib.Path(input_path).resolve()
        output_p = pathlib.Path(output_svg_path).resolve()
        
        # Ensure output directory exists
        output_p.parent.mkdir(parents=True, exist_ok=True)
        
        args = ["fp", "export", "svg", "--output", str(output_p), str(input_p)]
        return self._execute(args, [output_p])
