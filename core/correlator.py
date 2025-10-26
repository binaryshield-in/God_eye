# correlator.py
"""
Entity Correlation Engine
Correlates entities across multiple data sources for intelligence linking.
"""

from collections import defaultdict


def correlate_entities(entities):
    """
    Identify overlapping entities across sources.
    e.g., same email appearing in GitHub and HaveIBeenPwned.
    """
    correlation_map = defaultdict(list)

    for entity in entities:
        value = entity["value"]
        correlation_map[value].append(entity["source"])

    correlated = []
    for value, sources in correlation_map.items():
        correlated.append({
            "entity": value,
            "count": len(sources),
            "sources": list(set(sources)),
            "linked": len(sources) > 1
        })

    return correlated
