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
        Enhanced classification with confidence and answer_style
        Returns: (intent, confidence, answer_style)
        """
        message_lower = message.lower().strip()
        
        # Chitchat patterns (high confidence)
        chitchat_patterns = [
            r'\b(hi|hello|hey|ping|test|thanks?|thank you|bye|goodbye)\b',
            r'^(how are you|what\'s up|testing|good morning|good day)$',
            r'\b(cool|nice|great|awesome|perfect|thanks)\b',
        ]
        
        for pattern in chitchat_patterns:
            if re.search(pattern, message_lower):
                return "chitchat", 0.95, "friendly"
        
        # Compliance/Pinpoint patterns (high confidence)
        compliance_patterns = [
            r'\b(nzbc clause|clause [a-h]\d+|[a-h]\d+/[a-z]+\d+)\b',  # Explicit clauses
            r'\b(as/nzs \d+|nzs \d+|iso \d+|astm [a-z]\d+)\b',  # Standards
            r'\b(minimum|maximum|exact|specific).*(cover|clearance|spacing|distance)\b',  # Specific measurements
            r'\b\d+\s*(mm|kpa|kn|m\^?2|degrees?)\b',  # Measurements with units
            r'\b(wind zone [vh]+|ultimate limit state|characteristic load)\b',  # Technical terms
        ]
        
        for pattern in compliance_patterns:
            if re.search(pattern, message_lower):
                return "compliance_strict", 0.85, "precise_citation"
        
        # General advice patterns (medium confidence)
        advice_patterns = [
            r'\b(how to|how do i|what should|best practice|recommend)\b',
            r'\b(check|inspect|install|fix|repair|maintain)\b',
            r'\b(what.*(spacings?|pitch|slope|requirements?))\b',
            r'\b(which.*(clause|standard|code|method))\b',
        ]
        
        building_terms = ['flashing', 'roofing', 'stud', 'nog', 'joist', 'rafter', 'membrane', 'underlay', 'fastener', 'cladding']
        has_building_content = any(term in message_lower for term in building_terms)
        
        if has_building_content:
            for pattern in advice_patterns:
                if re.search(pattern, message_lower):
                    return "general_advice", 0.75, "practical_guidance"
        
        # Clarifying patterns (medium-low confidence)
        clarify_patterns = [
            r'\b(new to|beginner|getting started|don\'t know|help me understand)\b',
            r'\b(what should i know|where do i start|basics|overview)\b',
            r'\b(first time|never done|not sure)\b',
        ]
        
        for pattern in clarify_patterns:
            if re.search(pattern, message_lower):
                return "clarify", 0.65, "educational"
        
        # General building (low-medium confidence)
        if has_building_content:
            return "general_building", 0.60, "practical_guidance"
        
        return "unknown", 0.30, "clarify_first"
    
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
        """Get system prompt based on intent and answer style"""
        
        base_prompt = """You are STRYDA, a practical NZ building assistant. Give concise, step-by-step, trade-friendly answers. 
If the user asks broadly, propose the key checks (e.g., wind zone, pitch, material, span). 
If uncertain, ask 1 clarifying question before deciding. 
Only include citations when the user asks for sources or the intent is compliance/pinpoint."""
        
        style_prompts = {
            "friendly": base_prompt + "\n\nThis is casual conversation. Be warm and helpful.",
            "educational": base_prompt + "\n\nProvide educational guidance with 1-2 clarifying questions.",
            "practical_guidance": base_prompt + "\n\nGive practical, step-by-step guidance. Focus on what they need to check or do.",
            "precise_citation": base_prompt + "\n\nBe precise and technical. Always cite specific sources and clauses.",
            "clarify_first": base_prompt + "\n\nAsk clarifying questions to understand what they need."
        }
        
        return style_prompts.get(answer_style, base_prompt)
    
    @staticmethod
    def should_ask_clarifying_question(intent: str, confidence: float) -> bool:
        """Determine if we should ask for clarification"""
        return confidence < 0.55 or intent == "unknown"

# Export for use in main app
intent_router = IntentRouter()