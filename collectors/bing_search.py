"""
Bing Web Search API Collector
Note: Requires BING_API_KEY environment variable
"""
"""
import aiohttp
import os
import logging

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    #Collect data from Bing Web Search
    
    api_key = os.getenv('BING_API_KEY')
    if not api_key:
        logger.warning("BING_API_KEY not set")
        return {
            "source": "Bing",
            "data": None,
            "error": "API key not configured"
        }
    
    try:
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key
        }
        params = {
            "q": query,
            "count": 10,
            "responseFilter": "Webpages,News"
        }
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                # Extract search results
                web_pages = data.get('webPages', {}).get('value', [])
                news = data.get('news', {}).get('value', [])
                
                result = {
                    "web_results": [
                        {
                            "name": page.get('name'),
                            "url": page.get('url'),
                            "snippet": page.get('snippet')
                        } for page in web_pages[:5]
                    ],
                    "news_results": [
                        {
                            "name": item.get('name'),
                            "url": item.get('url'),
                            "description": item.get('description')
                        } for item in news[:3]
                    ],
                    "total_estimated_matches": data.get('webPages', {}).get('totalEstimatedMatches')
                }
                
                return {
                    "source": "Bing",
                    "data": result
                }
            else:
                logger.warning(f"Bing API returned status {response.status}")
                return {
                    "source": "Bing",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"Bing collection failed: {str(e)}")
        return {
            "source": "Bing",
            "data": None,
            "error": str(e)
        }
    """