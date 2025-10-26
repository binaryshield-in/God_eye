#!/usr/bin/env python3
# MIT License
# Copyright (c) 2025 GodEye OSINT Project
"""
GodEye Data Normalizer v1.2

Enhancements:
- JSON Schema validation
- Correlation hash for cross-source fusion
- Temporal decay confidence weighting
- Structured audit logging

This normalizer transforms heterogeneous collector outputs into a unified schema
with deterministic identifiers, provenance evidence, and normalized confidence metrics.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from utils.time import to_iso
from utils.text import clean_text
from utils.identity import canonical_domain, canonical_ip

try:
    from jsonschema import validate, ValidationError
except ImportError:
    validate = None
    ValidationError = Exception

logger = logging.getLogger("core.normalizer")

SRC_TRUST = {
    'shodan': 0.95, 'virustotal': 0.90, 'abuseipdb': 0.88,
    'crtsh': 0.85, 'whois': 0.83, 'dns': 0.82, 'github': 0.80,
    'ipinfo': 0.78, 'haveibeenpwned': 0.85, 'urlhaus': 0.82,
    'otx': 0.80, 'wayback': 0.75, 'hunter': 0.73, 'duckduckgo': 0.70,
    'twitter': 0.65, 'clearbit': 0.68, 'phishtank': 0.82,
    'commoncrawl': 0.72, 'generic': 0.50
}


class DataNormalizer:
    """Normalizes raw OSINT collector data into canonical schema with extended validation and fusion."""

    def __init__(self, schema_path: str = None):
        self.schema_path = schema_path
        self.schema = None

        if schema_path:
            try:
                with open(schema_path, "r") as f:
                    self.schema = json.load(f)
                logger.info(f"Schema loaded: {schema_path}")
            except Exception as e:
                logger.warning(f"Schema load failed: {e}")

    # ────────────────────────────────────────────────────────────────────────────────
    # Core Utility Functions
    # ────────────────────────────────────────────────────────────────────────────────

    def _generate_id(self, source: str, raw_id: str, indicator: str) -> str:
        composite = f"{source}|{raw_id}|{indicator}"
        return hashlib.sha256(composite.encode()).hexdigest()[:16]

    def _generate_correlation_hash(self, indicator: str) -> str:
        """Cross-source correlation hash used for entity fusion."""
        return hashlib.sha1(indicator.encode('utf-8')).hexdigest()[:12]

    def _apply_temporal_decay(self, timestamp: Optional[str]) -> float:
        """Reduces confidence for stale data (>365 days old)."""
        if not timestamp:
            return 1.0
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            delta_days = (datetime.utcnow() - dt).days
            return max(0.5, 1.0 - (delta_days / 365))
        except Exception:
            return 1.0

    def _calculate_confidence(self, source: str, raw_score: Optional[float] = None, timestamp: Optional[str] = None) -> float:
        base = SRC_TRUST.get(source.lower(), SRC_TRUST['generic'])
        if raw_score is not None:
            raw_score = max(0.0, min(1.0, float(raw_score)))
            confidence = (base * 0.7) + (raw_score * 0.3)
        else:
            confidence = base
        decay = self._apply_temporal_decay(timestamp)
        return round(confidence * decay, 3)

    def _validate_schema(self, record: dict):
        if not (self.schema and validate):
            return
        try:
            validate(instance=record, schema=self.schema)
        except ValidationError as e:
            logger.warning(f"Schema validation failed: {e.message}")

    # ────────────────────────────────────────────────────────────────────────────────
    # Dynamic Normalization Dispatcher
    # ────────────────────────────────────────────────────────────────────────────────

    def normalize(self, data, *args, **kwargs):
        """
        Normalize raw input data into a unified schema.
        Accepts flexible arguments for future extensions.
        """
        try:
            # If the top-level caller passed the full collection wrapper (from main/CollectorManager),
            # it will look like: {'input':..., 'type':..., 'results': [...] }. In that case normalize each collector result.
            if isinstance(data, dict) and 'results' in data and isinstance(data.get('results'), list):
                data = data.get('results')

            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = [{"source": "GodEyeCollector", "raw": data}]
            elif isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                data = [{"source": "GodEyeCollector", "raw": str(data)}]

            normalized_data = []

            for item in data:
                item_copy = item.copy()

                # Prefer an explicit 'collector' field, then 'source'
                collector_name = item_copy.get('collector') or item_copy.get('source') or 'generic'
                source = str(collector_name).lower()

                # Try explicit matches first
                if 'twitter' in source:
                    normalized = self._normalize_twitter(item_copy)
                elif 'shodan' in source:
                    normalized = self._normalize_shodan(item_copy)
                elif 'urlscan' in source or 'url_scan' in source:
                    normalized = self._normalize_urlscan(item_copy)
                elif 'abuseipdb' in source:
                    # abuseipdb normalizer expects a raw dict
                    normalized = self._normalize_abuseipdb(item_copy.get('raw', item_copy))
                elif 'ipinfo' in source or 'ip' in (item_copy.get('raw', {}) or {}) or 'ip' in (item_copy.get('data', {}) or {}):
                    # If raw contains an IP, route to ipinfo normalizer
                    normalized = self._normalize_ipinfo(item_copy.get('raw', item_copy))
                elif 'crt' in source or 'crt.sh' in source or 'crtsh' in source:
                    normalized = self._normalize_crtsh(item_copy)
                elif 'dns' in source or 'dns lookup' in source or 'dns lookup' in source.lower():
                    normalized = self._normalize_dns(item_copy)
                else:
                    # Try to heuristically detect content type (ip/domain/email)
                    raw = item_copy.get('raw') or item_copy.get('data') or {}
                    r = raw if isinstance(raw, dict) else {'value': str(raw)}
                    if r.get('ip') or r.get('ip_str'):
                        normalized = self._normalize_ipinfo(r)
                    elif r.get('domain') or r.get('hostname') or (r.get('value') and '.' in str(r.get('value'))):
                        # fallback to generic but attempt to canonicalize domain first
                        normalized = self._normalize_generic(item_copy)
                    else:
                        logger.debug(f"No specific normalizer for source '{source}', using generic handler.")
                        normalized = self._normalize_generic(item_copy)

                normalized_data.append(normalized)

            return normalized_data

        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return []

    # ────────────────────────────────────────────────────────────────────────────────
    # Optional Utility: discover available normalizers
    # ────────────────────────────────────────────────────────────────────────────────

    def list_available_normalizers(self) -> list:
        """Return a list of all available _normalize_* handlers for debugging or registry introspection."""
        return [
            name.replace("_normalize_", "")
            for name in dir(self)
            if name.startswith("_normalize_")
        ]

    # ────────────────────────────────────────────────────────────────────────────────
    # Individual Normalizers
    # ────────────────────────────────────────────────────────────────────────────────

    def _normalize_ipinfo(self, raw: dict) -> dict:
        source = raw.get('source', 'ipinfo')
        query_type = raw.get('query_type', 'unknown')
        indicator = canonical_ip(raw.get('ip', 'unknown'))
        raw_id = indicator
        ts = to_iso(datetime.utcnow())

        record = {
            'id': self._generate_id(source, raw_id, indicator),
            'source': source,
            'collector': 'ipinfo',
            'type': 'network_intel',
            'indicator': indicator,
            'timestamp': ts,
            'data': {
                'hostname': raw.get('hostname'),
                'city': raw.get('city'),
                'region': raw.get('region'),
                'country': raw.get('country'),
                'location': raw.get('loc'),
                'organization': raw.get('org'),
                'asn': raw.get('asn'),
                'privacy': raw.get('privacy')
            },
            'confidence': self._calculate_confidence(source, timestamp=ts),
            'evidence': [{
                'url': f"https://ipinfo.io/{indicator}",
                'collected_at': ts,
                'method': 'api_query'
            }],
            'metadata': {'query_type': query_type, 'raw_id': raw_id}
        }
        return record

    def _normalize_abuseipdb(self, raw: dict) -> dict:
        source = raw.get('source', 'abuseipdb')
        query_type = raw.get('query_type', 'unknown')
        indicator = canonical_ip(raw.get('ip', raw.get('ipAddress', 'unknown')))
        raw_id = indicator
        abuse_score = raw.get('abuse_confidence_score', raw.get('abuseConfidenceScore', 0))
        raw_score = float(abuse_score) / 100.0 if abuse_score else None
        ts = to_iso(datetime.utcnow())

        record = {
            'id': self._generate_id(source, raw_id, indicator),
            'source': source,
            'collector': 'abuseipdb',
            'type': 'threat_intel',
            'indicator': indicator,
            'timestamp': ts,
            'data': {
                'abuse_confidence_score': abuse_score,
                'country': raw.get('country_name'),
                'isp': raw.get('isp'),
                'domain': raw.get('domain'),
                'total_reports': raw.get('total_reports', 0)
            },
            'confidence': self._calculate_confidence(source, raw_score, ts),
            'evidence': [{
                'url': f"https://www.abuseipdb.com/check/{indicator}",
                'collected_at': ts,
                'method': 'api_query'
            }],
            'metadata': {'query_type': query_type, 'raw_id': raw_id}
        }
        return record

    def _normalize_twitter(self, item):
        """Handle Twitter API output."""
        try:
            text = item.get("text") or item.get("value") or "unknown"
            user = item.get("user", {}).get("screen_name", "unknown")
            return {
                "event": "normalize_complete",
                "source": "Twitter",
                "indicator": text,
                "confidence": 0.9,
                "user": user,
                "id": hashlib.sha256(f"{user}{text}".encode()).hexdigest()[:16],
                "collector": "twitter",
            }
        except Exception as e:
            logger.error(f"Twitter normalization failed: {e}")
            return {"event": "normalize_failed", "source": "Twitter", "error": str(e)}

    def _normalize_shodan(self, item):
        """Handle Shodan data."""
        ip = item.get("ip_str") or item.get("ip") or "unknown"
        org = item.get("org", "unknown")
        return {
            "event": "normalize_complete",
            "source": "Shodan",
            "indicator": ip,
            "organization": org,
            "confidence": 0.8,
            "id": hashlib.sha256(ip.encode()).hexdigest()[:16],
            "collector": "shodan",
        }

    def _normalize_urlscan(self, item):
        """Handle URLScan results."""
        domain = item.get("domain") or item.get("url") or "unknown"
        verdict = item.get("verdict", {}).get("score", 0.5)
        return {
            "event": "normalize_complete",
            "source": "URLScan",
            "indicator": domain,
            "confidence": verdict,
            "id": hashlib.sha256(domain.encode()).hexdigest()[:16],
            "collector": "urlscan",
        }
#--------------------------------------------------------------------------------------------------------------------------------
    def _normalize_generic(self, item: dict) -> dict:
        """
        Safe generic normalizer - handles ANY data structure
        """
        source = item.get('source', 'generic')
        raw = item.get('data') or item.get('raw', item)  # ✅ Try 'data' first
        query_type = item.get('query_type', 'unknown')

        # Defensive casting
        if not isinstance(raw, dict):
            raw = {"value": str(raw)}

        # Safe key extraction
        indicator = str(
            raw.get("indicator") or
            raw.get("domain") or
            raw.get("ip") or
            raw.get("query") or
            raw.get("value") or
            "unknown"
        )

        raw_id = str(raw.get("id", indicator))
        ts = to_iso(datetime.utcnow())

        record = {
            "id": self._generate_id(source, raw_id, indicator),
            "source": source,
            "collector": "generic",
            "type": "unstructured",
            "indicator": indicator,
            "timestamp": ts,
            "data": dict(raw),
            "confidence": self._calculate_confidence("generic", timestamp=ts),
            "correlation_hash": self._generate_correlation_hash(indicator),
            "evidence": [{
                "url": raw.get("url", "unknown"),
                "collected_at": ts,
                "method": "inferred"
            }],
            "metadata": {"query_type": query_type, "raw_id": raw_id},
        }
        return record

    def _normalize_crtsh(self, item: dict) -> dict:
        """Normalize crt.sh certificate search results into domain indicators."""
        source = item.get('source', 'crt.sh')
        raw = item.get('data') or item.get('raw', item)
        query_type = item.get('query_type', 'domain')

        ts = to_iso(datetime.utcnow())

        # attempt to extract domains list
        domains = []
        if isinstance(raw, dict):
            domains = raw.get('domains') or []
            # also accept certs list
            certs = raw.get('certificates') or []
            for c in certs:
                cn = c.get('common_name')
                if cn and cn not in domains:
                    domains.append(cn)

        primary = domains[0] if domains else raw.get('query') if isinstance(raw, dict) else str(raw)

        indicator = canonical_domain(primary) if primary else 'unknown'

        raw_id = str(indicator)

        record = {
            'id': self._generate_id(source, raw_id, indicator),
            'source': source,
            'collector': 'crt.sh',
            'type': 'certificate',
            'indicator': indicator,
            'timestamp': ts,
            'data': { 'domains': domains, 'raw': raw },
            'confidence': self._calculate_confidence(source, timestamp=ts),
            'evidence': [{ 'url': raw.get('query', 'unknown') if isinstance(raw, dict) else 'unknown', 'collected_at': ts }],
            'metadata': { 'query_type': query_type, 'raw_id': raw_id }
        }
        return record

    def _normalize_dns(self, item: dict) -> dict:
        """Normalize DNS lookup results into IP/domain indicators."""
        source = item.get('source', 'dns')
        raw = item.get('data') or item.get('raw', item)
        query_type = item.get('query_type', 'domain')

        ts = to_iso(datetime.utcnow())

        ip = None
        domain = None
        if isinstance(raw, dict):
            a = raw.get('A') or []
            if a:
                ip = a[0]
            domain = raw.get('query') or raw.get('domain')

        indicator = canonical_ip(ip) if ip else (canonical_domain(domain) if domain else 'unknown')
        raw_id = indicator

        record = {
            'id': self._generate_id(source, raw_id, indicator),
            'source': source,
            'collector': 'dns',
            'type': 'network_intel' if ip else 'domain',
            'indicator': indicator,
            'timestamp': ts,
            'data': raw,
            'confidence': self._calculate_confidence(source, timestamp=ts),
            'evidence': [{ 'url': 'dns_lookup', 'collected_at': ts }],
            'metadata': { 'query_type': query_type, 'raw_id': raw_id }
        }
        return record



# ────────────────────────────────────────────────────────────────────────────────
# Module-level helper for backward compatibility
# ────────────────────────────────────────────────────────────────────────────────

def normalize_data(source_name: str, raw: dict, query_type: str, schema_path: str = None) -> dict:
    """
    Compatibility wrapper for class-based normalization.
    Allows importing `normalize_data` directly from core.normalizer.
    """
    normalizer = DataNormalizer(schema_path)
    return normalizer.normalize(raw)