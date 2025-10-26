"""
Google Custom Search API Collector
Requires: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables
"""

import aiohttp
import os
import logging
from typing import Dict, Any

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> Dict[str, Any]:
    """Collect data from Google Custom Search API"""
    
    api_key = os.getenv('GOOGLE_API_KEY')
    cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key or not cse_id:
        logger.warning("GOOGLE_API_KEY or GOOGLE_CSE_ID not set")
        return {
            "source": "Google Search",
            "data": None,
            "error": "API credentials not configured"
        }
    
    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": 10
        }
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                # Extract search results
                search_results = []
                for item in data.get('items', []):
                    search_results.append({
                        "title": item.get('title'),
                        "link": item.get('link'),
                        "snippet": item.get('snippet'),
                        "displayLink": item.get('displayLink')
                    })
                
                result = {
                    "total_results": data.get('searchInformation', {}).get('totalResults', '0'),
                    "search_time": data.get('searchInformation', {}).get('searchTime'),
                    "results": search_results
                }
                
                return {
                    "source": "Google Search",
                    "data": result
                }
            else:
                error_data = await response.text()
                logger.warning(f"Google Search API returned status {response.status}: {error_data}")
                return {
                    "source": "Google Search",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"Google Search collection failed: {str(e)}")
        return {
            "source": "Google Search",
            "data": None,
            "error": str(e)
        }