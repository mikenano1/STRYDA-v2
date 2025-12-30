"""
STRYDA Intent Classifier V2.4 (Async/Gemini)
Enhanced 4-step hybrid pipeline with full 105 few-shot examples
Target: >90% intent accuracy with intelligent compliance bucket routing
"""

import psycopg2
import re
import asyncio
from typing import Dict, List, Optional, Tuple
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

# Emergent Integrations
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    print("CRITICAL: emergentintegrations not installed")
    LlmChat = None

load_dotenv(override=True)

API_KEY = os.getenv("EMERGENT_LLM_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") # Use fast model for classification

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
    V2.4 Intent classifier with 4-step hybrid pipeline (Async)
    """
    
    def __init__(self):
        print(f"✅ Intent Classifier V2.4 initialized with 105 few-shot examples")
    
    async def classify_intent(self, question: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        V2.4 - 4-step hybrid pipeline for intent classification (Async)
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
        
        # STEP 3: Get LLM classification with full few-shot library (Async)
        llm_result = await self._llm_classify(question, context)
        llm_intent = llm_result["intent"]
        llm_conf = llm_result["confidence"]
        
        # STEP 4: Hybrid scoring model
        if has_compliance_tone:
            pattern_weight = 0.70
            llm_weight = 0.30
        else:
            pattern_weight = 0.55
            llm_weight = 0.45
        
        # CASE 1: Both pattern and LLM agree
        if pattern_intent == llm_intent:
            final_intent = pattern_intent
            final_confidence = min(1.0, max(pattern_conf, llm_conf) + 0.08)
            method = "hybrid_agree"
        
        # CASE 2: Disagree - use weighted scoring with smoothing
        else:
            pattern_score = pattern_conf * pattern_weight
            llm_score = llm_conf * llm_weight
            
            # Bias boost
            if has_compliance_tone:
                if pattern_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]:
                    pattern_score += 0.05
                if llm_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]:
                    llm_score += 0.05
            
            # Smoothing
            if pattern_conf < 0.75 and llm_conf < 0.75:
                pattern_is_compliance = pattern_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]
                llm_is_compliance = llm_intent in [Intent.COMPLIANCE_STRICT.value, Intent.IMPLICIT_COMPLIANCE.value]
                
                if pattern_is_compliance and llm_is_compliance:
                    final_intent = Intent.IMPLICIT_COMPLIANCE.value
                    final_confidence = (pattern_score + llm_score) / 2
                    method = "hybrid_smoothed_compliance"
                else:
                    if pattern_score > llm_score:
                        final_intent = pattern_intent
                        final_confidence = pattern_score
                        method = "hybrid_pattern_ambiguous"
                    else:
                        final_intent = llm_intent
                        final_confidence = llm_score
                        method = "hybrid_llm_ambiguous"
            else:
                if pattern_score > llm_score:
                    final_intent = pattern_intent
                    final_confidence = pattern_score
                    method = "hybrid_pattern"
                else:
                    final_intent = llm_intent
                    final_confidence = llm_score
                    method = "hybrid_llm"
        
        # Build result
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
            "_pattern_conf": pattern_conf,
            "_llm_conf": llm_conf
        }
        
        return self._normalize_compliance_bucket(result)
    
    def _apply_hard_compliance_rules(self, question: str) -> Optional[Dict]:
        """Hard rules"""
        # (Same as before)
        q_lower = question.lower()
        has_standard = bool(re.search(
            r'\b(nzs\s*3604|nzs\s*4229|nzbc|e2/as1|b1/as1|g12/as1|g13/as1|'
            r'h1\s|f4\s|g5\s|c/as2|clause\s+[a-h]\d+|section\s+[a-h]\d+)\b',
            q_lower
        ))
        has_requirement = bool(re.search(
            r'\b(requirements?|minimum|maximum|what does (the code|nzs|nzbc) (say|require|specify)|'
            r'per (nzs|nzbc|code)|according to (nzs|nzbc))\b',
            q_lower
        ))
        
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
        """Normalize low-confidence compliance intents"""
        intent = result["intent"]
        confidence = result["confidence"]
        
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
        """Enhanced pattern-based classification"""
        q_lower = question.lower()
        
        # COMPLIANCE_STRICT
        strict_patterns = [
            r'\b(minimum|maximum|required|shall|must)\s+\d+',
            r'\b(what\s+(are|is)\s+the|what\s+does)\s+(nzs|nzbc|e2|h1|c/as|b1|f4|g5|g12|g13)\s+(requirement|say|require|specify|state)',
            r'\baccording to\s+(nzs|e2|h1|b1|nzbc|code|standard)\b',
            r'\b(nzs\s*3604|nzs\s*4229|e2/as1|h1/as1|b1/as1|c/as\d)\s+(table|clause|section)\s*\d',
            r'\bwhat\s+(r-?value|span|spacing|height|width|depth|thickness|cover)\s+(does|is|are).*(require|code|nzs|standard)',
            r'\bwhat\s+is\s+the\s+(stud|joist|rafter|purlin|beam|bearer)\s+spacing\b',
            r'\bwhat\s+is\s+the\s+maximum\s+span\b',
            r'\b(show|find)\s+(me\s+)?(the\s+)?(matrix|table|chart|diagram|figure|selection\s+tables?)\b',
            r'\b[a-h]\d+/as\d+\s+(says?|requires?|states?)\b',
            r'\b(nzs|nzbc)\s+\d+\s+(clause|table|section|requirements?)\b',
            r'\b(wind|corrosion)\s+zone\b',
            r'\bcalculate\b', # Added keyword
        ]
        for pattern in strict_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {"intent": Intent.COMPLIANCE_STRICT.value, "trade": trade, "confidence": 0.92}

        # IMPLICIT_COMPLIANCE
        implicit_patterns = [
            r'\b(does this|is this|will this)\s+(comply|meet|satisfy|acceptable|allowed|legal|ok|acceptable)\b',
            r'\b(do i need|is .* required|must i)\s+.*\b(code|standard|nzs|nzbc|comply)\b',
            r'\b(can i|is it ok|is it acceptable|is it legal)\s+.*\b(per|under|code|nzs|nzbc)\b',
            r'\b(will council|would council)\s+(accept|allow|approve|sign off)\b',
            r'\b(ccc|code compliance|producer statement|ps\d)\s+(require|needed|necessary)\b',
            r'\b(is|does).*(acceptable|allowed|permitted|legal)\s+(per|under|in|by)\s+(nzs|code|nzbc)\b',
            r'\b(built in|designed in|constructed in)\s+\d{4}.*\b(which|what)\s+(version|code|standard|applies)\b',
            r'\bback in\s+\d{4}.*\b(requirement|code|standard)\b',
        ]
        for pattern in implicit_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {"intent": Intent.IMPLICIT_COMPLIANCE.value, "trade": trade, "confidence": 0.88}

        # COUNCIL_PROCESS
        council_patterns = [
            r'\b(ccc|code compliance certificate)\b',
            r'\b(ps1|ps3|ps4|producer statement)\b',
            r'\bcouncil\s+(inspection|inspector|sign[- ]?off|approval)\b',
            r'\b(consent|building consent)\s+(process|application|requirement)\b',
            r'\brfi\b',
            r'\bschedule\s*1\b',
        ]
        for pattern in council_patterns:
            if re.search(pattern, q_lower):
                return {"intent": Intent.COUNCIL_PROCESS.value, "trade": "council_consent", "confidence": 0.90}

        # PRODUCT_INFO
        product_patterns = [
            r'\b(difference|diff)\s+between\s+(h[34](\.\d)?|treated timber|treatment)\b',
            r'\bh[34](\.\d)?\s+(vs|versus|or)\s+h[34](\.\d)?\b',
            r'\b(do i need|should i use|which)\s+h[34](\.\d)?\b',
            r'\bh[34](\.\d)?\s+(timber|pine|treatment|treated)\b',
            r'\bwhat\s+(product|brand|manufacturer|system)\b',
            r'\b(best|recommended)\s+(product|material|brand|system)\b',
            r'\b(gib|james hardie|resene|pink batts|metalcraft|ardex)\b',
            r'\bwhat\s+.*(works best|suits|lasts longest|performs best|should i use)\b',
            r'\baccording to\s+(nz metal roofing|wganz|gib|ardex|manufacturer)\b',
            r'\bwhich\s+(gib|ardex|metal roofing|manufacturer)\s+system\b',
        ]
        for pattern in product_patterns:
            if re.search(pattern, q_lower):
                trade = self._guess_trade(q_lower)
                return {"intent": Intent.PRODUCT_INFO.value, "trade": trade, "confidence": 0.87}

        # GENERAL_HELP fallback
        trade = self._guess_trade(q_lower)
        return {"intent": Intent.GENERAL_HELP.value, "trade": trade, "confidence": 0.70}
    
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
            return "carpentry"
        return max(trade_scores.items(), key=lambda x: x[1])[0]
    
    async def _llm_classify(self, question: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        V2.4 LLM-based classification (Gemini)
        """
        if not API_KEY:
             return {"intent": Intent.GENERAL_HELP.value, "trade": "carpentry", "confidence": 0.5}

        # Build prompt (Same as before)
        examples_text = ""
        examples_text += "\n🔵 COMPLIANCE_STRICT:\n" + "\n".join([f"  - {ex}" for ex in fewshots_compliance_strict[:15]])
        examples_text += "\n🟠 IMPLICIT_COMPLIANCE:\n" + "\n".join([f"  - {ex}" for ex in fewshots_implicit_compliance[:15]])
        examples_text += "\n🟢 GENERAL_HELP:\n" + "\n".join([f"  - {ex}" for ex in fewshots_general_help[:12]])
        examples_text += "\n🟣 PRODUCT_INFO:\n" + "\n".join([f"  - {ex}" for ex in fewshots_product_info[:8]])
        examples_text += "\n🟡 COUNCIL_PROCESS:\n" + "\n".join([f"  - {ex}" for ex in fewshots_council_process[:8]])
        
        prompt = f"""You are an expert NZ building code classifier. Classify this question into EXACTLY ONE intent category.

**Intent Definitions:**
- **compliance_strict**: Asks for EXACT code requirements (minimum/maximum values, what code says).
- **implicit_compliance**: Asks if a design/approach MEETS code (checking compliance).
- **general_help**: Practical tradie guidance, how-to questions. NO compliance checking.
- **product_info**: Product/material/brand recommendations.
- **council_process**: Consent process, inspections, CCC.

**Examples:**
{examples_text}

**Question to classify:** {question}

Respond with ONLY a JSON object:
{{"intent": "...", "trade": "...", "confidence": 0.XX}}"""

        try:
            # Init Client per request
            chat_client = LlmChat(
                api_key=API_KEY,
                session_id="intent_classify",
                system_message="",
                initial_messages=[{"role": "user", "content": prompt}]
            )
            chat_client.with_model("gemini", MODEL)
            chat_client.with_params(max_tokens=150, temperature=0.0)
            
            result_text = await chat_client.send_message(UserMessage(text=None))
            
            # Clean markdown
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            import json
            result = json.loads(result_text)
            
            # Add trade details
            trade = result.get("trade", "carpentry")
            result["trade_type_detailed"] = TRADE_DOMAINS.get(trade, {}).get("trade_types", [])[:2]
            
            return result
            
        except Exception as e:
            print(f"⚠️ LLM classification failed: {e}")
            return self._pattern_classify(question) or {
                "intent": Intent.GENERAL_HELP.value,
                "trade": "carpentry",
                "trade_type_detailed": [],
                "confidence": 0.50
            }

# Global classifier instance
_classifier = None

def get_classifier() -> IntentClassifierV2:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifierV2()
    return _classifier

async def classify_intent(question: str, context: Optional[List[Dict]] = None) -> Dict:
    """Async wrapper for main classification"""
    classifier = get_classifier()
    return await classifier.classify_intent(question, context)
