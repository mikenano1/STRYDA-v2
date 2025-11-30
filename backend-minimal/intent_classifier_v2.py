"""
STRYDA Intent Classifier V2
Uses training_questions_v2 dataset for accurate intent classification
"""

import psycopg2
import re
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import os
from dotenv import load_dotenv
from intent_config import Intent, IntentPolicy, TRADE_DOMAINS

load_dotenv()

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

class IntentClassifierV2:
    """
    Intent classifier using training_questions_v2 as labelled data
    Combines pattern matching + LLM-based classification
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._load_training_samples()
    
    def _load_training_samples(self):
        """Load representative samples from training_questions_v2"""
        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            cur = conn.cursor()
            
            # Get 3 examples per intent for few-shot classification
            self.few_shot_examples = {}
            
            for intent in [Intent.COMPLIANCE_STRICT, Intent.IMPLICIT_COMPLIANCE, 
                          Intent.GENERAL_HELP, Intent.PRODUCT_INFO, Intent.COUNCIL_PROCESS]:
                cur.execute("""
                    SELECT question, trade, trade_type_detailed
                    FROM training_questions_v2
                    WHERE intent = %s
                    ORDER BY RANDOM()
                    LIMIT 3;
                """, (intent.value,))
                
                self.few_shot_examples[intent] = [
                    {"question": q, "trade": t, "trade_type": tt} 
                    for q, t, tt in cur.fetchall()
                ]
            
            cur.close()
            conn.close()
            
            print(f"✅ Loaded few-shot examples for {len(self.few_shot_examples)} intents")
            
        except Exception as e:
            print(f"⚠️ Failed to load training samples: {e}")
            self.few_shot_examples = {}
    
    def classify_intent(self, question: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        Classify user question into intent + trade
        
        Returns:
            {
                "intent": str,
                "trade": str,
                "trade_type_detailed": List[str],
                "confidence": float,
                "method": str,  # "pattern", "llm", or "hard_rule"
                "original_intent": str  # Before normalization
            }
        """
        
        # STEP 0: Check for hard compliance rules (highest priority)
        hard_rule_result = self._apply_hard_compliance_rules(question)
        if hard_rule_result:
            hard_rule_result["method"] = "hard_rule"
            hard_rule_result["original_intent"] = hard_rule_result["intent"]
            return hard_rule_result
        
        # STEP 1: Try pattern-based classification first (fast path)
        pattern_result = self._pattern_classify(question)
        if pattern_result and pattern_result["confidence"] >= 0.85:
            pattern_result["method"] = "pattern"
            pattern_result["original_intent"] = pattern_result["intent"]
            
            # Apply compliance bucket normalization
            return self._normalize_compliance_bucket(pattern_result)
        
        # STEP 2: Use LLM with few-shot examples (accurate path)
        llm_result = self._llm_classify(question, context)
        llm_result["method"] = "llm"
        llm_result["original_intent"] = llm_result["intent"]
        
        # Apply compliance bucket normalization
        return self._normalize_compliance_bucket(llm_result)
    
    def _apply_hard_compliance_rules(self, question: str) -> Optional[Dict]:
        """
        Hard rules to force compliance_strict for explicit standard references
        """
        q_lower = question.lower()
        
        # Standard/code identifiers
        has_standard = bool(re.search(
            r'\b(nzs\s*3604|nzs\s*4229|nzbc|e2/as1|b1/as1|g12/as1|g13/as1|'
            r'h1\s|f4\s|g5\s|c/as2|clause\s+[a-h]\d+|section\s+[a-h]\d+)\b',
            q_lower
        ))
        
        # Requirement phrases
        has_requirement = bool(re.search(
            r'\b(requirements?|minimum|maximum|what does (the code|nzs|nzbc) (say|require|specify)|'
            r'per (nzs|nzbc|code)|according to (nzs|nzbc))\b',
            q_lower
        ))
        
        # Force compliance_strict if both present
        if has_standard and has_requirement:
            trade = self._guess_trade(q_lower)
            return {
                "intent": Intent.COMPLIANCE_STRICT.value,
                "trade": trade,
                "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                "confidence": 0.95
            }
        
        return None
    
    def _normalize_compliance_bucket(self, result: Dict) -> Dict:
        """
        Normalize low-confidence compliance intents to implicit_compliance
        Treats compliance_strict and implicit_compliance as a shared bucket
        """
        intent = result["intent"]
        confidence = result["confidence"]
        
        # If it's a compliance intent but low confidence, normalize to implicit
        if intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]:
            if confidence < 0.70:
                result["intent"] = Intent.IMPLICIT_COMPLIANCE.value
                result["normalized"] = True
                print(f"   🔄 Normalized {result['original_intent']} → implicit_compliance (confidence: {confidence:.2f})")
            else:
                result["normalized"] = False
        else:
            result["normalized"] = False
        
        return result
    
    def _pattern_classify(self, question: str) -> Optional[Dict]:
        """
        Enhanced pattern-based classification with stronger rules
        Returns high confidence for clear patterns, allowing LLM override for ambiguous cases
        """
        q_lower = question.lower()
        
        # COMPLIANCE_STRICT patterns - explicit code requirements with numeric/technical details
        strict_patterns = [
            # Explicit numeric requirements
            r'\b(minimum|maximum|required|shall|must)\s+\d+',  # "minimum 2.4m", "maximum 600mm"
            r'\b(what\s+(are|is)\s+the|what\s+does)\s+(nzs|nzbc|e2|h1|c/as|b1|f4|g5|g12|g13)\s+(requirement|say|require|specify|state)',
            r'\baccording to\s+(nzs|e2|h1|b1|nzbc|code|standard)\b',
            r'\b(nzs\s*3604|nzs\s*4229|e2/as1|h1/as1|b1/as1|c/as\d)\s+(table|clause|section)\s*\d',
            r'\bwhat\s+(r-?value|span|spacing|height|width|depth|thickness|cover)\s+(does|is|are).*(require|code|nzs|standard)',
            # Explicit standard references
            r'\b[a-h]\d+/as\d+\s+(says?|requires?|states?)\b',
            r'\b(nzs|nzbc)\s+\d+\s+(clause|table|section|requirements?)\b',
        ]
        
        for pattern in strict_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {
                    "intent": Intent.COMPLIANCE_STRICT.value,
                    "trade": trade,
                    "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                    "confidence": 0.92
                }
        
        # IMPLICIT_COMPLIANCE patterns - "does this comply / is this allowed" style
        implicit_patterns = [
            r'\b(does this|is this|will this)\s+(comply|meet|satisfy|acceptable|allowed|legal|ok|acceptable)\b',
            r'\b(do i need|is .* required|must i)\s+.*\b(code|standard|nzs|nzbc|comply)\b',
            r'\b(can i|is it ok|is it acceptable|is it legal)\s+.*\b(per|under|code|nzs|nzbc)\b',
            r'\b(will council|would council)\s+(accept|allow|approve|sign off)\b',
            r'\b(ccc|code compliance|producer statement|ps\d)\s+(require|needed|necessary)\b',
            r'\b(is|does).*(acceptable|allowed|permitted|legal)\s+(per|under|in|by)\s+(nzs|code|nzbc)\b',
            # Historical compliance questions
            r'\b(built in|designed in|constructed in)\s+\d{4}.*\b(which|what)\s+(version|code|standard|applies)\b',
            r'\bback in\s+\d{4}.*\b(requirement|code|standard)\b',
        ]
        
        for pattern in implicit_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {
                    "intent": Intent.IMPLICIT_COMPLIANCE.value,
                    "trade": trade,
                    "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                    "confidence": 0.88
                }
        
        # COUNCIL_PROCESS patterns
        council_patterns = [
            r'\b(ccc|code compliance certificate)\b',
            r'\b(ps1|ps3|ps4|producer statement)\b',
            r'\bcouncil\s+(inspection|inspector|sign[- ]?off|approval)\b',
            r'\b(consent|building consent)\s+(process|application|requirement)\b',
            r'\brfi\b',  # Request for information
            r'\bschedule\s*1\b',
        ]
        
        for pattern in council_patterns:
            if re.search(pattern, q_lower):
                return {
                    "intent": Intent.COUNCIL_PROCESS.value,
                    "trade": "council_consent",
                    "trade_type_detailed": ["consents", "inspections"],
                    "confidence": 0.90
                }
        
        # PRODUCT_INFO patterns - strengthened
        product_patterns = [
            r'\bwhat\s+(product|brand|manufacturer|system)\b',
            r'\b(best|recommended)\s+(product|material|brand|system)\b',
            r'\b(gib|james hardie|resene|pink batts|metalcraft|ardex)\b',  # NZ brands
            r'\bwhat\s+.*(works best|suits|lasts longest|performs best|should i use)\b',
            r'\baccording to\s+(nz metal roofing|wganz|gib|ardex|manufacturer)\b',
            r'\bwhich\s+(gib|ardex|metal roofing|manufacturer)\s+system\b',
        ]
        
        for pattern in product_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {
                    "intent": Intent.PRODUCT_INFO.value,
                    "trade": trade,
                    "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                    "confidence": 0.87
                }
        
        # GENERAL_HELP (fallback for practical questions)
        trade = self._guess_trade(q_lower)
        return {
            "intent": Intent.GENERAL_HELP.value,
            "trade": trade,
            "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
            "confidence": 0.70
        }
    
    def _guess_trade(self, question_lower: str) -> str:
        """Guess trade from question keywords"""
        trade_scores = {}
        
        for trade, config in TRADE_DOMAINS.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword.lower() in question_lower:
                    score += 1
            trade_scores[trade] = score
        
        if not trade_scores or max(trade_scores.values()) == 0:
            return "carpentry"  # Default
        
        return max(trade_scores.items(), key=lambda x: x[1])[0]
    
    def _llm_classify(self, question: str, context: Optional[List[Dict]] = None) -> Dict:
        """LLM-based classification using few-shot examples"""
        
        # Build few-shot prompt
        examples_text = ""
        if self.few_shot_examples:
            for intent, samples in list(self.few_shot_examples.items())[:3]:  # Use 3 intents
                examples_text += f"\n{intent.value} examples:\n"
                for sample in samples[:2]:  # 2 per intent
                    examples_text += f"  - {sample['question']}\n"
        
        prompt = f"""Classify this NZ building trade question into ONE intent category:

Intents:
- compliance_strict: Explicit code/standard queries requiring precise citations
- implicit_compliance: Code-aware but conversational
- general_help: Practical tradie guidance
- product_info: Product/material recommendations
- council_process: Consent/inspection/regulatory process

{examples_text}

Question: {question}

Respond with ONLY a JSON object:
{{"intent": "...", "trade": "...", "confidence": 0.XX}}

Valid trades: carpentry, roofing, plumbing, electrical, cladding, drainage, concrete_foundations, passive_fire, interior_linings, joinery, waterproofing, h1_energy, hvac_ventilation, earthworks_stormwater, council_consent"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON
            import json
            result = json.loads(result_text)
            
            # Add trade_type_detailed
            trade = result.get("trade", "carpentry")
            result["trade_type_detailed"] = TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2]
            
            return result
            
        except Exception as e:
            print(f"⚠️ LLM classification failed: {e}")
            # Fallback to pattern
            return self._pattern_classify(question) or {
                "intent": Intent.GENERAL_HELP.value,
                "trade": "carpentry",
                "trade_type_detailed": [],
                "confidence": 0.50
            }

# Global classifier instance
_classifier = None

def get_classifier() -> IntentClassifierV2:
    """Get or create global classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifierV2()
    return _classifier

def classify_intent(question: str, context: Optional[List[Dict]] = None) -> Dict:
    """
    Main classification function
    
    Args:
        question: User question
        context: Optional conversation history
    
    Returns:
        {
            "intent": str,
            "trade": str,
            "trade_type_detailed": List[str],
            "confidence": float,
            "method": str
        }
    """
    classifier = get_classifier()
    return classifier.classify_intent(question, context)
