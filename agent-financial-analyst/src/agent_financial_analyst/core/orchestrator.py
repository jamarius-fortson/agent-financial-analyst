"""Institutional Research Orchestrator — Advanced Edition."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List

from opentelemetry import trace

from ..agents.document_analyst import DocumentAnalystAgent
from ..agents.fundamental import FundamentalAgent
from ..agents.market_data import MarketDataAgent
from ..agents.reviewer import ReviewerAgent
from ..agents.risk import RiskAgent
from ..agents.synthesis import SynthesisAgent
from ..agents.technical import TechnicalAgent
from ..schema.models import AgentOutput, ResearchReport
from ..utils.logging import get_logger

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


class ResearchOrchestrator:
    """
    Advanced orchestrator coordinating a 6-agent research cluster.
    """

    def __init__(
        self,
        main_model: str = "gpt-4o",
        mini_model: str = "gpt-4o-mini",
        enable_telemetry: bool = False,
    ):
        # Core Analytic cluster
        self.market_agent = MarketDataAgent(model=mini_model)
        self.fundamental_agent = FundamentalAgent(model=main_model)
        self.technical_agent = TechnicalAgent(model=mini_model)
        self.doc_agent = DocumentAnalystAgent(model=main_model)
        
        # Risk & Quality cluster
        self.risk_agent = RiskAgent(model=main_model)
        self.reviewer_agent = ReviewerAgent(model=main_model)
        self.synthesis_agent = SynthesisAgent(model=main_model)
        
        self.enable_telemetry = enable_telemetry

    @tracer.start_as_current_span("orchestrate_institutional_research")
    async def analyze(self, ticker: str) -> ResearchReport:
        """Run the full advanced pipeline."""
        start_t = time.perf_counter()
        task_id = f"research_{ticker}_{int(time.time())}"
        
        logger.info(f"🚀 INITIATING ADVANCED RESEARCH CLUSTER: {ticker}")
        
        # 1. Broad Market Data Fetch
        data_state = await self.market_agent.fetch(ticker)
        data_context = data_state.model_dump_json() # Use JSON for structured passing
        
        # 2. Triple-Analyst Deep Dive (Parallel)
        logger.info("🔍 PHASE 2: Concurrent multi-specialist deep dive")
        
        analyst_tasks = [
            self.fundamental_agent.analyze(ticker, data_context),
            self.technical_agent.analyze(ticker, data_context),
            self.doc_agent.analyze_filings(ticker)
        ]
        
        # Expert Pattern: gather with return_exceptions to prevent cascading failure
        results = await asyncio.gather(*analyst_tasks, return_exceptions=True)
        
        fundamental = results[0] if not isinstance(results[0], Exception) else f"Error in fundamental analysis: {results[0]}"
        technical = results[1] if not isinstance(results[1], Exception) else f"Error in technical analysis: {results[1]}"
        docs = results[2] if not isinstance(results[2], Exception) else f"Error in document analysis: {results[2]}"
        
        if any(isinstance(r, Exception) for r in results):
            logger.warning(f"⚠️ Partial failure in analyst cluster for {ticker}. Proceeding with degraded data.")
        
        # 3. Risk Intelligence
        logger.info("⚠️ PHASE 3: Multi-factor risk mapping")
        risks = await self.risk_agent.analyze(ticker, data_context)
        risk_text = "\n".join([f"- [{r.level}] {r.title}: {r.description}" for r in risks])
        
        # 4. Peer Review & Critique Loop
        logger.info("⚖️ PHASE 4: Institutional critique and bias check")
        draft_body = (
            f"FUNDAMENTAL: {fundamental[:1000]}\n\n"
            f"TECHNICAL: {technical[:1000]}\n\n"
            f"DOCUMENT: {docs[:1000]}\n\n"
            f"RISKS: {risk_text}"
        )
        critique = await self.reviewer_agent.review(draft_body)
        
        # 5. Executive Synthesis
        logger.info("📑 PHASE 5: Synthesis of final investment thesis")
        final_context = f"{draft_body}\n\nMANAGEMENT CRITIQUE:\n{critique}"
        
        exec_summary, build_conclusion = await self.synthesis_agent.summarize(
            ticker, fundamental, technical, f"{risk_text}\n\nREVIEWR NOTES:\n{critique}"
        )
        
        total_ms = (time.perf_counter() - start_t) * 1000
        
        # Construction of the institutional report
        return ResearchReport(
            task_id=task_id,
            ticker=ticker.upper(),
            created_at=datetime.utcnow(),
            executive_summary=exec_summary,
            company_context=data_state.metadata.description,
            fundamental_analysis=fundamental,
            technical_analysis=technical,
            risk_assessment=risks,
            conclusion=build_conclusion,
            data_snapshot=data_state,
            agent_traces=[], # Would be populated per agent in prod
            total_latency_ms=total_ms,
            total_cost_usd=0.25 # Mocked sum for demo
        )
