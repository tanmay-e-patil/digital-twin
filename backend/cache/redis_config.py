"""
Redis Configuration Module

This module handles Redis connection management with connection pooling,
retry logic, and configuration management for the semantic cache.
"""

import os
import redis
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RedisConfig:
    """Manages Redis connection configuration and pooling for the semantic cache."""
    
    def __init__(self):
        """Initialize Redis configuration from environment variables."""
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.password = os.getenv("REDIS_PASSWORD")
        self.db = int(os.getenv("REDIS_DB", 0))
        self.connection_pool = None
        self.client = None
        self._connected = False
    
    def connect(self) -> bool:
        """
        Initialize Redis connection with connection pooling.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection pool with optimized settings
            self.connection_pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                max_connections=20,  # Maximum number of connections in pool
                retry_on_timeout=True,  # Retry on timeout
                socket_keepalive=True,  # Enable TCP keepalive
                socket_keepalive_options={},  # Use OS defaults for keepalive
                socket_connect_timeout=5,  # Connection timeout
                socket_timeout=5,  # Read/write timeout
                health_check_interval=30,  # Check connection health every 30 seconds
            )
            
            # Create Redis client from connection pool
            self.client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection with ping
            self.client.ping()
            self._connected = True
            
            logger.info(f"Connected to Redis at {self.host}:{self.port}, db={self.db}")
            return True
            
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            self._connected = False
            return False
        except redis.AuthenticationError as e:
            logger.error(f"Redis authentication error: {e}")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self._connected = False
            return False
    
    def get_client(self) -> Optional[redis.Redis]:
        """
        Get Redis client, connecting if necessary.
        
        Returns:
            redis.Redis: Redis client instance or None if connection fails
        """
        if not self._connected or self.client is None:
            if not self.connect():
                return None
        return self.client
    
    def disconnect(self):
        """Close Redis connections and cleanup resources."""
        try:
            if self.connection_pool:
                self.connection_pool.disconnect()
                self.connection_pool = None
            self.client = None
            self._connected = False
            logger.info("Disconnected from Redis")
        except Exception as e:
            logger.warning(f"Error disconnecting from Redis: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if Redis is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self._connected or self.client is None:
            return False
        
        try:
            # Quick ping to verify connection
            self.client.ping()
            return True
        except:
            self._connected = False
            return False
    
    def get_connection_info(self) -> dict:
        """
        Get Redis connection information.
        
        Returns:
            dict: Connection information
        """
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "connected": self.is_connected(),
            "has_password": bool(self.password)
        }


# Global Redis configuration instance
redis_config = RedisConfig()