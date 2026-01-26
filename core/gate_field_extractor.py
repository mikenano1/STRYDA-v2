"""
Gate Field Extractor
Extracts required fields from user follow-up messages for gated questions
"""

import re
from typing import Dict

def extract_gate_fields(message: str, required_fields: list) -> Dict[str, str]:
    """
    Extract required fields from user's follow-up message.
    
    Args:
        message: User's follow-up message
        required_fields: List of fields to extract
    
    Returns:
        Dict of field_name → extracted_value (only validated fields)
    """
    msg_lower = message.lower()
    extracted = {}
    
    # Extract roof_profile
    if "roof_profile" in required_fields:
        if re.search(r'\bcorrugate', msg_lower):
            extracted["roof_profile"] = "corrugate"
        elif re.search(r'\b5[-\s]?rib\b', msg_lower):
            extracted["roof_profile"] = "5-rib"
        elif re.search(r'\btray\b', msg_lower):
            extracted["roof_profile"] = "tray"
        elif re.search(r'\blongrun\b', msg_lower):
            extracted["roof_profile"] = "longrun"
    
    # Extract underlay_system (brand/model recognition)
    if "underlay_system" in required_fields:
        if re.search(r'\bru\s?24\b', msg_lower):
            extracted["underlay_system"] = "RU24"
        elif re.search(r'\bdristud\b', msg_lower):
            extracted["underlay_system"] = "Dristud"
        elif re.search(r'\bthermakraft\b', msg_lower):
            extracted["underlay_system"] = "Thermakraft"
        elif re.search(r'\bself[- ]?supporting\b', msg_lower):
            extracted["underlay_system"] = "self-supporting"
        elif re.search(r'\bsynthetic\b', msg_lower):
            extracted["underlay_system"] = "synthetic"
        elif re.search(r'\bpermeable\b', msg_lower):
            extracted["underlay_system"] = "permeable"
        elif re.search(r'\brigid\b', msg_lower):
            extracted["underlay_system"] = "rigid"
        elif re.search(r'\bsarking\b', msg_lower):
            extracted["underlay_system"] = "sarking"
    
    # Extract clarify_direction
    if "clarify_direction" in required_fields:
        if re.search(r'\broll\s+direction\b', msg_lower) or re.search(r'\broll\b', msg_lower):
            extracted["clarify_direction"] = "roll_direction"
        elif re.search(r'\blap\s+direction\b', msg_lower) or re.search(r'\blap\b', msg_lower):
            extracted["clarify_direction"] = "lap_direction"
    
    # DO NOT extract roof_pitch_deg for underlay_changeover_pitch gate
    # Pitch is the OUTPUT, not an input!
    
    return extracted
