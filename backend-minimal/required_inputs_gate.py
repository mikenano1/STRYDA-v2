"""
STRYDA Required-Inputs Gate
Blocks threshold/changeover questions until key inputs are provided
Prevents guessing numeric thresholds
"""

import re
from typing import Dict, List, Optional

def gate_required_inputs(question: str) -> Dict:
    """
    Check if question asks for threshold/changeover and needs inputs before answering.
    
    Args:
        question: User's question
    
    Returns:
        {
            "should_gate": bool,
            "reason": str,
            "ask": str,
            "required_fields": List[str]
        }
    """
    
    q_lower = question.lower()
    
    # THRESHOLD/CHANGEOVER TRIGGERS
    threshold_patterns = [
        r'\bwhat\s+pitch\b',
        r'\bwhat\s+angle\b',
        r'\bat\s+what\s+pitch\b',
        r'\bwhen\s+do\s+i\s+change\b',
        r'\bchange\s+from\b.*(vertical|horizontal)',
        r'\bminimum\s+pitch\b',
        r'\bmaximum\s+pitch\b',
        r'\brequired\s+pitch\b',
        r'\bpitch\s+(roof\s+)?requires?\b',
    ]
    
    # Check if question matches threshold pattern
    is_threshold_question = any(re.search(p, q_lower) for p in threshold_patterns)
    
    if not is_threshold_question:
        return {
            "should_gate": False,
            "reason": "not_threshold",
            "ask": "",
            "required_fields": []
        }
    
    # Check if roof/underlay context
    is_roof_underlay = any(term in q_lower for term in ['roof', 'underlay', 'sarking', 'membrane', 'corrugate', 'iron', 'tray', 'profile', 'cladding'])
    
    if not is_roof_underlay:
        # Other threshold questions might be fine (not roofing)
        return {
            "should_gate": False,
            "reason": "not_roof_underlay",
            "ask": "",
            "required_fields": []
        }
    
    # ROOF/UNDERLAY THRESHOLD QUESTION - gate it!
    
    # Check what inputs are already provided
    provided_fields = []
    
    # Check for roof profile
    if any(term in q_lower for term in ['corrugate', '5-rib', '5 rib', '5rib', 'tray', 'longrun', 'metal', 'tile']):
        provided_fields.append('roof_profile')
    
    # Check for underlay system (brand/model)
    if any(term in q_lower for term in ['ru24', 'ru 24', 'dristud', 'thermakraft', 'synthetic', 'permeable', 'rigid', 'self supporting', 'self-supporting']):
        provided_fields.append('underlay_system')
    
    # Check for direction clarification
    if 'roll' in q_lower or 'lap' in q_lower:
        provided_fields.append('clarify_direction')
    
    # Required fields for underlay changeover threshold (FIXED: removed roof_pitch_deg - that's the OUTPUT!)
    required_fields = ['roof_profile', 'underlay_system', 'clarify_direction']
    
    # Check if all required fields are provided
    missing_fields = [f for f in required_fields if f not in provided_fields]
    
    if not missing_fields:
        # All inputs provided, allow answering
        return {
            "is_gated": False,
            "reason": "inputs_complete",
            "prompt": "",
            "required_fields": [],
            "question_key": ""
        }
    
    # GATE: Missing inputs, ask for them (natural wording, no "Quick ones")
    ask_message = "Before I answer properly: what roof profile is it (corrugate / 5-rib / tray), what underlay (brand/model), and do you mean roll direction or lap direction?"
    
    return {
        "is_gated": True,
        "reason": "threshold_changeover",
        "prompt": ask_message,
        "required_fields": missing_fields,
        "question_key": "underlay_changeover_pitch"
    }
