"""
Cache Utilities Module

This module provides utility functions for cache logging, monitoring,
and performance metrics collection.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from .semantic_cache import semantic_cache
from .redis_config import redis_config

logger = logging.getLogger(__name__)


def log_cache_hit(query: str, response_source: str, similarity_score: float = None):
    """
    Log cache hit events with detailed information.
    
    Args:
        query: The user query that resulted in a cache hit
        response_source: Source of the cached response (exact/semantic)
        similarity_score: Similarity score for semantic matches
    """
    log_data = {
        "event": "cache_hit",
        "query_length": len(query),
        "query_preview": query[:100] + "..." if len(query) > 100 else query,
        "response_source": response_source,
        "similarity_score": similarity_score,
        "timestamp": datetime.now().isoformat()
    }
    
    if similarity_score:
        logger.info(f"Cache hit ({response_source}): similarity={similarity_score:.3f}, query_length={len(query)}")
    else:
        logger.info(f"Cache hit ({response_source}): query_length={len(query)}")
    
    # Structured logging for analytics
    logger.debug(f"Cache hit data: {log_data}")


def log_cache_miss(query: str):
    """
    Log cache miss events with detailed information.
    
    Args:
        query: The user query that resulted in a cache miss
    """
    log_data = {
        "event": "cache_miss",
        "query_length": len(query),
        "query_preview": query[:100] + "..." if len(query) > 100 else query,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Cache miss: query_length={len(query)}")
    logger.debug(f"Cache miss data: {log_data}")


def log_cache_store(query: str, response_length: int):
    """
    Log cache storage events.
    
    Args:
        query: The user query being stored
        response_length: Length of the response being stored
    """
    log_data = {
        "event": "cache_store",
        "query_length": len(query),
        "response_length": response_length,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Cache store: query_length={len(query)}, response_length={response_length}")
    logger.debug(f"Cache store data: {log_data}")


def get_cache_performance_metrics() -> Dict[str, Any]:
    """
    Get comprehensive cache performance metrics.
    
    Returns:
        Dict containing cache performance metrics
    """
    try:
        # Get cache statistics
        cache_stats = semantic_cache.get_stats()
        
        # Get Redis connection info
        redis_info = redis_config.get_connection_info()
        
        # Calculate additional metrics
        total_entries = cache_stats.get("total_entries", 0)
        total_hits = cache_stats.get("total_hits", 0)
        hit_rate = cache_stats.get("hit_rate", 0)
        
        # Estimate cost savings (rough calculation)
        # Assuming average LLM call costs and cache hit savings
        avg_llm_cost_per_call = 0.002  # Rough estimate in USD
        estimated_savings = total_hits * avg_llm_cost_per_call
        
        metrics = {
            "cache_stats": cache_stats,
            "redis_info": redis_info,
            "performance": {
                "hit_rate_percentage": round(hit_rate * 100, 2),
                "total_cache_entries": total_entries,
                "total_cache_hits": total_hits,
                "estimated_cost_savings_usd": round(estimated_savings, 4),
                "embedding_cache_size": cache_stats.get("embedding_cache_size", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting cache performance metrics: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_cache_health_status() -> Dict[str, Any]:
    """
    Get cache health status for monitoring.
    
    Returns:
        Dict containing cache health information
    """
    try:
        # Check Redis connection
        redis_connected = redis_config.is_connected()
        
        # Get cache stats
        cache_stats = semantic_cache.get_stats()
        
        # Determine health status
        health_status = "healthy"
        issues = []
        
        if not redis_connected:
            health_status = "unhealthy"
            issues.append("Redis connection failed")
        
        if "error" in cache_stats:
            health_status = "degraded" if redis_connected else "unhealthy"
            issues.append(f"Cache stats error: {cache_stats['error']}")
        
        # Check if cache is empty (might be normal for new deployments)
        total_entries = cache_stats.get("total_entries", 0)
        if total_entries == 0 and redis_connected:
            issues.append("Cache is empty")
        
        health_info = {
            "status": health_status,
            "redis_connected": redis_connected,
            "cache_entries": total_entries,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error getting cache health status: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def warm_cache(common_queries: list) -> Dict[str, Any]:
    """
    Warm up the cache with common queries and their responses.
    
    Args:
        common_queries: List of common queries to pre-cache
        
    Returns:
        Dict containing warm-up results
    """
    results = {
        "total_queries": len(common_queries),
        "successful_warms": 0,
        "failed_warms": 0,
        "errors": []
    }
    
    logger.info(f"Starting cache warm-up with {len(common_queries)} queries")
    
    for query in common_queries:
        try:
            # This would typically involve generating responses for common queries
            # For now, we'll just log the attempt
            logger.info(f"Cache warm-up query: {query[:50]}...")
            results["successful_warms"] += 1
        except Exception as e:
            logger.error(f"Error warming up cache for query '{query[:50]}...': {e}")
            results["failed_warms"] += 1
            results["errors"].append(str(e))
    
    logger.info(f"Cache warm-up completed: {results['successful_warms']} successful, {results['failed_warms']} failed")
    return results


def cleanup_expired_entries() -> Dict[str, Any]:
    """
    Clean up expired cache entries (handled automatically by Redis TTL,
    but this function can be used for manual cleanup or additional logic).
    
    Returns:
        Dict containing cleanup results
    """
    try:
        # Redis automatically handles TTL expiration
        # This function can be extended for additional cleanup logic
        
        cache_stats = semantic_cache.get_stats()
        total_entries = cache_stats.get("total_entries", 0)
        
        cleanup_info = {
            "message": "Redis TTL handles automatic cleanup",
            "current_entries": total_entries,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Cache cleanup check completed (Redis handles TTL automatically)")
        return cleanup_info
        
    except Exception as e:
        logger.error(f"Error during cache cleanup: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


class CachePerformanceTimer:
    """
    Context manager for timing cache operations.
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            logger.debug(f"Cache operation '{self.operation_name}' completed in {duration:.4f}s")
        else:
            logger.warning(f"Cache operation '{self.operation_name}' failed after {duration:.4f}s: {exc_val}")
    
    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the operation."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None