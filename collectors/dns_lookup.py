"""
DNS Lookup Collector using dnspython
"""

import asyncio
import dns.resolver
import dns.reversename
import logging
from typing import List, Dict

logger = logging.getLogger('GodEye')

async def collect(query: str, session, query_type: str) -> dict:
    """Perform comprehensive DNS lookups"""
    
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        resolver.lifetime = 10
        
        results = {}
        
        # DNS record types to check
        record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA']
        
        for record_type in record_types:
            try:
                answers = resolver.resolve(query, record_type)
                results[record_type] = [str(rdata) for rdata in answers]
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
                results[record_type] = []
        
        # Reverse DNS for IP addresses
        if query_type == 'ip':
            try:
                rev_name = dns.reversename.from_address(query)
                ptr_answers = resolver.resolve(rev_name, 'PTR')
                results['PTR'] = [str(rdata) for rdata in ptr_answers]
            except Exception:
                results['PTR'] = []
        
        return {
            "source": "DNS Lookup",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"DNS lookup failed: {str(e)}")
        return {
            "source": "DNS Lookup",
            "data": None,
            "error": str(e)
        }