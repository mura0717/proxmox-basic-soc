"""MAC address utilities for consistent handling across sources"""

import re
from typing import Optional, Dict, Set, Union, Iterable

def normalize_mac(mac: str) -> Optional[str]:
    """
    Normalize MAC address to consistent format (uppercase, colon-separated)
    Handles various input formats: AA:BB:CC:DD:EE:FF, aa-bb-cc-dd-ee-ff, aabbccddeeff
    """
    if not mac:
        return None
    
    # Remove common separators and whitespace
    clean = mac.upper().replace(':', '').replace('-', '').replace('.', '').strip()
    
    # Validate length
    if len(clean) != 12:
        return None  # NONE or should Return original if invalid?
    
    # Format as XX:XX:XX:XX:XX:XX
    return ':'.join(clean[i:i+2] for i in range(0, 12, 2)).upper()

def combine_macs(mac_list: list) -> str:
    """
    Combine multiple MAC addresses into newline-separated string
    Removes duplicates and normalizes format
    """
    if not mac_list:
        return None
    
    # Normalize and deduplicate
    normalized = []
    seen = set()
    
    for mac in mac_list:
        if not mac:
            continue
        norm_mac = normalize_mac(mac)
        if norm_mac and norm_mac not in seen:
            normalized.append(norm_mac)
            seen.add(norm_mac)
    
    return '\n'.join(normalized) if normalized else None

def macs_from_string(value: Optional[str]) -> Set[str]:
    """
    Parse a string that may contain one or more MACs separated by newlines/whitespace/commas/semicolons.
    Returns a set of normalized MACs.
    """
    result: Set[str] = set()
    if not value:
        return result
    for token in re.split(r'[\s,;]+', value.strip()):
        nm = normalize_mac(token)
        if nm:
            result.add(nm)
    return result

def macs_from_any(value: Optional[Union[str, Iterable[str]]]) -> Set[str]:
    """
    Parse a string or iterable of strings into a set of normalized MACs.
    """
    if value is None:
        return set()
    if isinstance(value, str):
        return macs_from_string(value)
    result: Set[str] = set()
    for v in value:
        if v:
            result |= macs_from_string(str(v))
    return result

def macs_from_keys(data: Dict, keys: Iterable[str]) -> Set[str]:
    """
    Collect normalized MACs from provided keys in a dict.
    Values may be strings or iterables of strings.
    """
    result: Set[str] = set()
    for k in keys:
        result |= macs_from_any(data.get(k))
    return result

def intersect_mac_sets(a: Set[str], b: Set[str]) -> Optional[str]:
    """
    Return one matching MAC from the intersection, or None if no match.
    """
    inter = a & b
    return next(iter(inter)) if inter else None