import os
import re
import platform
import pathlib
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class LibraryEntry:
    """Represents a KiCad library entry from the symbol or footprint table."""
    nickname: str
    path: str

class KiCadEnvParser:
    """
    Parser for KiCad environment variables and global library tables.
    Detects KiCad installation and configuration paths across Windows and POSIX systems.
    """

    def __init__(self) -> None:
        self.env_vars: Dict[str, str] = {}
        self.config_path: Optional[pathlib.Path] = None
        self._initialize()

    def _initialize(self):
        """Initializes the environment variable map and locates the config directory."""
        # 1. Capture existing environment variables
        self.env_vars = dict(os.environ)

        # 2. Detect KiCad version and installation paths
        self._detect_kicad_installations()

        # 3. Locate the global configuration directory
        self.config_path = self._find_global_config_dir()

    def _detect_kicad_installations(self):
        """Heuristically detects KiCad installation paths to populate missing environment variables."""
        versions = ["9.0", "8.0", "7.0", "6.0"]
        
        if platform.system() == "Windows":
            # Common Windows installation roots
            program_files = pathlib.Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
            program_files_x86 = pathlib.Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))
            base_paths = [
                program_files / "KiCad",
                program_files_x86 / "KiCad"
            ]
            
            for v in versions:
                v_major = v.split('.')[0]
                for base in base_paths:
                    install_path = base / v
                    if install_path.exists():
                        # Construct standard KiCad variable defaults
                        share_path = install_path / "share" / "kicad"
                        self._set_default_vars(v_major, share_path)
                        break
        else:
            # POSIX standard paths (Linux/macOS)
            posix_bases = [
                pathlib.Path("/usr/share/kicad"),
                pathlib.Path("/usr/local/share/kicad"),
                pathlib.Path("/opt/kicad"),
                pathlib.Path("~/Library/Application Support/kicad").expanduser()
            ]
            
            for v in versions:
                v_major = v.split('.')[0]
                for base in posix_bases:
                    if base.exists():
                        v_base = base / v
                        target_base = v_base if v_base.exists() else base
                        self._set_default_vars(v_major, target_base)
                        break

    def _set_default_vars(self, version_major: str, share_path: pathlib.Path) -> None:
        """Sets KICADx_... variables if they are not already in the environment."""
        var_map = {
            f"KICAD{version_major}_SYMBOL_DIR": share_path / "symbols",
            f"KICAD{version_major}_FOOTPRINT_DIR": share_path / "footprints",
            f"KICAD{version_major}_TEMPLATE_DIR": share_path / "template",
            f"KICAD{version_major}_3DMODEL_DIR": share_path / "3dmodels",
        }
        for var, path in var_map.items():
            if var not in self.env_vars and path.exists():
                self.env_vars[var] = str(path.resolve())

    def _find_global_config_dir(self) -> Optional[pathlib.Path]:
        """Locates the KiCad global configuration directory containing library tables."""
        search_roots = []
        
        # Check for explicit KiCad config home override
        config_home_str = self.env_vars.get("KICAD_CONFIG_HOME")
        if config_home_str:
            config_home = pathlib.Path(config_home_str)
            if config_home.exists():
                if (config_home / "sym-lib-table").exists():
                    return config_home
                search_roots.append(config_home)

        if platform.system() == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                search_roots.append(pathlib.Path(appdata) / "kicad")
        elif platform.system() == "Darwin":
            search_roots.append(pathlib.Path("~/Library/Preferences/kicad").expanduser())
        else:
            # Linux/Other POSIX
            search_roots.append(pathlib.Path("~/.config/kicad").expanduser())
            
        versions = ["9.0", "8.0", "7.0", "6.0"]
        for root in search_roots:
            if not root.exists():
                continue
            for v in versions:
                config_v = root / v
                if (config_v / "sym-lib-table").exists():
                    return config_v
        return None

    def expand_path_vars(self, path: str) -> str:
        """Expands ${VAR} and $(VAR) placeholders in KiCad paths."""
        def _replacer(match):
            var_name = match.group(1)
            # Check detected env_vars first, then fall back to match itself
            return self.env_vars.get(var_name, match.group(0))
        
        # KiCad uses both curly and round brackets for variables
        expanded = re.sub(r'\$\{([^}]+)\}', _replacer, path)
        expanded = re.sub(r'\$\(([^)]+)\)', _replacer, expanded)
        
        # Clean up path separators and expand user home if present
        return str(pathlib.Path(expanded).expanduser().resolve())

    def parse_lib_table(self, table_name: str) -> List[LibraryEntry]:
        """Parses a KiCad S-expression library table file."""
        if not self.config_path:
            return []
        
        file_path = self.config_path / table_name
        if not file_path.exists():
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return []
            
        entries: List[LibraryEntry] = []
        
        # Split by '(lib' to isolate each library entry block. 
        # This avoids issues with non-greedy regex matches stopping at nested parentheses.
        blocks = content.split('(lib')[1:]
        
        name_pattern = re.compile(r'\(name\s+"([^"]+)"\)')
        uri_pattern = re.compile(r'\(uri\s+"([^"]+)"\)')
        
        for block in blocks:
            name_match = name_pattern.search(block)
            uri_match = uri_pattern.search(block)
            
            if name_match and uri_match:
                nickname = name_match.group(1)
                uri = uri_match.group(1)
                entries.append(LibraryEntry(
                    nickname=nickname,
                    path=self.expand_path_vars(uri)
                ))
                
        return entries

    def get_all_libraries(self) -> Tuple[List[LibraryEntry], List[LibraryEntry]]:
        """
        Returns all global symbol and footprint libraries.
        Returns: (symbols_list, footprints_list)
        """
        symbols = self.parse_lib_table("sym-lib-table")
        footprints = self.parse_lib_table("fp-lib-table")
        return symbols, footprints

def get_kicad_libraries() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Convenience function to get parsed KiCad libraries as lists of dictionaries.
    Required by the task specification.
    """
    parser = KiCadEnvParser()
    syms, fps = parser.get_all_libraries()
    
    return (
        [{"nickname": e.nickname, "path": e.path} for e in syms],
        [{"nickname": e.nickname, "path": e.path} for e in fps]
    )
