"""
Configuration for GodEye Google Collectors
"""

import os

# Google Custom Search API
# Get these from: https://developers.google.com/custom-search/v1/introduction
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')

# Rate limiting settings
GOOGLE_RATE_LIMIT_DELAY = 1  # seconds between requests