"""
Simple in-memory LRU cache for STRYDA-v2
Caches query embeddings and chat responses to reduce latency
"""

import time
import hashlib
from collections import OrderedDict
from typing import Optional, Any, Dict

class LRUCache:
    """Least Recently Used cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.timestamps = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired"""
        if key in self.cache:
            # Check if expired
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                del self.cache[key]
                del self.timestamps[key]
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            self.timestamps[key] = time.time()
            
            # Evict oldest if over max_size
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 1),
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds
        }

# Global caches
embedding_cache = LRUCache(max_size=500, ttl_seconds=3600)  # 1 hour TTL for embeddings
response_cache = LRUCache(max_size=200, ttl_seconds=1800)  # 30 min TTL for responses

def cache_key(text: str) -> str:
    """Generate cache key from text using MD5 hash"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]

def get_cache_stats() -> Dict[str, Dict]:
    """Get statistics for all caches"""
    return {
        "embedding_cache": embedding_cache.stats(),
        "response_cache": response_cache.stats()
    }

# Export for use in other modules
__all__ = ['embedding_cache', 'response_cache', 'cache_key', 'get_cache_stats']
