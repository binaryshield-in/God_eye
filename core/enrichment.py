# enrichment.py
"""
Data Enrichment Layer
Adds context to entities using open-source intelligence lookups.
"""

import requests


def enrich_data(entities):
    """
    Add enrichment data like GeoIP, ASN, or breach status.
    (Example uses free APIs.)
    """
    enriched = []

    for ent in entities:
        data = ent.copy()
        value = ent["value"]

        if ent["type"] == "ip":
            try:
                resp = requests.get(f"https://ipinfo.io/{value}/json", timeout=5)
                if resp.status_code == 200:
                    data["geo"] = resp.json()
            except Exception:
                pass

        elif ent["type"] == "email":
            data["breach_status"] = "unknown"  # can later integrate HIBP

        elif ent["type"] == "url":
            data["domain_category"] = value.split(".")[-1]

        enriched.append(data)
    return enriched
