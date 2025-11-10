"""
LLM Core Module - LM Studio Integration

This module provides local LLM integration via LM Studio HTTP API.
Includes client, micro-agent system, fallback rules, and error handling.

Author: LLMExpert (Agenci Team)
"""

from .lm_studio_client import (
    LMStudioClient,
    LMStudioError,
    LMStudioConnectionError,
    LMStudioTimeoutError,
    get_lm_studio_client,
)
from .micro_agents import (
    MicroAgents,
    create_micro_agents,
    cached_micro_agent,
)
from .fallback_rules import (
    FallbackRules,
    log_fallback_usage,
)

__all__ = [
    # LM Studio Client
    "LMStudioClient",
    "LMStudioError",
    "LMStudioConnectionError",
    "LMStudioTimeoutError",
    "get_lm_studio_client",

    # Micro-Agents
    "MicroAgents",
    "create_micro_agents",
    "cached_micro_agent",

    # Fallback Rules
    "FallbackRules",
    "log_fallback_usage",
]
