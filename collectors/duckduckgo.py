"""
DuckDuckGo Instant Answer API Collector
- No API key required.
- Robust: timeout, retries, user-agent, consistent return schema.
"""

import json
import os
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Optional: load .env in dev (make sure .env is in .gitignore)
load_dotenv()

logger = logging.getLogger('GodEye')

# Configurable parameters (change via env or defaults)
USER_AGENT = os.getenv("GODEYE_USER_AGENT", "GodEye/1.0 (+https://github.com/yourorg/godeye)")
REQUEST_TIMEOUT = float(os.getenv("GODEYE_DDG_TIMEOUT", "12"))  # seconds
RETRIES = int(os.getenv("GODEYE_DDG_RETRIES", "3"))
BACKOFF_FACTOR = float(os.getenv("GODEYE_DDG_BACKOFF", "0.8"))
MIN_DELAY = float(os.getenv("GODEYE_DDG_MIN_DELAY", "0.15"))  # polite delay between calls

async def _fetch(session: aiohttp.ClientSession, url: str, params: dict) -> Optional[dict]:
    """Internal fetch wrapper with timeout and backoff; returns JSON or None."""
    attempt = 0
    while attempt < RETRIES:
        try:
            headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
            timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            async with session.get(url, params=params, headers=headers, timeout=timeout) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return json.loads(text)

                # handle rate-limit or server error
                if 500 <= resp.status < 600:
                    logger.warning(f"DuckDuckGo returned {resp.status}; retrying (attempt {attempt+1})")
                else:
                    # client error (4xx) — no retry
                    text = await resp.text()
                    logger.debug(f"DuckDuckGo non-200: {resp.status} body={text[:200]}")
                    return {"_http_status": resp.status, "_raw_text": text}
        except asyncio.TimeoutError:
            logger.warning(f"DuckDuckGo request timed out (attempt {attempt+1})")
        except Exception as e:
            logger.exception(f"Unexpected fetch error (attempt {attempt+1}): {e}")
        # backoff
        attempt += 1
        await asyncio.sleep(BACKOFF_FACTOR * (2 ** (attempt - 1)))
    return None

async def collect(query: str, session: aiohttp.ClientSession, query_type: str) -> Dict[str, Any]:
    """
    Collect data from DuckDuckGo Instant Answers.
    Returns a dict: { source, data, error (optional), meta (optional) }
    """
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1"
    }

    # polite pacing — avoid hammering free endpoints when multiple collectors run
    await asyncio.sleep(MIN_DELAY)

    try:
        data = await _fetch(session, url, params)
        if data is None:
            return {"source": "DuckDuckGo", "data": None, "error": "timeout/retries_exhausted"}
        # if API returned raw text (non-JSON), propagate an error
        if isinstance(data, dict) and data.get("_http_status"):
            return {"source": "DuckDuckGo", "data": None, "error": f"HTTP {data.get('_http_status')}", "meta": {"raw": data.get("_raw_text")[:500]}}

        # Normalize output: pick the most useful fields
        result = {
            "abstract": data.get("Abstract"),
            "abstract_text": data.get("AbstractText"),
            "abstract_source": data.get("AbstractSource"),
            "abstract_url": data.get("AbstractURL"),
            "image": data.get("Image"),
            "related_topics": [
                {"text": t.get("Text"), "url": t.get("FirstURL")}
                for t in (data.get("RelatedTopics") or [])[:6]
            ],
            "results": data.get("Results", [])[:4]
        }

        return {"source": "DuckDuckGo", "data": result}
    except Exception as e:
        logger.exception("DuckDuckGo collection failed")
        return {"source": "DuckDuckGo", "data": None, "error": str(e)}
