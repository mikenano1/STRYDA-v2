"""
STRYDA Intent Classifier V2
Uses training_questions_v2 dataset for accurate intent classification
"""

import psycopg2
import re
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import os
from intent_config import Intent, IntentPolicy, TRADE_DOMAINS

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
                "method": str  # "pattern" or "llm"
            }
        """
        
        # STEP 1: Try pattern-based classification first (fast path)
        pattern_result = self._pattern_classify(question)
        if pattern_result and pattern_result["confidence"] >= 0.85:
            pattern_result["method"] = "pattern"
            return pattern_result
        
        # STEP 2: Use LLM with few-shot examples (accurate path)
        llm_result = self._llm_classify(question, context)
        llm_result["method"] = "llm"
        return llm_result
    
    def _pattern_classify(self, question: str) -> Optional[Dict]:
        """Fast pattern-based classification"""
        q_lower = question.lower()
        
        # COMPLIANCE_STRICT patterns
        strict_patterns = [
            r'\b(nzs\s*3604|nzs\s*4229)\s+\d+\.\d+',  # NZS 3604 7.1
            r'\b[a-h]\d+/as\d+\b',  # E2/AS1, B1/AS1
            r'\b[a-h]\d+\.\d+\.\d+\b',  # H1.2.3, G5.3.2
            r'\bwhat\s+are\s+the\s+(nzs|b1|e2|h1|f4|g5)\s+requirements\b',
            r'\bwhat\s+does\s+(nzs|nzbc|building code)\s+say\b',
            r'\b(minimum|maximum)\s+.*(per|under|according to)\s+(nzs|e2|b1|h1)\b'
        ]
        
        for pattern in strict_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {
                    "intent": Intent.COMPLIANCE_STRICT.value,
                    "trade": trade,
                    "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                    "confidence": 0.90
                }
        
        # COUNCIL_PROCESS patterns
        council_patterns = [
            r'\b(ccc|code compliance certificate)\b',
            r'\b(ps1|ps3|ps4|producer statement)\b',
            r'\bcouncil\s+(inspection|inspector|sign[- ]?off)\b',
            r'\b(consent|building consent)\s+(process|application|requirement)\b',
            r'\brfi\b',  # Request for information
        ]
        
        for pattern in council_patterns:
            if re.search(pattern, q_lower):
                return {
                    "intent": Intent.COUNCIL_PROCESS.value,
                    "trade": "council_consent",
                    "trade_type_detailed": ["consents", "inspections"],
                    "confidence": 0.88
                }
        
        # PRODUCT_INFO patterns
        product_patterns = [
            r'\bwhat\s+(product|brand|manufacturer)\b',
            r'\b(best|recommended)\s+(product|material|brand)\b',
            r'\b(gib|james hardie|resene|pink batts|metalcraft)\b',  # NZ brands
            r'\bwhat\s+.*(works best|suits|lasts longest|performs best)\b',
        ]
        
        for pattern in product_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {
                    "intent": Intent.PRODUCT_INFO.value,
                    "trade": trade,
                    "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                    "confidence": 0.85
                }
        
        # IMPLICIT_COMPLIANCE patterns (mentions compliance but conversational)
        if any(term in q_lower for term in ['meets', 'compliant', 'code', 'standard', 'building code']):
            if any(term in q_lower for term in ['how do i', 'best way', 'should i']):
                trade = self._guess_trade(q_lower)
                return {
                    "intent": Intent.IMPLICIT_COMPLIANCE.value,
                    "trade": trade,
                    "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
                    "confidence": 0.80
                }
        
        # GENERAL_HELP (fallback)
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
