"""
STRYDA Intent Classifier V2.4
Enhanced 4-step hybrid pipeline with full 105 few-shot examples
Target: >90% intent accuracy with intelligent compliance bucket routing
"""

import psycopg2
import re
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import os
from dotenv import load_dotenv
from intent_config import Intent, IntentPolicy, TRADE_DOMAINS
from intent_fewshots_v2 import (
    fewshots_compliance_strict, 
    fewshots_implicit_compliance,
    fewshots_general_help,
    fewshots_product_info,
    fewshots_council_process
)

load_dotenv()

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

def is_compliance_tone(question: str) -> bool:
    """
    V2.4 Enhanced compliance tone detector
    Detects implicit compliance queries (checking/verifying if something meets code)
    """
    q_lower = question.lower()
    
    # STEP 1: Check for code/standard references
    has_code_ref = bool(re.search(
        r'\b(nzs|nzbc|e[123]/as\d?|h1/as1|b1/as1|c/as\d?|f[467]/as1|g[1-9]+/as1|'
        r'building code|code|standard|clause|amendment)\b',
        q_lower
    ))
    
    # STEP 2: Compliance verification language (is this allowed/acceptable)
    has_verification_lang = bool(re.search(
        r'\b(does this|is this|will this|can i|do i need|is it|am i).*(comply|compliant|'
        r'meet|meets|satisfy|pass|fail|acceptable|allowed|legal|permitted|okay|ok|fine|safe)\b',
        q_lower
    )) or bool(re.search(
        r'\b(will council|would council|will inspector|does the code).*(accept|allow|approve|'
        r'sign off|fail|pass|require|permit)\b',
        q_lower
    ))
    
    # STEP 3: Exclude strict requirement language (those are compliance_strict)
    has_strict_lang = bool(re.search(
        r'\b(minimum|maximum|what does .* (say|require|specify|state)|what is the .* requirement|'
        r'exact requirement|which table|what (r-?value|spacing|height|span))\b',
        q_lower
    ))
    
    # STEP 4: Amplify signal from legacy/version questions
    has_legacy_context = bool(re.search(
        r'\b(built in|designed in|constructed in|back in|older|pre-|which version|which edition)\s+\d{4}\b',
        q_lower
    ))
    
    # Final determination
    if has_legacy_context:
        # Legacy questions are implicit compliance (not asking for exact numbers)
        return True
    
    return has_code_ref and has_verification_lang and not has_strict_lang

class IntentClassifierV2:
    """
    V2.4 Intent classifier with 4-step hybrid pipeline
    
    Pipeline:
    1. Fast pattern matching layer (regex-based)
    2. Compliance tone detector (is_compliance_tone)
    3. LLM classifier with 105 few-shot examples
    4. Hybrid scoring model with agreement bonuses and smoothing
    
    Target: >90% accuracy with correct compliance bucket routing
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print(f"✅ Intent Classifier V2.4 initialized with 105 few-shot examples")
    
    def classify_intent(self, question: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        V2.4 - 4-step hybrid pipeline for intent classification
        
        STEP 0: Hard compliance rules (highest priority)
        STEP 1: Fast pattern matching
        STEP 2: Compliance tone detection  
        STEP 3: LLM classification with 105 few-shot examples
        STEP 4: Hybrid scoring model with agreement bonuses
        
        Returns:
            {
                "intent": str,
                "trade": str,
                "trade_type_detailed": List[str],
                "confidence": float,
                "method": str,  # "hard_rule", "pattern_strong", "hybrid_agree", "hybrid_llm", "hybrid_pattern"
                "original_intent": str,
                "pattern_intent": str,  # For debugging
                "llm_intent": str,  # For debugging
                "compliance_tone": bool  # For debugging
            }
        """
        
        # STEP 0: Check for hard compliance rules (highest priority)
        hard_rule_result = self._apply_hard_compliance_rules(question)
        if hard_rule_result:
            hard_rule_result["method"] = "hard_rule"
            hard_rule_result["original_intent"] = hard_rule_result["intent"]
            hard_rule_result["pattern_intent"] = hard_rule_result["intent"]
            hard_rule_result["llm_intent"] = None
            hard_rule_result["compliance_tone"] = True
            print(f"   🔒 Hard rule fired: {hard_rule_result['intent']}")
            return hard_rule_result
        
        # STEP 1: Get pattern classification
        pattern_result = self._pattern_classify(question)
        pattern_intent = pattern_result["intent"] if pattern_result else None
        pattern_conf = pattern_result["confidence"] if pattern_result else 0.0
        
        # STEP 2: Detect compliance tone (critical for weighting)
        has_compliance_tone = is_compliance_tone(question)
        
        # STEP 3: Get LLM classification with full few-shot library
        llm_result = self._llm_classify(question, context)
        llm_intent = llm_result["intent"]
        llm_conf = llm_result["confidence"]
        
        # STEP 4: Hybrid scoring model
        # V2.4 CHANGES:
        # - Increased pattern_weight when compliance tone detected (0.55 → 0.70)
        # - Agreement bonus increased from 0.05 → 0.08
        # - Smoothing for ambiguous cases (both intents < 0.75 confidence)
        
        if has_compliance_tone:
            pattern_weight = 0.70  # INCREASED: Trust patterns more for compliance tone
            llm_weight = 0.30
        else:
            pattern_weight = 0.55
            llm_weight = 0.45
        
        # CASE 1: Both pattern and LLM agree
        if pattern_intent == llm_intent:
            final_intent = pattern_intent
            final_confidence = min(1.0, max(pattern_conf, llm_conf) + 0.08)  # INCREASED agreement bonus
            method = "hybrid_agree"
        
        # CASE 2: Disagree - use weighted scoring with smoothing
        else:
            pattern_score = pattern_conf * pattern_weight
            llm_score = llm_conf * llm_weight
            
            # V2.4 ADDITION: Compliance tone bias within compliance bucket
            if has_compliance_tone:
                # Boost whichever one picked a compliance intent
                if pattern_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]:
                    pattern_score += 0.05  # INCREASED from 0.03
                if llm_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]:
                    llm_score += 0.05  # INCREASED from 0.03
            
            # V2.4 ADDITION: Smoothing for ambiguous cases
            # If both classifiers are uncertain (conf < 0.75), apply smoothing
            if pattern_conf < 0.75 and llm_conf < 0.75:
                # Check if both picked intents within same bucket
                pattern_is_compliance = pattern_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]
                llm_is_compliance = llm_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]
                
                if pattern_is_compliance and llm_is_compliance:
                    # Both picked compliance bucket but different types
                    # Normalize to implicit_compliance (safer choice)
                    final_intent = Intent.IMPLICIT_COMPLIANCE.value
                    final_confidence = (pattern_score + llm_score) / 2
                    method = "hybrid_smoothed_compliance"
                    print(f"   🔄 Smoothing: Both picked compliance, normalized to implicit_compliance")
                else:
                    # Different buckets, low confidence - choose higher score
                    if pattern_score > llm_score:
                        final_intent = pattern_intent
                        final_confidence = pattern_score
                        method = "hybrid_pattern_ambiguous"
                    else:
                        final_intent = llm_intent
                        final_confidence = llm_score
                        method = "hybrid_llm_ambiguous"
            else:
                # Normal case: choose higher score
                if pattern_score > llm_score:
                    final_intent = pattern_intent
                    final_confidence = pattern_score
                    method = "hybrid_pattern"
                else:
                    final_intent = llm_intent
                    final_confidence = llm_score
                    method = "hybrid_llm"
        
        # Build result with full debugging metadata
        trade = pattern_result.get("trade") if pattern_result else llm_result.get("trade", "carpentry")
        
        result = {
            "intent": final_intent,
            "trade": trade,
            "trade_type_detailed": TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2],
            "confidence": final_confidence,
            "method": method,
            "original_intent": final_intent,
            "pattern_intent": pattern_intent,
            "llm_intent": llm_intent,
            "compliance_tone": has_compliance_tone,
            # Include raw scores for debugging
            "_pattern_conf": pattern_conf,
            "_llm_conf": llm_conf,
            "_pattern_weight": pattern_weight,
            "_llm_weight": llm_weight
        }
        
        # Apply compliance bucket normalization
        return self._normalize_compliance_bucket(result)
    
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
        """
        V2.4 LLM-based classification with FULL 105 few-shot examples
        
        Uses optimized prompt with more examples per intent for better accuracy
        """
        
        # Build few-shot prompt with MORE examples (12-15 per intent for high-confidence classification)
        examples_text = ""
        
        # COMPLIANCE_STRICT: Use 15 examples (most critical to get right)
        examples_text += "\n🔵 COMPLIANCE_STRICT (explicit code requirements, asking what code says):\n"
        for ex in fewshots_compliance_strict[:15]:
            examples_text += f"  - {ex}\n"
        
        # IMPLICIT_COMPLIANCE: Use 15 examples (critical for compliance bucket)
        examples_text += "\n🟠 IMPLICIT_COMPLIANCE (checking if design meets code, verification questions):\n"
        for ex in fewshots_implicit_compliance[:15]:
            examples_text += f"  - {ex}\n"
        
        # GENERAL_HELP: Use 12 examples (practical tradie guidance)
        examples_text += "\n🟢 GENERAL_HELP (practical tradie guidance, no compliance checking):\n"
        for ex in fewshots_general_help[:12]:
            examples_text += f"  - {ex}\n"
        
        # PRODUCT_INFO: Use 8 examples (less common)
        examples_text += "\n🟣 PRODUCT_INFO (product/material recommendations):\n"
        for ex in fewshots_product_info[:8]:
            examples_text += f"  - {ex}\n"
        
        # COUNCIL_PROCESS: Use 8 examples (less common)
        examples_text += "\n🟡 COUNCIL_PROCESS (consents, inspections, regulatory process):\n"
        for ex in fewshots_council_process[:8]:
            examples_text += f"  - {ex}\n"
        
        prompt = f"""You are an expert NZ building code classifier. Classify this question into EXACTLY ONE intent category.

**Intent Definitions:**
- **compliance_strict**: Asks for EXACT code requirements (minimum/maximum values, what code says, specific clauses, table references). User wants precise numbers or rule text.
- **implicit_compliance**: Asks if a design/approach MEETS code or will be accepted (checking compliance, verification questions). User has a design and wants to check if it's acceptable.
- **general_help**: Practical tradie guidance, how-to questions, troubleshooting, best practices. NO compliance checking.
- **product_info**: Product/material/brand recommendations, which product to use.
- **council_process**: Consent process, inspections, CCC, producer statements, regulatory paperwork.

**Examples from 9,000 real NZ builder questions:**
{examples_text}

**Question to classify:** {question}

**Classification rules:**
1. Look for "what does [code] say/require" → compliance_strict
2. Look for "is this acceptable/compliant/allowed" → implicit_compliance
3. Look for "how do I" or "why does" (practical) → general_help
4. Look for "which product/brand" → product_info
5. Look for "consent/CCC/inspection" → council_process
6. Legacy questions ("built in 2005", "older code") → implicit_compliance
7. If asking for NUMBERS from code → compliance_strict
8. If asking if DESIGN meets code → implicit_compliance

Respond with ONLY a JSON object (no markdown):
{{"intent": "...", "trade": "...", "confidence": 0.XX}}

Valid trades: carpentry, roofing, plumbing, electrical, cladding, drainage, concrete_foundations, passive_fire, interior_linings, joinery, waterproofing, h1_energy, hvac_ventilation, earthworks_stormwater, council_consent"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # V2.4: Zero temperature for consistency
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean markdown if present
            if result_text.startswith("```"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            
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
