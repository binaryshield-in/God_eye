"""
Twitter Data Collector with API fallback
"""

import asyncio
import logging
import subprocess
import json
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('GodEye')

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")


async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> dict:
    """Collect Twitter data using API if available, else fallback to snscrape"""

    try:
        # If you have an API key, use the Twitter API (v2)
        if TWITTER_API_KEY:
            headers = {
                "Authorization": f"Bearer {TWITTER_API_KEY}",
                "User-Agent": "GodEyeOSINT/1.0"
            }

            if query_type == 'username':
                url = f"https://api.x.com/2/users/by/username/{query}"
            else:
                url = f"https://api.x.com/2/tweets/search/recent?query={query}&max_results=10"

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "source": "Twitter API",
                        "data": data
                    }
                else:
                    logger.warning(f"Twitter API returned {response.status}")
                    return {
                        "source": "Twitter API",
                        "data": None,
                        "error": f"HTTP {response.status}"
                    }

        # If no API key, fallback to snscrape
        else:
            if query_type == 'username':
                cmd = [
                    'snscrape', '--jsonl', '--max-results', '1',
                    'twitter-user', query
                ]
            else:
                cmd = [
                    'snscrape', '--jsonl', '--max-results', '10',
                    'twitter-search', query
                ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                data = [json.loads(line) for line in lines if line]
                return {
                    "source": "Twitter (snscrape)",
                    "data": data
                }
            else:
                error_msg = stderr.decode().strip()
                logger.warning(f"snscrape failed: {error_msg}")
                return {
                    "source": "Twitter (snscrape)",
                    "data": None,
                    "error": error_msg
                }

    except Exception as e:
        logger.error(f"Twitter collection failed: {str(e)}")
        return {
            "source": "Twitter",
            "data": None,
            "error": str(e)
        }
