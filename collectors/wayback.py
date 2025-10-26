"""
Wayback Machine API Collector
"""

import aiohttp
import logging

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect data from Wayback Machine"""
    
    try:
        # Get available snapshots
        cdx_url = "http://web.archive.org/cdx/search/cdx"
        params = {
            "url": query,
            "output": "json",
            "collapse": "urlkey",
            "limit": 20
        }
        
        async with session.get(cdx_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                # Parse CDX results
                snapshots = []
                if len(data) > 1:  # First row is headers
                    for row in data[1:]:
                        snapshots.append({
                            "timestamp": row[1],
                            "original": row[2],
                            "mimetype": row[3],
                            "status_code": row[4],
                            "digest": row[5],
                            "length": row[6]
                        })
                
                # Get total count
                count_params = params.copy()
                count_params['showNumPages'] = 'true'
                count_params['limit'] = '1'
                
                async with session.get(cdx_url, params=count_params) as count_response:
                    total_pages = await count_response.text() if count_response.status == 200 else "Unknown"
                
                result = {
                    "total_snapshots": len(snapshots),
                    "total_pages": total_pages.strip(),
                    "snapshots": snapshots[:10],  # Limit to 10
                    "wayback_url": f"https://web.archive.org/web/*/{query}"
                }
                
                return {
                    "source": "Wayback",
                    "data": result
                }
            else:
                logger.warning(f"Wayback API returned status {response.status}")
                return {
                    "source": "Wayback",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"Wayback collection failed: {str(e)}")
        return {
            "source": "Wayback",
            "data": None,
            "error": str(e)
        }