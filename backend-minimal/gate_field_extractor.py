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
    
    # Extract underlay_system
    if "underlay_system" in required_fields:
        if re.search(r'\bself[- ]?supporting\b', msg_lower):
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
        if re.search(r'\broll\s+direction\b', msg_lower):
            extracted["clarify_direction"] = "roll_direction"
        elif re.search(r'\blap\s+direction\b', msg_lower):
            extracted["clarify_direction"] = "lap_direction"
    
    # Extract roof_pitch_deg
    if "roof_pitch_deg" in required_fields:
        # Match patterns like "3 degrees", "5°", "7.5 deg"
        pitch_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:degree|°|deg)', msg_lower)
        if pitch_match:
            extracted["roof_pitch_deg"] = float(pitch_match.group(1))
    
    return extracted
