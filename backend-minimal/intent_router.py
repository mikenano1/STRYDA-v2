"""
STRYDA Conversational Intent Router v1.2
Enhanced conversational flow with answer_style routing
"""

import os
import re
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

class IntentRouter:
    """Enhanced intent classification for natural conversation flow"""
    
    @staticmethod
    def classify_intent_and_confidence(message: str, conversation_history: List[Dict] = None) -> Tuple[str, float, str]:
        """
        Enhanced classification to avoid code-dump replies on short queries
        Returns: (intent, confidence, answer_style)
        """
        message_lower = message.lower().strip()
        
        # Chitchat patterns (high confidence) - expanded
        chitchat_patterns = [
            r'\b(hi|hello|hey|ping|test|thanks?|thank you|bye|goodbye|good morning|good day)\b',
            r'^(how are you|what\'s up|testing|all good|cheers)$',
            r'\b(cool|nice|great|awesome|perfect|sweet|thanks)\b$',
            r'^(kia ora|gday|morning)$',
        ]
        
        for pattern in chitchat_patterns:
            if re.search(pattern, message_lower):
                return "chitchat", 0.95, "friendly"
        
        # Compliance/Pinpoint patterns (high confidence) 
        compliance_patterns = [
            r'\b(nzbc clause|clause [a-h]\d+|[a-h]\d+/[a-z]+\d+)\b',
            r'\b(as/nzs \d+|nzs \d+|iso \d+|astm [a-z]\d+)\b',
            r'\b(minimum|maximum|exact|specific).*(cover|clearance|spacing|distance)\b',
            r'\b\d+\s*(mm|kpa|kn|m\^?2|degrees?)\b',
            r'\b(wind zone [vh]+|ultimate limit state|characteristic load)\b',
        ]
        
        for pattern in compliance_patterns:
            if re.search(pattern, message_lower):
                return "compliance_strict", 0.85, "precise_citation"
        
        # How-to patterns (medium confidence) - avoid short queries becoming code dumps
        how_to_patterns = [
            r'\b(how to|how do i|step by step|best way to|process for)\b',
            r'\b(install|fix|repair|maintain|check|inspect)\b.*\b(roof|flashing|gutter)\b',
            r'(where do i start|new to|beginner|getting started)',
        ]
        
        building_terms = ['flashing', 'roofing', 'stud', 'nog', 'joist', 'rafter', 'membrane', 'underlay', 'fastener', 'cladding', 'gutter']
        has_building_content = any(term in message_lower for term in building_terms)
        
        # Prevent short queries from getting complex responses
        if len(message.split()) <= 3 and not any(re.search(pattern, message_lower) for pattern in compliance_patterns):
            return "clarify", 0.60, "educational"
        
        if has_building_content:
            for pattern in how_to_patterns:
                if re.search(pattern, message_lower):
                    return "general_advice", 0.75, "practical_guidance"
        
        # Clarifying patterns
        clarify_patterns = [
            r'\b(help|advice|guidance|suggestions?)\b$',
            r'^(what|where|why|which).*\?$',
            r'\b(not sure|unsure|confused|unclear)\b',
        ]
        
        for pattern in clarify_patterns:
            if re.search(pattern, message_lower):
                return "clarify", 0.65, "educational"
        
        # General building (lower confidence to avoid over-complexity)
        if has_building_content:
            return "general_building", 0.55, "practical_guidance"
        
        return "clarify", 0.35, "clarify_first"
    
    @staticmethod
    def get_retrieval_params(intent: str, answer_style: str) -> Dict:
        """Get retrieval parameters based on intent and answer style"""
        params = {
            "chitchat": {"do_retrieval": False, "top_k": 0, "show_citations": False},
            "clarify": {"do_retrieval": False, "top_k": 2, "show_citations": False},
            "general_advice": {"do_retrieval": True, "top_k": 4, "show_citations": False, "sources_button": True},
            "general_building": {"do_retrieval": True, "top_k": 4, "show_citations": False, "sources_button": True},
            "compliance_strict": {"do_retrieval": True, "top_k": 3, "show_citations": True},
            "unknown": {"do_retrieval": True, "top_k": 2, "show_citations": False},
        }
        
        return params.get(intent, params["unknown"])
    
    @staticmethod
    def get_system_prompt(intent: str, answer_style: str) -> str:
        """Get system prompt with few-shot exemplars for natural conversation"""
        
        exemplars = """
EXEMPLARS - Follow these response patterns:

1) Chitchat (no citations)
User: "Hi, how are you?"
Intent: chitchat
Assistant: "Kia ora, I'm running well and ready to help with building or code questions. What's on your mind?"

2) How-to (plain language, stepwise, no citations)
User: "How do I fix a leaking gutter?"
Intent: how_to
Assistant: "Here's a quick plan:
1) Clear leaves and muck.
2) Check joints for gaps or loose screws.
3) Seal hairline gaps with gutter sealant.
4) Reseat and re-screw loose joints.
5) Replace badly rusted sections.
Tip: If leaks return after rain, the fall may be wrong and you'll need to re-hang a section."

3) How-to (jobsite, underlay install, no citations)
User: "How do I install roofing underlay?"
Intent: how_to
Assistant: "Run it horizontally from eaves, 150 mm overlaps, fix to rafters/purlins without sag. Tape penetrations, and don't leave it exposed more than a few days before cladding."

4) Compliance (precise + citations ≤3)
User: "What is the minimum cover for apron flashing?"
Intent: compliance
Assistant: "Minimum apron flashing cover is 150 mm in standard conditions."
[Citations: NZ Metal Roofing Code of Practice, p.231]

5) Compliance follow-up (context carry)
User: "What about in very high wind zones?"
Intent: compliance
Assistant: "Maintain at least 150 mm cover and add additional fixings to resist uplift. Some profiles may require increased laps per COP guidance."
[Citations: NZ Metal Roofing Code of Practice, p.231]

6) Clarify (vague request)
User: "Do I need a permit?"
Intent: clarify
Assistant: "Do you mean a council building consent or a site safety permit? What work are you doing (e.g., reroof, new deck, internal wall change)? Two examples that help me answer quickly:
• 'Reroofing Colorsteel over existing purlins in a high-wind zone.'
• 'New internal load-bearing wall in a single-storey dwelling.'"

7) Chitchat (light, on-topic)
User: "Are you smarter than a builder?"
Intent: chitchat
Assistant: "I'm fast with the paperwork; the builder's the pro with tools. Think of me as your code sidekick."

8) Compliance (NZBC clause overview + cite)
User: "Explain NZBC clause E2."
Intent: compliance
Assistant: "E2 covers external moisture—keeping water out of the building. Acceptable Solution E2/AS1 includes roof pitches, flashings, and cladding details."
[Citations: NZBC E2/AS1, p.15]
"""
        
        base_prompt = f"""You are STRYDA, a practical NZ building assistant. Give trade-friendly answers following these patterns:

{exemplars}

RULES:
- For how_to: Be practical and stepwise. NO citations unless confidence < 0.65 OR user asks "source?"
- For compliance: Be precise. ALWAYS include ≤3 citations with snippets ≤200 chars
- For chitchat: Be friendly and brief. NO citations
- For clarify: Ask 1-2 targeted questions with concrete examples

Follow NZ context and plain English. Be helpful like an experienced foreman explaining to a tradesperson."""
        
        return base_prompt
    
    @staticmethod
    def should_ask_clarifying_question(intent: str, confidence: float) -> bool:
        """Determine if we should ask for clarification"""
        return confidence < 0.55 or intent == "unknown"

# Export for use in main app
intent_router = IntentRouter()