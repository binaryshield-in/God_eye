"""
Google Dorking Patterns Collector
Generates and tests common Google dorks for OSINT
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger('GodEye')

def generate_google_dorks(query: str, query_type: str) -> List[Dict[str, str]]:
    """Generate Google dorks based on query type"""
    
    dorks = []
    
    if query_type == 'domain':
        dorks = [
            {"name": "Site Search", "dork": f"site:{query}"},
            {"name": "Filetype PDF", "dork": f"site:{query} filetype:pdf"},
            {"name": "Configuration Files", "dork": f"site:{query} ext:xml | ext:conf | ext:cnf | ext:reg | ext:inf | ext:rdp | ext:cfg | ext:txt | ext:ora"},
            {"name": "Database Files", "dork": f"site:{query} ext:sql | ext:dbf | ext:mdb"},
            {"name": "Log Files", "dork": f"site:{query} ext:log"},
            {"name": "Backup Files", "dork": f"site:{query} ext:bkf | ext:bkp | ext:bak | ext:old | ext:backup"},
            {"name": "Login Pages", "dork": f"site:{query} inurl:login"},
            {"name": "Admin Pages", "dork": f"site:{query} inurl:admin"},
            {"name": "PHP Info", "dork": f"site:{query} ext:php intitle:phpinfo \"published by the PHP Group\""},
            {"name": "Index of", "dork": f"site:{query} \"index of/\""},
        ]
    
    elif query_type == 'email':
        dorks = [
            {"name": "Email in Text", "dork": f"\"{query}\""},
            {"name": "LinkedIn Profile", "dork": f"site:linkedin.com \"{query}\""},
            {"name": "GitHub Profile", "dork": f"site:github.com \"{query}\""},
            {"name": "Documents with Email", "dork": f"\"{query}\" filetype:pdf OR filetype:doc OR filetype:docx"},
        ]
    
    elif query_type == 'username':
        dorks = [
            {"name": "Exact Username", "dork": f"\"{query}\""},
            {"name": "Social Media", "dork": f"\"{query}\" site:twitter.com OR site:github.com OR site:reddit.com OR site:instagram.com"},
            {"name": "Forum Posts", "dork": f"\"{query}\" \"forums\" OR \"discussion\""},
        ]
    
    elif query_type == 'ip':
        dorks = [
            {"name": "IP Reference", "dork": f"\"{query}\""},
            {"name": "Server Related", "dork": f"\"{query}\" \"server\" OR \"host\" OR \"ip address\""},
        ]
    
    elif query_type == 'person':
        dorks = [
            {"name": "Exact Name", "dork": f"\"{query}\""},
            {"name": "Professional Profiles", "dork": f"\"{query}\" site:linkedin.com OR site:twitter.com"},
            {"name": "News Articles", "dork": f"\"{query}\" news"},
        ]
    
    return dorks

async def collect(query: str, session, query_type: str) -> Dict[str, Any]:
    """Generate Google dorking patterns for OSINT"""
    
    try:
        dorks = generate_google_dorks(query, query_type)
        
        result = {
            "generated_dorks": dorks,
            "total_dorks": len(dorks),
            "search_links": [
                {
                    "name": dork["name"],
                    "url": f"https://www.google.com/search?q={dork['dork'].replace(' ', '+')}",
                    "dork": dork["dork"]
                } for dork in dorks
            ]
        }
        
        return {
            "source": "Google Dorks",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Google Dorks collection failed: {str(e)}")
        return {
            "source": "Google Dorks",
            "data": None,
            "error": str(e)
        }