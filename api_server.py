#!/usr/bin/env python3
"""
GodEye OSINT Platform - API Server
===================================
FastAPI middleware connecting dashboard UI with backend intelligence pipeline.
Handles async analysis requests, data normalization, and structured responses.

Author: BinaryShield
License: MIT
"""

import asyncio
import logging
import traceback
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
import uvicorn

# Import your core analysis engine
try:
    from main import analyze_query
except ImportError:
    async def analyze_query(query: str, query_type: str = "auto") -> Dict[str, Any]:
        """Mock analysis function for development"""
        logging.warning("Using mock analyze_query - implement main.py for production")
        return {
            "summary": f"Analysis completed for {query}",
            "confidence_avg": 0.75,
            "resource_count": 10,
            "indicators": [
                {
                    "indicator": query,
                    "type": query_type,
                    "confidence": 0.75,
                    "connections": 3,
                    "source": "mock"
                }
            ]
        }

# ═══════════════════════════════════════════════════════════
# FIX WINDOWS CONSOLE ENCODING FOR EMOJIS
# ═══════════════════════════════════════════════════════════

if sys.platform == 'win32':
    # Fix Windows console encoding
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# ═══════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("godeye.api")

# ═══════════════════════════════════════════════════════════
# PYDANTIC MODELS (Updated to V2)
# ═══════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query (domain, IP, email)")
    type: str = Field(default="auto", description="Query type (auto, domain, ip, email)")
    
    @field_validator('query')
    @classmethod
    def query_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed_types = ['auto', 'domain', 'ip', 'email']
        if v not in allowed_types:
            raise ValueError(f'Type must be one of: {", ".join(allowed_types)}')
        return v


class IndicatorModel(BaseModel):
    """Model for individual threat indicator"""
    indicator: str
    type: str
    confidence: float = Field(ge=0.0, le=1.0)
    connections: int = Field(ge=0)
    source: str


class AnalyticsModel(BaseModel):
    """Model for analytics metrics"""
    total_entities: int
    avg_confidence: float = Field(ge=0.0, le=1.0)
    source_count: int


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint"""
    status: str = Field(default="success")
    summary: str
    analytics: AnalyticsModel
    results: List[IndicatorModel]
    timestamp: str
    query_info: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error")
    message: str
    detail: Optional[str] = None
    timestamp: str


# ═══════════════════════════════════════════════════════════
# LIFESPAN CONTEXT MANAGER (FastAPI V2 Style)
# ═══════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    Replaces deprecated @app.on_event
    """
    # STARTUP
    logger.info("=" * 60)
    logger.info("GodEye OSINT API Server Starting...")
    logger.info("=" * 60)
    
    dashboard_path = Path(__file__).parent / "dashboard"
    logger.info(f"Dashboard path: {dashboard_path}")
    logger.info(f"Dashboard exists: {dashboard_path.exists()}")
    
    # Create results directory
    os.makedirs("results", exist_ok=True)
    logger.info("Results directory initialized")
    
    if not dashboard_path.exists():
        logger.warning("Dashboard directory not found! Create 'dashboard/' folder.")
    
    logger.info("Server initialization complete")
    
    yield  # Server is running
    
    # SHUTDOWN
    logger.info("GodEye OSINT API Server shutting down...")


# ═══════════════════════════════════════════════════════════
# FASTAPI APPLICATION SETUP
# ═══════════════════════════════════════════════════════════

app = FastAPI(
    title="GodEye OSINT API",
    description="AI-Powered Threat Intelligence Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan  # Use lifespan instead of on_event
)

# ─────────────────────────────────────────────────────────
# CORS Configuration
# ─────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Check this is present
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# Static Files (Serve Dashboard)
# ─────────────────────────────────────────────────────────

dashboard_path = Path(__file__).parent / "dashboard"
if dashboard_path.exists():
    app.mount("/static", StaticFiles(directory=str(dashboard_path / "static")), name="static")

# ═══════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ═══════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error occurred",
            "detail": str(exc) if app.debug else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════
# API ROUTES
# ═══════════════════════════════════════════════════════════

@app.get("/index.html", response_class=FileResponse)
async def serve_index():
    """Serve index.html"""
    index_file = dashboard_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/results.html", response_class=FileResponse)
async def serve_results():
    """Serve results.html"""
    results_file = dashboard_path / "results.html"
    if results_file.exists():
        return FileResponse(str(results_file))
    raise HTTPException(status_code=404, detail="Results page not found")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GodEye OSINT API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/status")
async def api_status():
    """API status endpoint with detailed information"""
    return {
        "status": "operational",
        "uptime": "healthy",
        "components": {
            "api": "operational",
            "analysis_engine": "operational",
            "database": "operational"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/search", response_model=AnalysisResponse)
async def search_analysis(request: AnalysisRequest):
    """
    Main analysis endpoint - accepts query and returns structured intelligence.
    """
    start_time = datetime.utcnow()
    logger.info(f"Received analysis request: {request.query} (type: {request.type})")
    
    try:
        # Call Backend Analysis Engine
        raw_results = await analyze_query(request.query, request.type)
        
        # Save Raw Results to output.json
        try:
            os.makedirs("results", exist_ok=True)
            output_path = "results/output.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(raw_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Raw results saved to {output_path}")
        except Exception as save_error:
            logger.error(f"Failed to save output.json: {save_error}")
        
        # Transform Results to Dashboard Format
        summary = raw_results.get('summary', f"Analysis completed for {request.query}")
        
        indicators = raw_results.get('indicators', [])
        total_entities = len(indicators)
        
        if total_entities > 0:
            avg_confidence = sum(ind.get('confidence', 0.5) for ind in indicators) / total_entities
        else:
            avg_confidence = 0.0
        
        unique_sources = len(set(ind.get('source', 'unknown') for ind in indicators))
        
        analytics = AnalyticsModel(
            total_entities=total_entities,
            avg_confidence=round(avg_confidence, 3),
            source_count=unique_sources
        )
        
        formatted_indicators = []
        for ind in indicators:
            try:
                formatted_indicators.append(IndicatorModel(
                    indicator=ind.get('indicator', 'unknown'),
                    type=ind.get('type', 'unknown'),
                    confidence=float(ind.get('confidence', 0.5)),
                    connections=int(ind.get('connections', 0)),
                    source=ind.get('source', 'unknown')
                ))
            except Exception as e:
                logger.warning(f"Failed to parse indicator: {e}")
                continue
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        response = AnalysisResponse(
            status="success",
            summary=summary,
            analytics=analytics,
            results=formatted_indicators,
            timestamp=datetime.utcnow().isoformat(),
            query_info={
                "query": request.query,
                "type": request.type,
                "processing_time": f"{processing_time:.2f}s"
            }
        )
        
        logger.info(f"Analysis completed successfully in {processing_time:.2f}s")
        logger.info(f"Found {total_entities} entities with avg confidence {avg_confidence:.2%}")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except TimeoutError:
        logger.error("Analysis timeout")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Analysis request timed out. Please try again."
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/api/analyze")
async def analyze_endpoint(request: AnalysisRequest):
    """Alternative analysis endpoint (alias for /api/search)"""
    return await search_analysis(request)


# ═══════════════════════════════════════════════════════════
# MIDDLEWARE FOR REQUEST LOGGING
# ═══════════════════════════════════════════════════════════

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    return response


# ═══════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GodEye OSINT API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    # Run server
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level="info",
        access_log=True
    )