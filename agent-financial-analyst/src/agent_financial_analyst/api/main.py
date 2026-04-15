"""FastAPI implementation for the institutional Research Analyst."""

from __future__ import annotations

import os
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..core.orchestrator import ResearchOrchestrator
from ..schema.models import ResearchReport
from ..utils.logging import setup_logging

# Initialize Logging
setup_logging(level="INFO")

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Agent Financial Analyst API",
    description="FAANG-level institutional equity research as a service.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Orchestrator
orchestrator = ResearchOrchestrator()


class ResearchRequest(BaseModel):
    ticker: str


@app.get("/")
def read_root():
    return {"status": "online", "description": "Agent Financial Analyst API"}


@app.post("/analyze", response_model=ResearchReport)
@limiter.limit("5/minute")
async def analyze_stock(request: ResearchRequest, req: Request):
    """
    Kicks off a full multi-agent institutional research report for the 
    specified stock ticker.
    """
    try:
        report = await orchestrator.analyze(request.ticker)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
