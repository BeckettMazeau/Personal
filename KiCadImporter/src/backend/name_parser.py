import re
import os
from typing import List, Optional

def _clean_single_name(filename: str) -> str:
    """Strips known extensions and common vendor prefixes/suffixes."""
    name = os.path.basename(filename)
    
    # Remove extensions
    extensions = ['.kicad_sym', '.kicad_mod', '.pretty', '.zip']
    for ext in extensions:
        if name.lower().endswith(ext.lower()):
            name = name[:-len(ext)]
            break
            
    # Remove common vendor prefixes (case-insensitive)
    prefixes = ['ul_', 'mouser_', 'digikey_', 'snapeda_', 'samacsys_', 'lib_', 'pcblib_']
    for prefix in prefixes:
        if name.lower().startswith(prefix.lower()):
            name = name[len(prefix):]
            break # Only remove one prefix
            
    # Remove common suffixes/versioning
    name = re.sub(r'(_v\d+|_latest|_v1|(_EXP)?)$', '', name, flags=re.IGNORECASE)
    
    return name

def _is_timestamp(name: str) -> bool:
    """Checks if a name looks like a timestamp (e.g. 2026-05-05_07-59-52)."""
    # Pattern for YYYY-MM-DD or HH-MM-SS variants
    # Also catches things like 450404015514 from the user's screenshot
    if re.match(r'^\d{4}[-_]\d{2}[-_]\d{2}([-_]\d{2}[-_]\d{2}[-_]\d{2})?$', name):
        return True
    if re.match(r'^\d{10,}$', name): # Long numeric strings (often unix timestamps or random IDs)
        return True
    return False

def _score_name(name: str) -> int:
    """Scores a name based on how likely it is to be a real part number."""
    if not name or len(name) < 2:
        return -100
    
    if _is_timestamp(name):
        return -50
        
    score = 0
    
    # Parts usually contain both letters and numbers (e.g. ESP32-S3)
    has_alpha = bool(re.search(r'[a-zA-Z]', name))
    has_digit = bool(re.search(r'\d', name))
    
    if has_alpha and has_digit:
        score += 30
    elif has_alpha:
        score += 10
        
    # Bonus for common part number patterns (dashes, capital letters)
    if '-' in name or '_' in name:
        score += 5
    if any(c.isupper() for c in name):
        score += 5
        
    # Length bonus (sweet spot 5-20 chars)
    if 5 <= len(name) <= 25:
        score += 10
    
    # Penalize purely numeric
    if name.isdigit():
        score -= 20
        
    return score

def _finalize_name(name: str) -> str:
    """Final normalization: alphanumeric and hyphens only."""
    # Replace non-alphanumeric (except hyphens) with hyphens
    name = re.sub(r'[^a-zA-Z0-9]', '-', name)
    # Collapse multiple hyphens
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

def suggest_part_name(file_list: List[str], zip_path: Optional[str] = None) -> str:
    """
    Suggests a part name by evaluating filenames and the archive name.
    
    Uses a scoring system to prefer descriptive part numbers over 
    vendor-generated timestamps or generic prefixes.
    """
    candidates = []
    
    # 1. Add zip name as a candidate (highest weight usually)
    if zip_path:
        zip_clean = _clean_single_name(zip_path)
        candidates.append((zip_clean, _score_name(zip_clean) + 5)) # Slight boost for zip name
        
    # 2. Add all files inside
    for f in file_list:
        clean = _clean_single_name(f)
        score = _score_name(clean)
        
        # Boost footprint files as they are usually named after the specific part
        if f.lower().endswith('.kicad_mod'):
            score += 10
            
        candidates.append((clean, score))
        
    if not candidates:
        return "Unknown_Part"
        
    # 3. Pick the highest scoring candidate
    best_name, best_score = max(candidates, key=lambda x: x[1])
    
    # 4. Fallback if everything is junk
    if best_score < -20:
        # If we have a zip path, use its cleaned name even if low score
        if zip_path:
            return _finalize_name(_clean_single_name(zip_path))
        return "Unknown_Part"

    return _finalize_name(best_name)

