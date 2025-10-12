"""
STRYDA v1.3.3-hotfix4 - Bulletproof Type Safety
Comprehensive Decimal elimination and type conversion
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Union
import json

def bulletproof_float(value: Any) -> float:
    """
    Bulletproof conversion to float - handles ALL edge cases
    """
    if value is None:
        return 0.0
    
    # Handle standard numeric types
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, Decimal):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value)
        except (ValueError, TypeError):
            return 0.0
    else:
        try:
            result = float(str(value))
        except (ValueError, TypeError):
            return 0.0
    
    # Guard against NaN/infinity
    if result != result or result == float('inf') or result == float('-inf'):
        return 0.0
    
    return result

def safe_hybrid_scoring(vector_score: Any, keyword_score: Any, source_boost: Any) -> float:
    """
    Safe hybrid scoring with comprehensive error handling
    """
    try:
        # Convert all inputs to safe floats
        v = bulletproof_float(vector_score)
        k = bulletproof_float(keyword_score)
        b = bulletproof_float(source_boost)
        
        # Additional range validation
        v = max(0.0, min(1.0, v))
        k = max(0.0, min(1.0, k))
        b = max(0.0, min(1.0, b))
        
        # Safe computation
        score = (0.7 * v) + (0.2 * k) + (0.1 * b)
        
        # Final validation
        score = max(0.0, min(1.0, score))
        
        return score
        
    except Exception as e:
        print(f"⚠️ Scoring calculation error: {e}, using fallback")
        return 0.5

def sanitize_result_for_json(result: dict) -> dict:
    """Sanitize result dictionary for JSON serialization"""
    sanitized = dict(result)
    
    # Convert all numeric fields to safe floats
    numeric_fields = ['vector_score', 'keyword_score', 'source_boost', 'score_final', 'score', 'fts_score']
    
    for field in numeric_fields:
        if field in sanitized:
            sanitized[field] = bulletproof_float(sanitized[field])
    
    # Ensure required fields exist
    sanitized['score'] = sanitized.get('score_final', sanitized.get('score', 0.0))
    
    return sanitized

def test_type_safety():
    """Test type safety functions"""
    print("🧪 Testing type safety functions...")
    
    # Test various problematic types
    test_cases = [
        Decimal('0.85'),
        0.85,
        '0.85',
        None,
        float('inf'),
        float('nan')
    ]
    
    for test_val in test_cases:
        result = bulletproof_float(test_val)
        print(f"   {type(test_val).__name__}({test_val}) → {result}")
    
    # Test hybrid scoring
    score = safe_hybrid_scoring(Decimal('0.8'), 0.6, 0.1)
    print(f"   Hybrid scoring test: {score}")
    
    print("✅ Type safety tests completed")

if __name__ == "__main__":
    test_type_safety()