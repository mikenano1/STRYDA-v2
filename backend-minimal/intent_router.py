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
        Enhanced classification with B1 Amendment 13 priority
        """
        message_lower = message.lower().strip()
        
        # PRIORITY: Force compliance_strict for amendment queries
        AMEND_PAT = re.compile(r'\b(amend(?:ment)?\s*13|amdt\s*13|amend\s*13|b1\s*a\s*13|b1\s*amendment)\b', re.I)
        if AMEND_PAT.search(message):
            return "compliance_strict", 0.95, "precise_citation"
        
        # Chitchat patterns (high confidence) - unchanged
        chitchat_patterns = [
            r'\b(hi|hello|hey|ping|test|thanks?|thank you|bye|goodbye|good morning|good day)\b',
            r'^(how are you|what\'s up|testing|all good|cheers)$',
            r'\b(cool|nice|great|awesome|perfect|sweet|thanks)\b$',
            r'^(kia ora|gday|morning)$',
        ]
        
        for pattern in chitchat_patterns:
            if re.search(pattern, message_lower):
                return "chitchat", 0.95, "friendly"
        
        # AGGRESSIVE Tier-1 compliance detection - catch all variants
        tier1_compliance_patterns = [
            # NZS 3604 patterns - enhanced for all variants
            r'\b(nzs 3604|stud spacing|stud centres?|stud centers?|timber|lintel|fixing|span)\b',
            r'\bstud\s+.*(spacing|centres?|centers?)\b',
            r'\b\d+\.?\d*\s*m?\s*(wall|stud|spacing|centres?)\b',  # "2.4m", "2400", "2.4 spacing"
            
            # E2/AS1 patterns - enhanced for all variants  
            r'\b(e2/?as1|e2\s+as1|external moisture)\b',
            r'\b(apron|head)\s*.*(flashing|cover)\b',
            r'\b(minimum|maximum)\s*.*(cover|clearance|mm)\b',
            r'\b(roof pitch|pitch|corrugate|underlay|cladding)\b',
            r'\bapron\s*cover\s*mm\b',  # "apron cover mm"
            r'\broof.?to.?wall\b',  # "roof-to-wall"
            
            # B1/AS1 patterns - enhanced for all variants
            r'\b(b1/?as1|b1\s+as1)\b',
            r'\b(wind\s*bracing?|bracing\s*.*(units?|demand|requirement|wall))\b',
            r'\b(wind\s*brace?\s*req)\b',  # "wind brace req"
            r'\b(earthquake bracing|hold-downs|brace wall)\b',
            r'\b(engineering design|specific engineering|structure)\b',
            
            # Measurement and compliance indicators
            r'\b(clause [a-h]\d+|[a-h]\d+/[a-z]+\d+)\b',
            r'\b\d+\s*(mm|kpa|kn|m\^?2|degrees?)\b',
            r'\b\d{4}\s*(centre|center|spacing)\b',  # "2400 centre"
            r'\b(requirement|minimum|maximum|shall|must)\b',
        ]
        
        # Priority check: Tier-1 compliance first (ENHANCED for B1 Amendment 13)
        for pattern in tier1_compliance_patterns:
            if re.search(pattern, message_lower):
                return "compliance_strict", 0.85, "precise_citation"
        
        # Specific B1 Amendment 13 detection
        if any(term in message_lower for term in ['amendment 13', 'b1 amendment', 'latest b1']):
            return "compliance_strict", 0.90, "precise_citation"
        
        # How-to patterns (medium confidence)
        how_to_patterns = [
            r'\b(how to|how do i|step by step|best way to|process for)\b',
            r'\b(install|fix|repair|maintain|check|inspect)\b.*\b(roof|flashing|gutter)\b',
            r'(where do i start|new to|beginner|getting started)',
        ]
        
        building_terms = ['flashing', 'roofing', 'stud', 'nog', 'joist', 'rafter', 'membrane', 'underlay', 'fastener', 'cladding', 'gutter']
        has_building_content = any(term in message_lower for term in building_terms)
        
        if has_building_content:
            for pattern in how_to_patterns:
                if re.search(pattern, message_lower):
                    return "general_advice", 0.75, "practical_guidance"
        
        # Clarifying patterns (only for truly ambiguous queries)
        clarify_patterns = [
            r'\b(help|advice|guidance|suggestions?)\s*$',  # Only at end of query
            r'^(what|where|why|which)\s+\?\s*$',  # Very short questions
            r'\b(not sure|unsure|confused|unclear)\b',
        ]
        
        for pattern in clarify_patterns:
            if re.search(pattern, message_lower):
                return "clarify", 0.65, "educational"
        
        # Default to compliance for building terms (safer than clarify)
        if has_building_content:
            return "compliance_strict", 0.70, "precise_citation"  # Changed from clarify
        
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

User: "Are you smarter than a builder?"
Intent: chitchat
Assistant: "I'm fast with the paperwork; the builder's the pro with tools. Think of me as your code sidekick."

User: "Thanks for the help"
Intent: chitchat  
Assistant: "No worries! Always here when you need building code backup."

2) How-to (plain language, stepwise, no citations unless user asks or low confidence)
User: "How do I fix a leaking gutter?"
Intent: how_to
Assistant: "Here's a quick plan:
1) Clear leaves and muck.
2) Check joints for gaps or loose screws.
3) Seal hairline gaps with gutter sealant.
4) Reseat and re-screw loose joints.
5) Replace badly rusted sections.
Tip: If leaks return after rain, the fall may be wrong and you'll need to re-hang a section."

User: "How do I install roofing underlay?"
Intent: how_to
Assistant: "Run it horizontally from eaves, 150 mm overlaps, fix to rafters/purlins without sag. Tape penetrations, and don't leave it exposed more than a few days before cladding."

User: "I'm new to roofing, where do I start?"
Intent: how_to
Assistant: "Start with the basics:
1) Check your wind zone (council website)
2) Get consent if needed (anything structural)
3) Plan material delivery access
4) Weather timing (dry spell forecast)
5) Safety gear and fall protection
What type of roof are you planning?"

3) Compliance (precise + citations ≤3)
User: "What is the minimum cover for apron flashing?"
Intent: compliance
Assistant: "Minimum apron flashing cover is 150 mm in standard conditions."
[Citations: NZ Metal Roofing Code of Practice, p.231]

User: "Explain NZBC clause E2."
Intent: compliance
Assistant: "E2 covers external moisture—keeping water out of the building. Acceptable Solution E2/AS1 includes roof pitches, flashings, and cladding details."
[Citations: NZBC E2/AS1, p.15]

4) Clarify (vague request)
User: "Do I need a permit?"
Intent: clarify
Assistant: "Do you mean a council building consent or a site safety permit? What work are you doing (e.g., reroof, new deck, internal wall change)? Two examples that help me answer quickly:
• 'Reroofing Colorsteel over existing purlins in a high-wind zone.'
• 'New internal load-bearing wall in a single-storey dwelling.'"

User: "I need help with studs"
Intent: clarify
Assistant: "Are you asking about:
• Spacing for wall studs?
• Sizing for load-bearing walls?  
• Fastening to foundations?
Examples that help me give exact answers:
• '90mm stud spacing in Very High wind zone'
• 'Load-bearing wall studs for 6m span'"

5) New Source Integration Examples:

User: "What stud spacing for 2.4m wall?"
Intent: compliance
Assistant: "For 2.4m wall height: 450mm spacing for 90mm studs in Medium wind, 600mm in Low wind per NZS 3604."
[Citations: NZS 3604:2011, Table 7.2]

User: "How do I flash around a window?"
Intent: how_to  
Assistant: "Window flashing sequence:
1) Install sill flashing first (slope away from window)
2) Side flashings overlap sill by 25mm minimum
3) Head flashing over side flashings
4) All flashings extend past frame by 100mm minimum
Check E2/AS1 for your specific cladding type."

User: "E2/AS1 minimum roof pitch"
Intent: compliance
Assistant: "E2/AS1 sets minimum roof pitches: 3° for membrane, 5° for metal with sealed joints, 8° for metal with lapped joints."
[Citations: NZBC E2/AS1, Table 1]
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