"""
Semantic Cache Module

This module implements semantic caching using Redis and Gemini embeddings
to reduce LLM API calls by finding semantically similar queries.
"""

import os
import json
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from scipy.spatial.distance import cosine
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .redis_config import redis_config

logger = logging.getLogger(__name__)


class SemanticCache:
    """
    Semantic cache that stores query-response pairs and retrieves them
    based on semantic similarity using embeddings.
    """
    
    def __init__(self):
        """Initialize the semantic cache with configuration from environment variables."""
        self.redis_client = redis_config.get_client()
        self.similarity_threshold = float(os.getenv("CACHE_SIMILARITY_THRESHOLD", 0.85))
        self.ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", 604800))  # 7 days
        
        # Initialize embeddings model using Gemini
        try:
            self.embeddings_model = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                task_type="retrieval_query"
            )
            logger.info("Initialized Gemini embeddings model")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings model: {e}")
            raise
        
        # Cache for embeddings to avoid recomputation
        self._embedding_cache = {}
        self._max_embedding_cache_size = 1000
        
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for text using Gemini.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            np.ndarray: Embedding vector
        """
        # Check local cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self._embedding_cache:
            return self._embedding_cache[text_hash]
        
        try:
            embedding = self.embeddings_model.embed_query(text)
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Cache the embedding (with size limit)
            if len(self._embedding_cache) >= self._max_embedding_cache_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self._embedding_cache))
                del self._embedding_cache[oldest_key]
            
            self._embedding_cache[text_hash] = embedding_array
            return embedding_array
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        try:
            # Using 1 - cosine distance to get similarity
            similarity = 1 - cosine(embedding1, embedding2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _get_cache_key(self, embedding_hash: str) -> str:
        """Generate Redis key for cache entry."""
        return f"cache:{embedding_hash}"
    
    def _get_similarity_index_key(self) -> str:
        """Generate Redis key for similarity index."""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"similarity_index:{today}"
    
    def _hash_embedding(self, embedding: np.ndarray) -> str:
        """Generate hash for embedding."""
        return hashlib.md5(embedding.tobytes()).hexdigest()
    
    def search_similar(self, query: str) -> Optional[str]:
        """
        Search for semantically similar cached responses.
        
        Args:
            query: User query to search for
            
        Returns:
            Optional[str]: Cached response if found, None otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available, skipping cache search")
            return None
            
        try:
            # Generate embedding for query
            query_embedding = self._get_embedding(query)
            query_hash = self._hash_embedding(query_embedding)
            
            # Check exact match first
            exact_match_key = self._get_cache_key(query_hash)
            cached_response = self.redis_client.get(exact_match_key)
            if cached_response:
                logger.info(f"Cache hit (exact): {query_hash}")
                self._increment_hit_count(query_hash)
                return json.loads(cached_response)["response"]
            
            # Search for similar embeddings
            similarity_index_key = self._get_similarity_index_key()
            cached_hashes = self.redis_client.zrange(similarity_index_key, 0, -1)
            
            best_match = None
            best_similarity = 0.0
            best_hash = None
            
            for cached_hash in cached_hashes:
                cached_hash = cached_hash.decode('utf-8')
                cache_key = self._get_cache_key(cached_hash)
                cached_data = self.redis_client.get(cache_key)
                
                if cached_data:
                    try:
                        data = json.loads(cached_data)
                        cached_embedding = np.array(data["embedding"], dtype=np.float32)
                        similarity = self._calculate_similarity(query_embedding, cached_embedding)
                        
                        if similarity > best_similarity and similarity >= self.similarity_threshold:
                            best_similarity = similarity
                            best_match = data["response"]
                            best_hash = cached_hash
                    except Exception as e:
                        logger.warning(f"Error processing cached entry {cached_hash}: {e}")
                        continue
            
            if best_match:
                logger.info(f"Cache hit (semantic): similarity={best_similarity:.3f}")
                self._increment_hit_count(best_hash)
                return best_match
            
            logger.info("Cache miss")
            return None
            
        except Exception as e:
            logger.error(f"Error searching cache: {e}")
            return None
    
    def store(self, query: str, response: str) -> bool:
        """
        Store query-response pair in cache.
        
        Args:
            query: User query
            response: LLM response
            
        Returns:
            bool: True if stored successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available, skipping cache storage")
            return False
            
        try:
            # Generate embedding for query
            query_embedding = self._get_embedding(query)
            query_hash = self._hash_embedding(query_embedding)
            
            # Prepare cache entry
            cache_entry = {
                "message": query,
                "response": response,
                "embedding": query_embedding.tolist(),
                "timestamp": datetime.now().isoformat(),
                "hit_count": 0
            }
            
            # Store in Redis with TTL
            cache_key = self._get_cache_key(query_hash)
            self.redis_client.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(cache_entry)
            )
            
            # Add to similarity index
            similarity_index_key = self._get_similarity_index_key()
            self.redis_client.zadd(
                similarity_index_key,
                {query_hash: datetime.now().timestamp()}
            )
            self.redis_client.expire(similarity_index_key, self.ttl_seconds)
            
            logger.info(f"Stored in cache: {query_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False
    
    def _increment_hit_count(self, cache_hash: str):
        """
        Increment hit count for a cache entry.
        
        Args:
            cache_hash: Hash of the cached entry
        """
        if not self.redis_client:
            return
            
        try:
            cache_key = self._get_cache_key(cache_hash)
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                data["hit_count"] = data.get("hit_count", 0) + 1
                self.redis_client.set(
                    cache_key,
                    json.dumps(data),
                    ex=self.ttl_seconds
                )
        except Exception as e:
            logger.warning(f"Error incrementing hit count: {e}")
    
    def get_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dict: Cache statistics
        """
        if not self.redis_client:
            return {"error": "Redis client not available"}
            
        try:
            # Count total cache entries
            similarity_index_key = self._get_similarity_index_key()
            total_entries = self.redis_client.zcard(similarity_index_key)
            
            # Calculate total hit counts
            total_hits = 0
            cached_hashes = self.redis_client.zrange(similarity_index_key, 0, -1)
            
            for cached_hash in cached_hashes:
                cached_hash = cached_hash.decode('utf-8')
                cache_key = self._get_cache_key(cached_hash)
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    total_hits += data.get("hit_count", 0)
            
            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "hit_rate": total_hits / max(total_entries, 1),
                "ttl_seconds": self.ttl_seconds,
                "similarity_threshold": self.similarity_threshold,
                "embedding_cache_size": len(self._embedding_cache)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available, skipping cache clear")
            return False
            
        try:
            similarity_index_key = self._get_similarity_index_key()
            cached_hashes = self.redis_client.zrange(similarity_index_key, 0, -1)
            
            # Delete all cache entries
            pipe = self.redis_client.pipeline()
            for cached_hash in cached_hashes:
                cache_key = self._get_cache_key(cached_hash.decode('utf-8'))
                pipe.delete(cache_key)
            
            # Delete similarity index
            pipe.delete(similarity_index_key)
            pipe.execute()
            
            # Clear local embedding cache
            self._embedding_cache.clear()
            
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


# Global cache instance
semantic_cache = SemanticCache()