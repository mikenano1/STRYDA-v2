"""
Canonical retrieval export for all callers (chat, selftest, tools).
This prevents drift between implementations.
"""

import sys
import os

# Add backend-minimal to path for imports
sys.path.insert(0, '/app/backend-minimal')

try:
    # Import the actual working function (correct name)
    from simple_tier1_retrieval import simple_tier1_retrieval
    
    # Canonical function that all systems use
    def tier1_retrieval(query: str, top_k: int = 6, intent: str = "compliance_strict", **kwargs):
        """
        Canonical Tier-1 retrieval used by chat, selftest, and all other systems
        Ensures consistency across all callers
        Passes intent through for metadata-aware ranking
        """
        return simple_tier1_retrieval(query, top_k, intent=intent)
    
    # Also export with the expected name for compatibility
    tier1_content_search = tier1_retrieval
    
except ImportError as e:
    # Fallback implementation
    print(f"⚠️ Primary retrieval import failed: {e}")
    
    def tier1_retrieval(query: str, top_k: int = 6, **kwargs):
        """Fallback retrieval implementation"""
        return []
    
    tier1_content_search = tier1_retrieval

# Export both names for compatibility
__all__ = ['tier1_retrieval', 'tier1_content_search']