# resolver.py
"""
Entity Resolver
Resolves extracted names, domains, IPs, or emails into unique entities.
"""

import hashlib
import ipaddress


def resolve_entities(normalized_records):
    """
    Deduplicate and map entities to a unified identity representation.
    """
    entity_map = {}

    for record in normalized_records:
        for url in record.get("urls", []):
            entity_id = hashlib.sha256(url.encode()).hexdigest()[:16]
            entity_map[entity_id] = {
                "type": "url",
                "value": url,
                "source": record["source"]
            }

        for email in record.get("emails", []):
            entity_id = hashlib.sha256(email.encode()).hexdigest()[:16]
            entity_map[entity_id] = {
                "type": "email",
                "value": email,
                "source": record["source"]
            }

        # Optional: detect IP addresses
        words = record.get("content", "").split()
        for word in words:
            try:
                ipaddress.ip_address(word)
                entity_id = hashlib.sha256(word.encode()).hexdigest()[:16]
                entity_map[entity_id] = {
                    "type": "ip",
                    "value": word,
                    "source": record["source"]
                }
            except ValueError:
                continue

    return list(entity_map.values())
