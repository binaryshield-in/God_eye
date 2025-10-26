"""
WHOIS Information Collector
"""

import whois
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger('GodEye')

async def collect(query: str, session, query_type: str) -> dict:
    """Collect WHOIS information"""
    
    try:
        # whois library is synchronous, so we run in executor
        loop = asyncio.get_event_loop()
        domain_info = await loop.run_in_executor(None, whois.whois, query)
        
        # Convert dates to strings for JSON serialization
        def serialize_dates(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, list):
                return [serialize_dates(item) for item in obj]
            return obj
        
        # Convert domain info to serializable dict
        whois_data = {}
        for key, value in domain_info.items():
            whois_data[key] = serialize_dates(value)
        
        result = {
            "domain_name": whois_data.get('domain_name'),
            "registrar": whois_data.get('registrar'),
            "creation_date": whois_data.get('creation_date'),
            "expiration_date": whois_data.get('expiration_date'),
            "updated_date": whois_data.get('updated_date'),
            "name_servers": whois_data.get('name_servers', []),
            "status": whois_data.get('status'),
            "emails": whois_data.get('emails', [])
        }
        
        return {
            "source": "WHOIS",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"WHOIS lookup failed: {str(e)}")
        return {
            "source": "WHOIS",
            "data": None,
            "error": str(e)
        }