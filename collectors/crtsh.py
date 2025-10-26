"""
crt.sh Certificate Transparency Collector
"""

import aiohttp
import logging

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect certificate transparency data from crt.sh"""
    
    try:
        url = "https://crt.sh/"
        params = {
            "q": f"%.{query}",
            "output": "json"
        }
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                # Process certificate data
                certificates = []
                domains = set()
                
                for cert in data[:50]:  # Limit results
                    common_name = cert.get('common_name', '')
                    name_value = cert.get('name_value', '')
                    
                    # Extract domains
                    if common_name:
                        domains.add(common_name)
                    if name_value:
                        for domain in name_value.split('\n'):
                            domains.add(domain.strip())
                    
                    certificates.append({
                        "id": cert.get('id'),
                        "logged_at": cert.get('entry_timestamp'),
                        "not_before": cert.get('not_before'),
                        "not_after": cert.get('not_after'),
                        "common_name": common_name,
                        "issuer_name": cert.get('issuer_name')
                    })
                
                result = {
                    "total_certificates": len(data),
                    "unique_domains": len(domains),
                    "domains": list(domains)[:20],  # Limit output
                    "certificates": certificates[:10]  # Limit output
                }
                
                return {
                    "source": "crt.sh",
                    "data": result
                }
            else:
                logger.warning(f"crt.sh returned status {response.status}")
                return {
                    "source": "crt.sh",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"crt.sh collection failed: {str(e)}")
        return {
            "source": "crt.sh",
            "data": None,
            "error": str(e)
        }