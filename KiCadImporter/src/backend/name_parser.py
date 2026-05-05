import re
import os
from typing import List

def _clean_single_name(filename: str) -> str:
    """Strips known extensions and common vendor prefixes/suffixes."""
    name = filename
    extensions = ['.kicad_sym', '.kicad_mod', '.pretty']
    for ext in extensions:
        if name.lower().endswith(ext.lower()):
            name = name[:-len(ext)]
            break
            
    # Remove vendor prefixes/suffixes (case-insensitive)
    name = re.sub(r'^(Mouser|DigiKey)[_-]', '', name, flags=re.IGNORECASE)
    name = re.sub(r'(_v\d+|_latest|_v1)$', '', name, flags=re.IGNORECASE)
    
    return name

def _normalize_for_comp(name: str) -> str:
    """Normalizes string for comparison by replacing underscores/hyphens with spaces."""
    return re.sub(r'[_ -]+', ' ', name).strip()

def _finalize_name(name: str) -> str:
    """Final normalization: alphanumeric and hyphens only."""
    # Replace non-alphanumeric (except hyphens) with hyphens
    name = re.sub(r'[^a-zA-Z0-9]', '-', name)
    # Collapse multiple hyphens
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

def _get_lcs(s1: str, s2: str) -> str:
    """Finds the longest common substring between two strings."""
    m = [[0] * (1 + len(s2)) for _ in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]

def suggest_part_name(file_list: List[str]) -> str:
    """
    Suggests a part name from a list of filenames by cleaning them and finding
    the longest common denominator.
    
    Args:
        file_list: A list of filenames (strings).
        
    Returns:
        str: A cleaned, normalized part name string.
    """
    if not file_list:
        return "Unknown_Part"

    # 1. Get basenames and clean them
    cleaned_names = [_clean_single_name(os.path.basename(f)) for f in file_list]
    
    # 2. Normalize for comparison
    comp_names = [_normalize_for_comp(n) for n in cleaned_names]

    # 4. Longest Common Substring Search
    if len(comp_names) == 1:
        result = comp_names[0]
    else:
        # Find LCS across all filenames
        result = comp_names[0]
        for i in range(1, len(comp_names)):
            result = _get_lcs(result, comp_names[i])
            if not result.strip():
                break
    
    result = result.strip()
    
    # 5. Edge Case Handling: If no common string is found, return name of largest file
    if not result:
        max_size = -1
        largest_file_idx = 0
        
        for i, f in enumerate(file_list):
            try:
                # If path is relative or non-existent, this might fail or return 0
                if os.path.exists(f):
                    size = os.path.getsize(f)
                    if size > max_size:
                        max_size = size
                        largest_file_idx = i
            except (OSError, AttributeError):
                pass
        
        # If we couldn't get sizes, or all were -1, use the first one as fallback
        return _finalize_name(cleaned_names[largest_file_idx])

    return _finalize_name(result)
