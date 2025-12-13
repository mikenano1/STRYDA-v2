"""
STRYDA GPT-Assisted Context Extraction (Task 2D-4-4)
GPT proposes context values, STRYDA validates and controls storage
"""

import json
import re
from typing import Dict, List, Optional
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_context_via_gpt(
    conversation_summary: Dict,
    recent_messages: List[Dict],
    missing_fields: List[str],
    current_message: str
) -> Dict[str, str]:
    """
    Use GPT to propose context values from natural language.
    GPT output is ADVISORY - STRYDA validates before storing.
    
    Args:
        conversation_summary: Original question, intent, state, etc.
        recent_messages: Last N turns
        missing_fields: Fields still needed
        current_message: Latest user message
    
    Returns:
        Dict of proposed_field → proposed_value (unvalidated)
    """
    
    # Build extraction prompt
    prompt = f"""You are helping extract structured context from a conversation.

ORIGINAL QUESTION: {conversation_summary['original_question']}
INTENT (LOCKED): {conversation_summary['intent_locked']}
STATE: {conversation_summary['state']}

CONTEXT COLLECTED SO FAR:
{json.dumps(conversation_summary.get('context_collected', {}), indent=2)}

STILL MISSING:
{', '.join(missing_fields)}

RECENT CONVERSATION:
{format_recent_messages(recent_messages)}

CURRENT USER MESSAGE: {current_message}

YOUR TASK:
Propose values for ONLY the missing fields based on the user's message.
DO NOT guess or assume.
DO NOT provide advice.
ONLY extract what the user clearly stated.

RESPOND WITH JSON ONLY (no markdown, no explanation):
{{
  "proposed_context": {{
    "field_name": "extracted_value"
  }}
}}

Allowed fields: {', '.join(missing_fields)}
Omit fields if not clearly stated in the message.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean markdown if present
        if result_text.startswith("```"):
            result_text = result_text.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        result = json.loads(result_text)
        proposed = result.get("proposed_context", {})
        
        print(f"   GPT proposed: {list(proposed.keys())}")
        return proposed
        
    except Exception as e:
        print(f"⚠️ GPT extraction failed: {e}")
        return {}


def format_recent_messages(messages: List[Dict]) -> str:
    """Format recent messages for GPT prompt"""
    if not messages:
        return "(no recent messages)"
    
    formatted = []
    for msg in messages[-4:]:  # Last 4 messages max
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:150]  # Truncate long messages
        formatted.append(f"{role.upper()}: {content}")
    
    return "\n".join(formatted)


def validate_proposed_context(proposed: Dict[str, str], missing_fields: List[str]) -> Dict[str, str]:
    """
    Validate GPT-proposed context values.
    STRYDA is the authority - only valid values are stored.
    
    Args:
        proposed: GPT's proposed values
        missing_fields: Fields we're looking for
    
    Returns:
        Dict of validated_field → validated_value
    """
    validated = {}
    
    # Validation rules per field type
    validators = {
        "timber_grade": _validate_timber_grade,
        "joist_spacing": _validate_spacing,
        "use_case": _validate_use_case,
        "climate_zone": _validate_climate_zone,
        "wind_zone": _validate_wind_zone,
        "roof_type": _validate_roof_type,
        "pitch": _validate_pitch,
        "storeys": _validate_storeys,
        "plumbing_sanitary": _validate_plumbing,
        "height_or_fall": _validate_height,
        "floor_area_m2": _validate_floor_area,
        "building_type": _validate_building_type,
    }
    
    for field in missing_fields:
        if field in proposed:
            proposed_value = proposed[field]
            validator = validators.get(field)
            
            if validator:
                validated_value = validator(proposed_value)
                if validated_value:
                    validated[field] = validated_value
                    print(f"      ✅ {field}: {validated_value}")
                else:
                    print(f"      ❌ {field}: '{proposed_value}' invalid")
            else:
                # No validator defined, accept as-is (risky, log warning)
                print(f"      ⚠️ {field}: no validator, accepting '{proposed_value}'")
                validated[field] = proposed_value
    
    return validated


# Validation functions
def _validate_timber_grade(value: str) -> Optional[str]:
    """Validate timber grade"""
    val_upper = value.upper().strip()
    if val_upper in ["SG8", "SG10", "SG6", "SG12"]:
        return val_upper
    return None

def _validate_spacing(value: str) -> Optional[str]:
    """Validate joist spacing"""
    # Extract number
    match = re.search(r'(\d+)', value)
    if match:
        spacing = int(match.group(1))
        if spacing in [400, 450, 600]:
            return f"{spacing}mm centres"
    return None

def _validate_use_case(value: str) -> Optional[str]:
    """Validate floor/roof/deck"""
    val_lower = value.lower().strip()
    if val_lower in ["floor", "roof", "deck"]:
        return val_lower
    return None

def _validate_climate_zone(value: str) -> Optional[str]:
    """Validate climate zone"""
    # Extract zone number
    match = re.search(r'([123])', value)
    if match:
        return f"zone {match.group(1)}"
    return None

def _validate_wind_zone(value: str) -> Optional[str]:
    """Validate wind zone"""
    val_lower = value.lower().strip()
    valid_zones = ["low", "medium", "high", "very high", "extra high"]
    if val_lower in valid_zones:
        return val_lower
    return None

def _validate_roof_type(value: str) -> Optional[str]:
    """Validate roof type"""
    val_lower = value.lower().strip()
    if any(t in val_lower for t in ["metal", "tile", "corrugated", "longrun"]):
        return val_lower
    return None

def _validate_pitch(value: str) -> Optional[str]:
    """Validate roof pitch"""
    # Extract numeric degrees
    match = re.search(r'(\d+)', value)
    if match:
        degrees = int(match.group(1))
        if 3 <= degrees <= 60:  # Reasonable pitch range
            return f"{degrees}°"
    return None

def _validate_storeys(value: str) -> Optional[str]:
    """Validate storeys - FLEXIBLE for natural language"""
    val_lower = value.lower().strip()
    
    # Accept variations
    if any(term in val_lower for term in ["single", "one", "1"]):
        return "single-storey"
    elif any(term in val_lower for term in ["two", "2", "double"]):
        return "two-storey"
    elif any(term in val_lower for term in ["multi", "three", "3"]):
        return "multi-storey"
    
    return None

def _validate_plumbing(value: str) -> Optional[str]:
    """Validate plumbing/sanitary - FLEXIBLE"""
    val_lower = value.lower().strip()
    
    # Check for explicit no
    if any(term in val_lower for term in ["no", "none", "without"]):
        return "none"
    
    # Check for yes/has plumbing
    if any(term in val_lower for term in ["yes", "toilet", "shower", "sink", "basin", "plumbing", "sanitary"]):
        return "has sanitary"
    
    return None

def _validate_height(value: str) -> Optional[str]:
    """Validate height in metres"""
    # Extract numeric + unit
    match = re.search(r'(\d+(?:\.\d+)?)\s*m', value.lower())
    if match:
        height = float(match.group(1))
        if 0.5 <= height <= 20:  # Reasonable building height
            return f"{height}m"
    return None

def _validate_floor_area(value: str) -> Optional[str]:
    """Validate floor area in m²"""
    # Extract numeric
    match = re.search(r'(\d+)', value)
    if match:
        area = int(match.group(1))
        if 1 <= area <= 1000:  # Reasonable range
            return f"{area}m²"
    return None

def _validate_building_type(value: str) -> Optional[str]:
    """Validate building type"""
    val_lower = value.lower().strip()
    valid_types = ["shed", "sleepout", "garage", "carport", "deck", "cabin", "studio", "verandah"]
    
    for building_type in valid_types:
        if building_type in val_lower:
            return building_type
    
    return None
