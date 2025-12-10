"""
STRYDA Missing Context Engine
Detects incomplete queries and generates follow-up questions before providing compliance answers
"""

import re
from typing import Dict, List, Optional, Tuple

# Context requirement patterns and mappings
CONTEXT_PATTERNS = {
    "span_query": {
        "triggers": [
            r'\b(span|how far|max distance|maximum span)\s+(for|of|with)?\s*(140x45|190x45|240x45|90x45|joist|beam|bearer|lintel)\b',
            r'\b(joist|bearer|beam|lintel)\s+span\b',
            r'\bcan\s+i\s+span\b',
        ],
        "required_context": ["timber_grade", "joist_spacing", "use_case"],
        "questions": {
            "timber_grade": "What timber grade are you using (SG8 or SG10)?",
            "joist_spacing": "What spacing (400, 450, or 600 centres)?",
            "use_case": "Is this for a floor or roof?"
        }
    },
    
    "h1_insulation": {
        "triggers": [
            r'\b(r-?value|insulation)\s+(for|in|required|needed)\b.*\b(ceiling|wall|floor|roof)\b',
            r'\bh1\s+(requirement|r-?value)\b',
            r'\bwhat\s+insulation\s+(do i need|required)\b',
        ],
        "required_context": ["climate_zone", "building_type", "element_type"],
        "questions": {
            "climate_zone": "What climate zone (1, 2, or 3)?",
            "building_type": "Is this a new build or a rental upgrade?",
            "element_type": "Ceiling, wall, or floor?"
        }
    },
    
    "underlay_rules": {
        "triggers": [
            r'\b(underlay|sarking|membrane)\s+(for|on|required)\b',
            r'\bwhat\s+underlay\b',
            r'\b(synthetic|permeable|rigid)\s+underlay\b',
        ],
        "required_context": ["wind_zone", "roof_type", "pitch"],
        "questions": {
            "wind_zone": "What wind zone (Low, Medium, High, Very High, or Extra High)?",
            "roof_type": "Metal or tiles?",
            "pitch": "What roof pitch (degrees)?"
        }
    },
    
    "plumbing_compliance": {
        "triggers": [
            r'\b(cylinder|hot water)\s+(temp|temperature|setting)\b',
            r'\bbackflow\s+(preventer|valve)\b',
            r'\bwaste\s+pipe\s+(size|diameter)\b',
            r'\b(trap|gully)\s+(depth|fall)\b',
        ],
        "required_context": ["fixture_type", "location"],
        "questions": {
            "fixture_type": "What fixture (basin, shower, toilet, kitchen sink)?",
            "location": "Inside or outside the building?"
        }
    },
    
    "electrical_compliance": {
        "triggers": [
            r'\b(coc|sdoc|certificate|electrical work)\b',
            r'\bclearance\s+(from|to)\s+(electrical|power|switchboard)\b',
            r'\bwhat\s+size\s+(cable|circuit|breaker)\b',
        ],
        "required_context": ["work_type", "load", "location"],
        "questions": {
            "work_type": "What electrical work (new circuit, replacement, or alteration)?",
            "load": "What load (amps or kW)?",
            "location": "Indoor or outdoor?"
        }
    },
    
    "schedule1_exemptions": {
        "triggers": [
            # Consent questions
            r'\bdo\s+i\s+need\s+(a\s+|an\s+)?(consent|building\s+consent)\b',
            r'\bneed\s+(a\s+|an\s+)?(consent|building\s+consent)\s+(for|to)\b',
            r'\b(is\s+this|is\s+it|is\s+that|is\s+a)\s+(exempt|exemption)\b',
            r'\bexempt\s+building\s+work\b',
            r'\bschedule\s*1\b',
            r'\bcan\s+i\s+build\s+without\s+(a\s+)?consent\b',
        ],
        # Secondary pattern: must also mention small building type
        "building_keywords": [
            r'\b(shed|sleepout|cabin|garage|carport|studio|granny\s+flat)\b',
            r'\b(deck|platform|verandah|veranda|patio)\b',
            r'\bminor\s+dwelling\b',
        ],
        "required_context": ["building_type", "floor_area_m2", "height_or_fall", "storeys", "plumbing_sanitary"],
        "questions": {
            "building_type": "What are you building (shed, sleepout, garage, carport, deck)?",
            "floor_area_m2": "What's the floor area (m²)?",
            "height_or_fall": "What's the max height from ground level or fall height (metres)?",
            "storeys": "Is it single-storey?",
            "plumbing_sanitary": "Are you putting in plumbing (toilet, shower, sink)?"
        }
    },
}


def detect_missing_context(question: str, intent: str) -> Optional[Dict]:
    """
    Detect if question lacks required context for a compliance answer.
    
    Args:
        question: User's question
        intent: Classified intent
    
    Returns:
        {
            "category": str,
            "missing_items": List[str],
            "follow_up_questions": List[str]
        }
        or None if no context is missing
    """
    
    # Only enforce for compliance intents
    if intent not in ["compliance_strict", "implicit_compliance"]:
        return None
    
    q_lower = question.lower()
    
    # Check each pattern category
    for category, config in CONTEXT_PATTERNS.items():
        # Check if question matches any trigger
        for trigger_pattern in config["triggers"]:
            if re.search(trigger_pattern, q_lower):
                # This question needs context - check what's missing
                missing = _check_what_is_missing(question, config["required_context"])
                
                if missing:
                    # Generate follow-up questions
                    follow_ups = [config["questions"][item] for item in missing]
                    
                    return {
                        "category": category,
                        "missing_items": missing,
                        "follow_up_questions": follow_ups
                    }
    
    # No missing context detected
    return None


def _check_what_is_missing(question: str, required_items: List[str]) -> List[str]:
    """
    Check which required context items are missing from the question.
    
    Uses pattern matching to detect if context is already provided.
    """
    q_lower = question.lower()
    missing = []
    
    # Define detection patterns for each context type
    detection_patterns = {
        "timber_grade": r'\b(sg8|sg10|sg6|sg12|structural\s+grade)\b',
        "joist_spacing": r'\b(400|450|600)\s*(mm|centres|center|c\/c|oc)\b',
        "use_case": r'\b(floor|roof|deck)\b',
        "design_load": r'\b(standard|heavy|light|residential|commercial)\s*(load|loading)\b',
        
        "climate_zone": r'\b(zone\s*[123]|climate\s+zone|zone\s+one|zone\s+two|zone\s+three)\b',
        "building_type": r'\b(new\s+build|rental|existing|retrofit)\b',
        "element_type": r'\b(ceiling|wall|floor|roof)\b',
        
        "wind_zone": r'\b(low|medium|high|very\s+high|extra\s+high)\s+(wind|zone)\b',
        "roof_type": r'\b(metal|tile|corrugated|longrun|concrete\s+tile)\b',
        "pitch": r'\b\d+\s*(degree|°|deg)\b',
        
        "fixture_type": r'\b(basin|shower|toilet|kitchen\s+sink|bath|tub)\b',
        "location": r'\b(inside|outside|internal|external|indoor|outdoor)\b',
        
        "work_type": r'\b(new\s+circuit|replacement|alteration|addition)\b',
        "load": r'\b\d+\s*(amp|kw|kilowatt)\b',
        
        "building_type": r'\b(deck|shed|carport|garage|sleepout)\b',
        "size": r'\b\d+\s*(m2|m²|square\s+metre|sqm)\b',
        "height": r'\b\d+(\.\d+)?\s*(m|metre|meter)\s+(high|height)\b',
    }
    
    # Check each required item
    for item in required_items:
        pattern = detection_patterns.get(item)
        if pattern:
            # If pattern NOT found in question, item is missing
            if not re.search(pattern, q_lower):
                missing.append(item)
        else:
            # No detection pattern defined, assume missing
            missing.append(item)
    
    return missing


def generate_missing_context_response(missing_context_info: Dict, user_question: str) -> str:
    """
    Generate a follow-up question asking for missing context.
    
    Uses STRYDA's foreman-style tone: short, direct, no fluff.
    
    Args:
        missing_context_info: Output from detect_missing_context()
        user_question: Original user question
    
    Returns:
        Follow-up question string in STRYDA's tone
    """
    
    follow_ups = missing_context_info["follow_up_questions"]
    category = missing_context_info["category"]
    
    if len(follow_ups) == 1:
        # Single question - keep it ultra-short
        return f"I need more info to give you the right answer. {follow_ups[0]}"
    
    elif len(follow_ups) == 2:
        # Two questions - list them
        return f"I need a couple of details:\n\n- {follow_ups[0]}\n- {follow_ups[1]}"
    
    else:
        # Three+ questions - list them with intro
        intro = "I need a few details to get this right:"
        question_list = "\n".join([f"- {q}" for q in follow_ups])
        return f"{intro}\n\n{question_list}"


def should_ask_for_context(question: str, intent: str) -> Tuple[bool, Optional[Dict]]:
    """
    Main entry point for missing context detection.
    
    Args:
        question: User's question
        intent: Classified intent
    
    Returns:
        (should_ask: bool, context_info: Dict or None)
        
        If should_ask is True, context_info contains:
        {
            "category": str,
            "missing_items": List[str],
            "follow_up_questions": List[str],
            "formatted_response": str
        }
    """
    
    missing_info = detect_missing_context(question, intent)
    
    if missing_info:
        # Generate formatted response
        formatted = generate_missing_context_response(missing_info, question)
        missing_info["formatted_response"] = formatted
        return (True, missing_info)
    
    return (False, None)
