# utils/identity.py
"""
Identity normalization and canonicalization utilities for GodEye.

Purpose:
---------
To ensure consistent representation of identifiers (domains, IPs, usernames, etc.)
across multiple data sources, so correlation and deduplication are accurate.

Functions:
----------
- generate_session_id() : returns UUIDv4 for each run
- hash_identifier(value): returns SHA-256 hash
- normalize_identity(value): generic normalization (lowercase/trim)
- canonical_domain(domain): normalize domain names (lowercase, no www.)
- canonical_ip(ip): validate and standardize IPv4/IPv6
"""

import uuid
import hashlib
import ipaddress
from urllib.parse import urlparse

# ---------------------------------------------------------------------
# Core identity helpers
# ---------------------------------------------------------------------

def generate_session_id() -> str:
    """Generate a unique session ID for each GodEye execution."""
    return str(uuid.uuid4())

def hash_identifier(value: str) -> str:
    """Create a SHA-256 hash to anonymize identifiers."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def normalize_identity(value: str) -> str:
    """Normalize generic identifiers (trim, lowercase)."""
    if not value:
        return ""
    return str(value).strip().lower()

# ---------------------------------------------------------------------
# Domain canonicalization
# ---------------------------------------------------------------------

def canonical_domain(domain: str) -> str:
    """
    Normalize domain name for correlation.
    - Strips protocols (http/https)
    - Removes 'www.' prefix
    - Converts to lowercase
    - Extracts netloc from URLs
    """
    if not domain:
        return ""

    domain = domain.strip().lower()

    # If it's a full URL, extract hostname
    if "://" in domain:
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path

    # Remove leading 'www.'
    if domain.startswith("www."):
        domain = domain[4:]

    # Remove trailing slashes
    domain = domain.rstrip("/")

    return domain

# ---------------------------------------------------------------------
# IP canonicalization
# ---------------------------------------------------------------------

def canonical_ip(ip: str) -> str:
    """
    Validate and return normalized IP address (v4 or v6).
    Raises ValueError for invalid IPs.
    """
    if not ip:
        return ""

    try:
        normalized = ipaddress.ip_address(ip)
        return normalized.exploded  # standardized string format
    except ValueError:
        return ""  # Return empty string for invalid IPs

# ---------------------------------------------------------------------
# __all__ (explicit exports)
# ---------------------------------------------------------------------

__all__ = [
    "generate_session_id",
    "hash_identifier",
    "normalize_identity",
    "canonical_domain",
    "canonical_ip",
]
