"""
LLM Parameter Guard - Prevents legacy parameter mismatches
Ensures GPT-5/o1 models only use supported parameters
"""

import os
from typing import Dict, Any


def reject_legacy_max_tokens(kwargs: Dict[str, Any]) -> None:
    """
    Reject legacy 'max_tokens' parameter.
    GPT-5/o1 require 'max_completion_tokens' instead.
    
    Raises:
        ValueError: If 'max_tokens' is present in kwargs
    """
    if "max_tokens" in kwargs:
        raise ValueError(
            "Legacy parameter 'max_tokens' not allowed. "
            "Use 'max_completion_tokens' for GPT-5/o1 models."
        )


def sanitize_params_for_model(model: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize parameters based on model type.
    
    GPT-5/o1 reasoning models support:
        - max_completion_tokens
        - (no temperature, top_p, presence_penalty, frequency_penalty)
    
    Standard models support:
        - max_tokens
        - temperature, top_p, presence_penalty, frequency_penalty
    
    Args:
        model: Model name (e.g., "gpt-5", "gpt-4o-mini")
        params: Raw parameters dict
    
    Returns:
        Sanitized parameters dict appropriate for model
    """
    sanitized = params.copy()
    
    # Detect reasoning models
    is_reasoning_model = (
        "gpt-5" in model.lower() or 
        "o1" in model.lower()
    )
    
    if is_reasoning_model:
        # GPT-5/o1: Strip unsupported parameters
        unsupported = ["temperature", "top_p", "presence_penalty", "frequency_penalty", "max_tokens"]
        for key in unsupported:
            if key in sanitized:
                del sanitized[key]
                print(f"⚙️  Stripped unsupported param '{key}' for {model}")
        
        # Ensure max_completion_tokens is used
        if "max_completion_tokens" not in sanitized:
            sanitized["max_completion_tokens"] = 600
            print(f"⚙️  Added max_completion_tokens=600 for {model}")
    
    else:
        # Standard models: Ensure max_tokens (not max_completion_tokens)
        if "max_completion_tokens" in sanitized:
            # Convert to max_tokens for standard models
            sanitized["max_tokens"] = sanitized.pop("max_completion_tokens")
            print(f"⚙️  Converted max_completion_tokens → max_tokens for {model}")
        
        if "max_tokens" not in sanitized:
            sanitized["max_tokens"] = 600
    
    return sanitized


def validate_model_params(model: str, params: Dict[str, Any]) -> None:
    """
    Validate that parameters are appropriate for the model.
    
    Raises:
        ValueError: If invalid parameter combination detected
    """
    is_reasoning_model = "gpt-5" in model.lower() or "o1" in model.lower()
    
    if is_reasoning_model:
        # Check for disallowed parameters
        disallowed = ["max_tokens", "temperature", "top_p", "presence_penalty", "frequency_penalty"]
        found = [k for k in disallowed if k in params]
        if found:
            raise ValueError(
                f"GPT-5/o1 models do not support: {', '.join(found)}. "
                f"Use max_completion_tokens only."
            )
        
        # Ensure max_completion_tokens is present
        if "max_completion_tokens" not in params:
            raise ValueError("GPT-5/o1 models require 'max_completion_tokens' parameter.")
    
    else:
        # Standard models need max_tokens
        if "max_tokens" not in params and "max_completion_tokens" not in params:
            raise ValueError("Standard models require 'max_tokens' parameter.")


def get_safe_model_params(model: str, max_length: int = 600) -> Dict[str, Any]:
    """
    Get safe default parameters for a model.
    
    Args:
        model: Model name
        max_length: Maximum token length for response
    
    Returns:
        Safe parameter dict for the model
    """
    is_reasoning_model = "gpt-5" in model.lower() or "o1" in model.lower()
    
    if is_reasoning_model:
        return {
            "max_completion_tokens": max_length
            # No temperature, top_p, etc. for GPT-5/o1
        }
    else:
        return {
            "max_tokens": max_length,
            "temperature": 0.3
        }
