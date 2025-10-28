"""
Semantic Cache Module for Digital Twin Application

This module provides semantic caching functionality using Redis and Gemini embeddings
to reduce LLM API calls while maintaining response quality.
"""

from .redis_config import redis_config
from .semantic_cache import semantic_cache
from .utils import log_cache_hit, log_cache_miss, get_cache_performance_metrics

__all__ = [
    'redis_config',
    'semantic_cache', 
    'log_cache_hit',
    'log_cache_miss',
    'get_cache_performance_metrics'
]