"""
Shodan API Collector
Note: Requires SHODAN_API_KEY environment variable
"""

import aiohttp
import os
import logging

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect data from Shodan API"""
    
    api_key = os.getenv('SHODAN_API_KEY')
    if not api_key:
        logger.warning("SHODAN_API_KEY not set")
        return {
            "source": "Shodan",
            "data": None,
            "error": "API key not configured"
        }
    
    try:
        if query_type == 'ip':
            url = f"https://api.shodan.io/shodan/host/{query}"
            params = {"key": api_key}
        else:
            url = "https://api.shodan.io/shodan/host/search"
            params = {
                "key": api_key,
                "query": query,
                "minify": "true"
            }
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "source": "Shodan",
                    "data": data
                }
            else:
                logger.warning(f"Shodan API returned status {response.status}")
                return {
                    "source": "Shodan",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"Shodan collection failed: {str(e)}")
        return {
            "source": "Shodan",
            "data": None,
            "error": str(e)
        }