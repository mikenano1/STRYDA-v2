"""
STRYDA Conversational Intent Router
Classifies user intents and routes appropriately
"""

import os
import re
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

class IntentRouter:
    """Lightweight intent classification for conversational flow"""
    
    @staticmethod
    def classify_intent(message: str, conversation_history: List[Dict] = None) -> str:
        """
        Classify user intent using heuristics + context
        Returns: chitchat, clarify, general_building, compliance_strict, unknown
        """
        message_lower = message.lower().strip()
        
        # Chitchat patterns
        chitchat_patterns = [
            r'\b(hi|hello|hey|ping|test|thanks?|thank you|bye|goodbye)\b',
            r'^(how are you|what\'s up|testing|test 123)$',
            r'\b(good|great|awesome|cool|nice)\b.*\b(work|job|thanks?)\b',
        ]
        
        if any(re.search(pattern, message_lower) for pattern in chitchat_patterns):
            return "chitchat"
        
        # Clarifying question patterns (vague, educational)
        clarify_patterns = [
            r'\b(new to|beginner|getting started|don\'t know|help me understand)\b',
            r'\b(what should i know|where do i start|basics|overview)\b',
            r'\b(first time|never done|not sure)\b',
            r'^(what|how|why)(?! is| are| do).*\?$',  # Open questions without specifics
        ]
        
        if any(re.search(pattern, message_lower) for pattern in clarify_patterns):
            return "clarify"
        
        # Compliance strict patterns (specific codes, measurements, standards)
        compliance_patterns = [
            r'\b(nzbc|clause [a-h]\d+|[a-h]\d+/[a-z]+\d+)\b',  # NZBC Clause E2, B1/AS1
            r'\b(as/nzs \d+|nzs \d+|iso \d+|astm [a-z]\d+)\b',  # Standards
            r'\b\d+\s*(mm|kpa|kn|m\^?2|degrees?)\b',  # Measurements  
            r'\b(wind zone|very high wind|ultimate limit state)\b',  # Specific technical terms
            r'\b(minimum|maximum|shall|must|requirement)\b.*\b(cover|clearance|spacing)\b',
        ]
        
        if any(re.search(pattern, message_lower) for pattern in compliance_patterns):
            return "compliance_strict"
        
        # Check for building/construction content
        building_terms = [
            'flashing', 'roofing', 'building', 'construction', 'fastener', 
            'installation', 'weatherproof', 'insulation', 'ventilation',
            'structure', 'foundation', 'cladding', 'membrane'
        ]
        
        if any(term in message_lower for term in building_terms):
            return "general_building"
        
        return "unknown"
    
    @staticmethod
    def get_retrieval_params(intent: str) -> Dict:
        """Get retrieval parameters based on intent"""
        params = {
            "chitchat": {"do_retrieval": False, "top_k": 0, "citation_threshold": 1.0},
            "clarify": {"do_retrieval": False, "top_k": 2, "citation_threshold": 0.90},
            "general_building": {"do_retrieval": True, "top_k": 4, "citation_threshold": 0.82},
            "compliance_strict": {"do_retrieval": True, "top_k": 3, "citation_threshold": 0.70},
            "unknown": {"do_retrieval": True, "top_k": 4, "citation_threshold": 0.85},
        }
        
        return params.get(intent, params["unknown"])
    
    @staticmethod
    def get_system_prompt(intent: str) -> str:
        """Get appropriate system prompt for intent"""
        base_prompt = """You are STRYDA, a helpful NZ building copilot. Speak naturally, brief and clear.
Use citations ONLY when you relied on a specific document passage. If the user is greeting/testing, reply warmly with no citations.
If the question is broad, summarise the essentials and offer to cite if they want the exact clause.
Always prefer NZ context and plain English. Ask one smart clarifying question if the request is ambiguous."""
        
        intent_specific = {
            "chitchat": base_prompt + "\n\nThis is a casual interaction. Be friendly and conversational. No technical citations needed.",
            "clarify": base_prompt + "\n\nThe user needs guidance. Ask 1-2 clarifying questions to help them get specific information.",
            "general_building": base_prompt + "\n\nProvide helpful building guidance. Use citations if you reference specific requirements.",
            "compliance_strict": base_prompt + "\n\nThis is a compliance question. Be precise and always cite the specific sources you use.",
            "unknown": base_prompt + "\n\nDetermine what the user needs and provide helpful guidance."
        }
        
        return intent_specific.get(intent, base_prompt)

# Export for use in main app
intent_router = IntentRouter()