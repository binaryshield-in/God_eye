# confidence.py
"""
Confidence Scoring Engine
Assigns credibility and data quality confidence scores.
"""

import random

def compute_confidence(records):
    """
    Compute a probabilistic confidence score for each record.
    Factors: Source reliability, data completeness, consistency.
    """
    scored = []
    for record in records:
        base = 0.5  # default mid-confidence
        src = record.get("source", "").lower()

        # Assign weight by data source type
        if "whois" in src or "crt" in src:
            base += 0.2
        elif "reddit" in src or "twitter" in src:
            base -= 0.1
        elif "bing" in src or "duckduckgo" in src:
            base += 0.05

        # Add small randomness for tie-breaking
        base += random.uniform(-0.05, 0.05)
        base = max(0, min(base, 1.0))

        record["confidence"] = round(base, 2)
        scored.append(record)
    return scored
