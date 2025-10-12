"""
STRYDA v1.3.3 Performance Profiler
Precise phase timing for latency optimization
"""

import time
from typing import Dict, Any, List
from contextlib import contextmanager

class STRYDAProfiler:
    """Precise phase timing for RAG pipeline optimization"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all timers for new request"""
        self.timers = {
            't_parse': 0,
            't_embed_query': 0, 
            't_vector_search': 0,
            't_hybrid_keyword': 0,
            't_merge_relevance': 0,
            't_generate': 0,
            't_total': 0
        }
        self.start_time = None
        
    @contextmanager
    def timer(self, phase: str):
        """Context manager for precise phase timing"""
        start = time.time()
        try:
            yield
        finally:
            duration = (time.time() - start) * 1000  # Convert to ms
            self.timers[phase] = duration
    
    def start_request(self):
        """Start total request timing"""
        self.start_time = time.time()
    
    def finish_request(self):
        """Finish total request timing"""
        if self.start_time:
            self.timers['t_total'] = (time.time() - self.start_time) * 1000
    
    def get_breakdown(self) -> Dict[str, float]:
        """Get timing breakdown"""
        return {k: round(v) for k, v in self.timers.items()}
    
    def get_telemetry(self, intent: str, confidence: float, citations_count: int, 
                     cache_hit: bool, top_sources: List[str]) -> Dict[str, Any]:
        """Generate complete telemetry payload"""
        return {
            'intent': intent,
            'confidence': round(confidence, 2),
            'citations_count': citations_count,
            'cache_hit': cache_hit,
            'top_sources': top_sources[:3],  # Top 3 sources
            'timing_breakdown': self.get_breakdown()
        }

# Global profiler instance
profiler = STRYDAProfiler()