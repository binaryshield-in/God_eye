"""
Have I Been Pwned API Collector
"""

import aiohttp
import hashlib
import logging

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Check if email/username appears in data breaches"""
    
    if query_type not in ['email', 'username']:
        return {
            "source": "HIBP",
            "data": None,
            "error": "Only emails and usernames supported"
        }
    
    try:
        # Hash the query for privacy
        query_hash = hashlib.sha1(query.encode('utf-8')).hexdigest().upper()
        prefix = query_hash[:5]
        
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.text()
                
                # Check if our hash suffix is in the results
                suffix = query_hash[5:]
                breaches = []
                
                for line in data.splitlines():
                    if line.startswith(suffix):
                        count = int(line.split(':')[1])
                        breaches.append({
                            "query": query,
                            "breach_count": count
                        })
                        break
                
                result = {
                    "breached": len(breaches) > 0,
                    "breaches": breaches
                }
                
                return {
                    "source": "HIBP",
                    "data": result
                }
            else:
                logger.warning(f"HIBP API returned status {response.status}")
                return {
                    "source": "HIBP",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"HIBP collection failed: {str(e)}")
        return {
            "source": "HIBP",
            "data": None,
            "error": str(e)
        }