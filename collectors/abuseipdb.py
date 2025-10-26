"""
AbuseIPDB API Collector
Note: Requires ABUSEIPDB_API_KEY environment variable
"""

import aiohttp
import os
import logging

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect IP reputation from AbuseIPDB"""
    
    if query_type != 'ip':
        return {
            "source": "AbuseIPDB",
            "data": None,
            "error": "Only IP addresses supported"
        }
    
    api_key = os.getenv('ABUSEIPDB_API_KEY')
    if not api_key:
        logger.warning("ABUSEIPDB_API_KEY not set")
        return {
            "source": "AbuseIPDB",
            "data": None,
            "error": "API key not configured"
        }
    
    try:
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Key": api_key,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": query,
            "maxAgeInDays": 90,
            "verbose": "true"
        }
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "source": "AbuseIPDB",
                    "data": data.get('data', {})
                }
            else:
                logger.warning(f"AbuseIPDB API returned status {response.status}")
                return {
                    "source": "AbuseIPDB",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"AbuseIPDB collection failed: {str(e)}")
        return {
            "source": "AbuseIPDB",
            "data": None,
            "error": str(e)
        }