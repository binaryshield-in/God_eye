"""
Google Hacking Database (GHDB) Patterns Collector
Common search patterns for vulnerability discovery
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger('GodEye')

def get_ghdb_categories() -> List[Dict[str, str]]:
    """Get GHDB categories and examples"""
    
    return [
        {
            "category": "Sensitive Directories",
            "description": "Exposed directories with sensitive information",
            "examples": [
                "intitle:index.of /admin",
                "intitle:index.of /backup",
                "intitle:index.of /config"
            ]
        },
        {
            "category": "Configuration Files",
            "description": "Exposed configuration files",
            "examples": [
                "ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg",
                "filetype:env DB_PASSWORD",
                "filetype:config web.config"
            ]
        },
        {
            "category": "Database Dumps",
            "description": "Exposed database files and dumps",
            "examples": [
                "filetype:sql \"INSERT INTO\"",
                "filetype:mdb inurl:users",
                "filetype:log \"error\" \"password\""
            ]
        },
        {
            "category": "Login Portals",
            "description": "Various login and admin portals",
            "examples": [
                "inurl:login",
                "inurl:admin",
                "intitle:\"login\" \"password\"",
                "inurl:wp-admin"
            ]
        },
        {
            "category": "Vulnerable Servers",
            "description": "Servers with known vulnerabilities",
            "examples": [
                "intitle:\"phpinfo()\" \"PHP Version\"",
                "\"Apache/2.4\" \"Server at\"",
                "\"Microsoft-IIS/8.5\""
            ]
        },
        {
            "category": "Camera Feeds",
            "description": "Exposed network camera feeds",
            "examples": [
                "inurl:/view.shtml",
                "intitle:\"Live View / - AXIS\"",
                "inurl:axis-cgi/jpg"
            ]
        }
    ]

async def collect(query: str, session, query_type: str) -> Dict[str, Any]:
    """Get Google Hacking Database patterns"""
    
    try:
        categories = get_ghdb_categories()
        
        # Generate domain-specific dorks if query is a domain
        domain_dorks = []
        if query_type == 'domain':
            domain_dorks = [
                f"site:{query} {dork}"
                for category in categories
                for dork in category['examples'][:2]  # Take 2 examples per category
            ]
        
        result = {
            "ghdb_categories": categories,
            "domain_specific_dorks": domain_dorks if domain_dorks else None,
            "total_categories": len(categories),
            "reference": "Based on Google Hacking Database (GHDB) patterns"
        }
        
        return {
            "source": "GHDB",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"GHDB collection failed: {str(e)}")
        return {
            "source": "GHDB",
            "data": None,
            "error": str(e)
        }