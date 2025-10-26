#!/usr/bin/env python3
"""
GodEye - OSINT Data Collection Orchestrator
Enhanced with AI Summary Generation
"""

import asyncio
import aiohttp
import aiosqlite
import json
import logging
import argparse
import sys
import os
from typing import List, Dict, Any
import importlib
import importlib.util
import glob
from dotenv import load_dotenv
from datetime import datetime, timezone

# Import normalization pipeline
from core.pipeline import NormalizationPipeline  
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('godeye.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('GodEye')


# -----------------------------------------------------------
# Cache Manager
# -----------------------------------------------------------
class CacheManager:
    """SQLite cache for API responses"""
    
    def __init__(self, db_path: str = "cache/cache.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    async def init_db(self):
        """Initialize cache database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
    
    async def get(self, key: str) -> Any:
        """Get cached value"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM cache WHERE key = ?", (key,)
            ) as cursor:
                result = await cursor.fetchone()
                return json.loads(result[0]) if result else None
    
    async def set(self, key: str, value: Any):
        """Set cached value"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "REPLACE INTO cache (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
            await db.commit()


# -----------------------------------------------------------
# Collector Manager
# -----------------------------------------------------------
class CollectorManager:
    """Manages and executes OSINT collectors"""
    
    def __init__(self):
        self.collectors = {}
        self.cache = CacheManager()
        self.session = None
    
    async def load_collectors(self):
        """Dynamically load all collector modules"""
        collector_files = glob.glob("collectors/*.py")
        
        for file_path in collector_files:
            module_name = os.path.basename(file_path)[:-3]
            if module_name == "__init__":
                continue
                
            try:
                spec = importlib.util.spec_from_file_location(
                    module_name, file_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'collect'):
                    self.collectors[module_name] = module.collect
                    logger.info(f" Loaded collector: {module_name}")
                else:
                    logger.warning(f"  No collect function in {module_name}")
                    
            except Exception as e:
                logger.error(f" Failed to load {module_name}: {str(e)}")
    
    async def execute_collector(self, collector_name: str, query: str, query_type: str) -> Dict[str, Any]:
        """Execute a single collector with error handling"""
        try:
            cache_key = f"{collector_name}:{query_type}:{query}"
            cached = await self.cache.get(cache_key)
            if cached:
                logger.info(f" Cache hit for {collector_name}")
                return cached
            
            if collector_name in self.collectors:
                logger.info(f" Executing {collector_name} for {query}")
                
                result = await self.collectors[collector_name](
                    query=query, 
                    session=self.session,
                    query_type=query_type
                )
                
                if result and result.get('data'):
                    await self.cache.set(cache_key, result)
                
                return result
            else:
                logger.warning(f" Collector {collector_name} not found")
                return None
                
        except Exception as e:
            logger.error(f" Collector {collector_name} failed: {str(e)}")
            return {
                "source": collector_name,
                "data": None,
                "error": str(e)
            }
    
    async def collect_all(self, query: str, query_type: str, selected_collectors: List[str] = None) -> Dict[str, Any]:
        """Execute all collectors in parallel"""
        await self.cache.init_db()
        
        collectors_to_run = selected_collectors if selected_collectors else list(self.collectors.keys())
        
        if not collectors_to_run:
            logger.warning(" No collectors available. Returning mock data.")
            return {
                "input": query,
                "type": query_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": [{
                    "source": "mock",
                    "data": {
                        "indicator": query,
                        "type": query_type,
                        "confidence": 0.75
                    }
                }]
            }
        
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=10)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            self.session = session
            
            tasks = []
            for collector_name in collectors_to_run:
                task = self.execute_collector(collector_name, query, query_type)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f" Collector task failed: {str(result)}")
                elif result is not None:
                    valid_results.append(result)
            
            return {
                "input": query,
                "type": query_type,           
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "results": valid_results
            }


# -----------------------------------------------------------
# AI Summary Generator
# -----------------------------------------------------------
def generate_ai_summary(query: str, indicators: List[Dict], query_type: str) -> str:
    """
    Generate human-readable AI summary from analysis results
    
    Args:
        query: Original search query
        indicators: List of threat indicators
        query_type: Type of query (domain, ip, email)
    
    Returns:
        Formatted AI summary string
    """
    entity_count = len(indicators)
    
    # No entities found
    if entity_count == 0:
        return (
            f"No threat intelligence found for '{query}'. "
            f"The indicator appears clean with no known malicious associations "
            f"across monitored intelligence sources."
        )
    
    # Calculate average confidence
    avg_confidence = sum(ind.get('confidence', 0.5) for ind in indicators) / entity_count if entity_count > 0 else 0
    
    # Determine risk level
    if avg_confidence >= 0.8:
        risk_level = "high"
        risk_color = "red"
        risk_desc = "Critical threat indicators detected"
        recommendation = "Immediate investigation recommended. Block or monitor this indicator closely."
    elif avg_confidence >= 0.6:
        risk_level = "moderate"
        risk_color = "orange"
        risk_desc = "Moderate risk indicators identified"
        recommendation = "Further investigation recommended. Consider adding to watchlist."
    elif avg_confidence >= 0.4:
        risk_level = "low"
        risk_color = "yellow"
        risk_desc = "Low-confidence indicators observed"
        recommendation = "Monitoring suggested. No immediate action required."
    else:
        risk_level = "minimal"
        risk_color = "blue"
        risk_desc = "Minimal threat indicators detected"
        recommendation = "No immediate concerns. Continue routine monitoring."
    
    # Count unique sources
    sources = set(ind.get('source', 'unknown') for ind in indicators)
    source_count = len(sources)
    
    # Build comprehensive summary
    summary = (
        f"{risk_color} Analysis of '{query}' ({query_type}) identified {entity_count} related "
        f"{'entity' if entity_count == 1 else 'entities'} across {source_count} intelligence "
        f"{'source' if source_count == 1 else 'sources'}. {risk_desc} with an average confidence "
        f"score of {avg_confidence:.0%}. {recommendation}"
    )
    
    return summary


# -----------------------------------------------------------
# Async Analysis Function (Called by api_server.py)
# -----------------------------------------------------------
async def analyze_query(query: str, query_type: str = "auto", selected_collectors: List[str] = None, timeout: int = 60) -> Dict[str, Any]:
    """
    Programmatic entrypoint for the API server to run an analysis.
    Returns JSON-serializable dictionary only.
    
    Args:
        query: Search query (domain, IP, email, etc.)
        query_type: Type of query (auto, domain, ip, email)
        selected_collectors: Specific collectors to run (None = all)
        timeout: Request timeout in seconds
    
    Returns:
        Dict containing summary and indicators (JSON serializable only)
    """
    try:
        logger.info(f"[ANALYSIS] Starting for: {query} (type: {query_type})")
        
        # Initialize collector manager
        manager = CollectorManager()
        await manager.load_collectors()

        # Run collectors
        results = await manager.collect_all(query, query_type, selected_collectors)
        
        # Save raw collector results immediately
        try:
            os.makedirs("results", exist_ok=True)
            with open("results/output.json", "w", encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info("[SAVE] Raw collector results saved to results/output.json")
        except Exception as save_error:
            logger.error(f"[ERROR] Failed to save output.json: {save_error}")

        # Run normalization pipeline
        try:
            pipeline = NormalizationPipeline()
            normalized_output = pipeline.run(results, query_type)
            logger.info("[PIPELINE] Normalization completed")
            
            # Save normalized data
            try:
                with open("results/normalized.jsonl", "w", encoding="utf-8") as f:
                    for entry in normalized_output.get("normalized", []):
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

                with open("results/entities.json", "w", encoding="utf-8") as f:
                    json.dump(normalized_output.get("entities", []), f, indent=2, ensure_ascii=False)

                with open("results/analytics.json", "w", encoding="utf-8") as f:
                    # Filter out non-serializable objects
                    analytics = normalized_output.get("analytics", {})
                    safe_analytics = {}
                    for k, v in analytics.items():
                        try:
                            json.dumps(v)
                            safe_analytics[k] = v
                        except (TypeError, ValueError):
                            logger.debug(f"Skipping non-serializable analytics key: {k}")
                    json.dump(safe_analytics, f, indent=2, ensure_ascii=False)

                logger.info("[SAVE] Normalization files saved successfully")
            except Exception as norm_save_error:
                logger.error(f"[ERROR] Failed to save normalization files: {norm_save_error}")
                
        except Exception as norm_error:
            logger.error(f"[ERROR] Normalization failed: {norm_error}", exc_info=True)
            normalized_output = {"entities": [], "normalized": [], "analytics": {}}

        # Build indicators list from normalized entities
        entities = normalized_output.get("entities") or normalized_output.get("normalized") or []
        indicators = []
        
        for ent in entities:
            try:
                indicators.append({
                    "indicator": ent.get("indicator") or ent.get("id") or ent.get("entity") or str(ent),
                    "type": ent.get("type", "unknown"),
                    "confidence": float(ent.get("confidence", 0.5)),
                    "connections": int(ent.get("connections", 0)) if ent.get("connections") is not None else 0,
                    "source": ent.get("source", "normalized")
                })
            except Exception as parse_error:
                logger.warning(f"[WARN] Failed to parse entity: {parse_error}")
                # Fallback simple representation
                indicators.append({
                    "indicator": str(ent),
                    "type": "unknown",
                    "confidence": 0.5,
                    "connections": 0,
                    "source": "normalized"
                })

        # Generate AI summary
        summary = generate_ai_summary(query, indicators, query_type)
        logger.info(f"[SUCCESS] Generated AI summary for {len(indicators)} indicators")

        # ✅ RETURN ONLY JSON-SERIALIZABLE DATA
        return {
            "summary": summary,
            "indicators": indicators
            # Note: We don't return raw_results or normalized_output 
            # because they contain non-serializable objects (DiGraph, etc.)
        }

    except Exception as e:
        logger.error(f"[FATAL] analyze_query failed: {e}", exc_info=True)
        return {
            "summary": f"Analysis failed: {str(e)}",
            "indicators": [],
            "error": str(e)
        }
    
    
# -----------------------------------------------------------
# Main CLI Orchestration
# -----------------------------------------------------------
async def main():
    """Command-line interface for GodEye"""
    parser = argparse.ArgumentParser(description='GodEye OSINT Data Collector')
    parser.add_argument('--query', type=str, required=True, help='Query to investigate')
    parser.add_argument('--type', type=str, required=True, 
                       choices=['person', 'username', 'domain', 'ip', 'email', 'image'],
                       help='Type of query')
    parser.add_argument('--collectors', type=str, nargs='+', 
                       help='Specific collectors to run (default: all)')
    parser.add_argument('--output', type=str, default='results/output.json',
                       help='Output file path')
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logging output')

    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Initialize manager
    manager = CollectorManager()
    await manager.load_collectors()
    
    logger.info(f" Starting collection for {args.query} (type: {args.type})")
    
    # Run collectors
    results = await manager.collect_all(
        query=args.query,
        query_type=args.type,
        selected_collectors=args.collectors
    )
    
    # Run normalization pipeline
    try:
        pipeline = NormalizationPipeline()
        normalized_output = pipeline.run(results, args.type)

        # Save normalized entities
        with open("results/normalized.jsonl", "w", encoding="utf-8") as f:
            for entry in normalized_output.get("normalized", []):
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        with open("results/entities.json", "w", encoding="utf-8") as f:
            json.dump(normalized_output.get("entities", []), f, indent=2, ensure_ascii=False)

        with open("results/analytics.json", "w", encoding="utf-8") as f:
            json.dump(normalized_output.get("analytics", {}), f, indent=2, ensure_ascii=False)

        logger.info(" Normalization pipeline executed successfully")
    
    except Exception as e:
        logger.error(f" Normalization pipeline failed: {str(e)}", exc_info=True)

    # Save raw results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f" Collection complete. Results saved to {args.output}")

    # Print summary
    successful = len([r for r in results['results'] if r.get('data')])
    total = len(results['results'])
    
    print("\n" + "="*60)
    print(" COLLECTION SUMMARY")
    print("="*60)
    print(f" Successful: {successful}/{total} collectors")
    print(f" Raw Output: {args.output}")
    print(f" Normalized Output: results/normalized.jsonl")
    print(f" Entities: results/entities.json")
    print(f" Analytics: results/analytics.json")
    print("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())