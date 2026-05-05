import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from src.backend.exceptions import ConfigurationError

# Configure logger
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages application configuration state with JSON persistence.
    Stored in the user's home directory under .kicad_import_tool/config.json.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initializes the Configuration Manager.
        
        Args:
            config_path: Optional specific path for the config file. 
                         Defaults to ~/.kicad_import_tool/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".kicad_import_tool" / "config.json"
            
        self.config_dir = self.config_path.parent
        
        # Default application state schema
        self._defaults: Dict[str, Any] = {
            "last_used_symbol_lib_path": "",
            "last_used_footprint_lib_path": "",
            "last_duplication_directory": "",
            "window_geometry": {},
        }
        
        self._config: Dict[str, Any] = self._defaults.copy()
        self.load()

    def load(self) -> None:
        """
        Reads the configuration file from disk.
        Handles missing files, permission errors, and malformed JSON.
        """
        if not self.config_path.exists():
            logger.info("Configuration file not found. Starting with clean defaults.")
            self._config = self._defaults.copy()
            # Try to save defaults immediately to ensure path is writable
            self.save()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                if not isinstance(loaded_data, dict):
                    raise ConfigurationError("Config file root must be a JSON object.")
                
                # Update config with loaded data, preserving defaults for missing keys
                self._config = self._defaults.copy()
                self._config.update(loaded_data)
                
        except (json.JSONDecodeError, ConfigurationError, ValueError, PermissionError) as e:
            logger.error(f"Error loading configuration from {self.config_path}: {e}")
            self._handle_corrupted_config()
        except Exception as e:
            logger.error(f"Unexpected error loading config: {e}")
            self._config = self._defaults.copy()

    def _handle_corrupted_config(self) -> None:
        """
        Backs up a corrupted config file and resets state to defaults.
        """
        try:
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix(".json.bak")
                shutil.copy2(self.config_path, backup_path)
                logger.warning(f"Corrupted config backed up to {backup_path}")
            
            self._config = self._defaults.copy()
            self.save()
        except Exception as e:
            logger.error(f"Failed to handle corrupted config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value.
        
        Args:
            key: The configuration key to lookup.
            default: Value to return if the key is not found.
            
        Returns:
            The value associated with the key, or the default value.
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Sets a configuration value in memory.
        Note: Use save() to persist changes to disk.
        
        Args:
            key: The configuration key to set.
            value: The value to store.
        """
        self._config[key] = value

    def save(self) -> bool:
        """
        Persists the current configuration state to disk.
        
        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            # Ensure the configuration directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Write to a temporary file first then rename to ensure atomicity
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            
            # Atomic swap (on most OSs)
            temp_path.replace(self.config_path)
            logger.debug(f"Configuration successfully saved to {self.config_path}")
            return True
            
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to save configuration to {self.config_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during save: {e}")
            return False

# Module-level singleton instance for shared application state
# Initialize with default path
instance = ConfigManager()
