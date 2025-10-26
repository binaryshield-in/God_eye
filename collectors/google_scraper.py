"""
Google Scraper - Use with caution and respect rate limits
This is for educational purposes only
"""

import aiohttp
import logging
from bs4 import BeautifulSoup
import asyncio
import random
from typing import Dict, Any, List

logger = logging.getLogger('GodEye')

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> Dict[str, Any]:
    """
    Basic Google scraping - USE WITH CAUTION
    Respect robots.txt and rate limits
    """
    
    try:
        # Add random delay to be respectful
        await asyncio.sleep(random.uniform(1, 3))
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        url = "https://www.google.com/search"
        params = {
            "q": query,
            "num": 10,
            "hl": "en"
        }
        
        async with session.get(url, params=params, headers=headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                results = []
                
                # Look for search result containers
                for g in soup.find_all('div', class_='g'):
                    title_element = g.find('h3')
                    link_element = g.find('a')
                    snippet_element = g.find('span', class_='aCOpRe')
                    
                    if title_element and link_element:
                        title = title_element.get_text()
                        link = link_element.get('href')
                        snippet = snippet_element.get_text() if snippet_element else ""
                        
                        # Filter out non-result links
                        if link and link.startswith('/url?q='):
                            # Extract actual URL from Google redirect
                            actual_link = link.split('/url?q=')[1].split('&')[0]
                            
                            results.append({
                                "title": title,
                                "link": actual_link,
                                "snippet": snippet
                            })
                
                result = {
                    "total_results": len(results),
                    "results": results[:5],  # Limit to 5 results
                    "note": "Scraped results - use with caution and respect rate limits"
                }
                
                return {
                    "source": "Google Scraper",
                    "data": result
                }
            elif response.status == 429:
                logger.warning("Google rate limit exceeded")
                return {
                    "source": "Google Scraper",
                    "data": None,
                    "error": "Rate limit exceeded - please wait before trying again"
                }
            else:
                logger.warning(f"Google returned status {response.status}")
                return {
                    "source": "Google Scraper",
                    "data": None,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"Google Scraper collection failed: {str(e)}")
        return {
            "source": "Google Scraper",
            "data": None,
            "error": str(e)
        }