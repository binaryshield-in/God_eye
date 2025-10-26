"""
GitHub API Collector
"""

import aiohttp
import logging
import os
from dotenv import load_dotenv

load_dotenv()  # load .env variables

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect GitHub user/repository information"""
    
    try:
        base_url = "https://api.github.com"
        
        if query_type == 'username':
            # Search for user
            user_url = f"{base_url}/users/{query}"
            async with session.get(user_url) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    # Get user repositories
                    repos_url = user_data.get('repos_url')
                    repos_data = []
                    if repos_url:
                        async with session.get(repos_url) as repos_response:
                            if repos_response.status == 200:
                                repos_data = await repos_response.json()
                                repos_data = repos_data[:10]  # Limit to 10 repos
                    
                    result = {
                        "user": user_data,
                        "repositories": repos_data
                    }
                    
                    return {
                        "source": "GitHub",
                        "data": result
                    }
                else:
                    return {
                        "source": "GitHub",
                        "data": None,
                        "error": f"User not found: HTTP {response.status}"
                    }
        else:
            # Search for repositories/organizations
            search_url = f"{base_url}/search/users"
            params = {"q": query}
            
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    search_data = await response.json()
                    return {
                        "source": "GitHub",
                        "data": {
                            "total_count": search_data.get('total_count'),
                            "items": search_data.get('items', [])[:5]
                        }
                    }
                else:
                    return {
                        "source": "GitHub",
                        "data": None,
                        "error": f"HTTP {response.status}"
                    }
                    
    except Exception as e:
        logger.error(f"GitHub collection failed: {str(e)}")
        return {
            "source": "GitHub",
            "data": None,
            "error": str(e)
        }