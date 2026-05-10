"""Shared text utilities used across agents, services, and tools."""
import re
from typing import List


# Canonical set of business-relevant keywords for extraction and intent detection
BUSINESS_TERMS = {
    "revenue", "sales", "profit", "growth", "customer", "client",
    "marketing", "strategy", "budget", "forecast", "kpi", "metrics",
    "document", "contract", "invoice", "report", "analysis",
    "competitor", "market", "product", "service", "team", "hiring",
}


def extract_keywords(text: str) -> List[str]:
    """Extract business-relevant keywords from text.
    
    Finds words >= 3 chars that match the BUSINESS_TERMS set.
    Used by the orchestrator, model layer, and conversation insights.
    """
    words = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
    return list(words & BUSINESS_TERMS)
