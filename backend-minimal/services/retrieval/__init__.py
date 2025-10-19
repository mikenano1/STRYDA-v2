"""
Canonical retrieval export for all callers (chat, selftest, tools).
This prevents drift between implementations.
"""

try:
    # Import the working implementation
    import sys
    import os
    
    # Add backend-minimal to path for imports
    sys.path.insert(0, '/app/backend-minimal')
    
    from simple_tier1_retrieval import tier1_content_search
    
    # Canonical function that all systems use
    def tier1_retrieval(query: str, top_k: int = 6, **kwargs):
        """
        Canonical Tier-1 retrieval used by chat, selftest, and all other systems
        Ensures consistency across all callers
        """
        return tier1_content_search(query, top_k)
    
except ImportError as e:
    # Fallback implementation
    print(f"⚠️ Primary retrieval import failed: {e}")
    
    def tier1_retrieval(query: str, top_k: int = 6, **kwargs):
        """Fallback retrieval implementation"""
        return []

# Export the canonical function
__all__ = ['tier1_retrieval']