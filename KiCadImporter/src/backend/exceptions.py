"""
Centralized exception definitions for the KiCad Importer backend.
"""

class KiCadImportError(Exception):
    """Base class for all custom exceptions in KiCad Importer."""
    pass

class FileCollisionError(KiCadImportError):
    """Exception raised when a file already exists in the target directory."""
    pass

class KiCadCLINotFoundError(KiCadImportError):
    """Exception raised when the kicad-cli executable cannot be located."""
    pass

class ArchiveExtractionError(KiCadImportError):
    """Exception raised when an archive fails to extract properly."""
    pass

class InvalidKiCadLibraryError(KiCadImportError):
    """Exception raised when a KiCad library file is invalid or unreadable."""
    pass

class ConfigurationError(KiCadImportError):
    """Exception raised when there is an issue reading or writing configuration."""
    pass
