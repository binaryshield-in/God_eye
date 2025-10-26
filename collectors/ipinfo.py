"""
IPinfo.io API Collector
Free tier: 50,000 requests/month
"""

import aiohttp
import logging
import os
from dotenv import load_dotenv

load_dotenv()  # load .env variables

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect IP information from IPinfo.io"""
    
    if query_type != 'ip':
        return {
            "source": "IPinfo",
            "data": None,
            "error": "Only IP addresses supported"
        }
    
    try:
        url = f"https://ipinfo.io/{query}/json"
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "source": "IPinfo",
                    "data": data
                }
            else:
                logger.warning(f"IPinfo API returned status {response.status}")
                return {
                    "source": "IPinfo",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"IPinfo collection failed: {str(e)}")
        return {
            "source": "IPinfo",
            "data": None,
            "error": str(e)
        }