"""
STRYDA Golden Test Set for Tier-1 Source Regression
Comprehensive testing for ranking bias and citation accuracy
"""

import os
import hashlib
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configurable bias parameters from environment
RETRIEVAL_BIAS_A13 = float(os.getenv("RETRIEVAL_BIAS_A13", "1.50"))
RETRIEVAL_DEBIAS_B1 = float(os.getenv("RETRIEVAL_DEBIAS_B1", "0.85"))
INTENT_HIGH_CONF = float(os.getenv("INTENT_HIGH_CONF", "0.70"))
AMEND_REGEX = os.getenv("AMEND_REGEX", r"amend(ment)?\s*13|b1\s*a?m?e?n?d?ment|latest\s+b1")

# Golden test set with expected citation signatures
GOLDEN_TESTS = [
    # A) Amendment-targeted (expect ≥1 B1 Amendment 13 citation)
    {
        "group": "amendment",
        "query": "B1 Amendment 13 verification methods for structural design",
        "expected_sources": ["B1 Amendment 13"],
        "expected_count": {"B1 Amendment 13": 1},
        "intent_expected": "compliance_strict"
    },
    {
        "group": "amendment", 
        "query": "latest B1 changes that affect deck or balcony supports",
        "expected_sources": ["B1 Amendment 13"],
        "expected_count": {"B1 Amendment 13": 1},
        "intent_expected": "compliance_strict"
    },
    {
        "group": "amendment",
        "query": "how did amendment 13 update structural verification?",
        "expected_sources": ["B1 Amendment 13"],
        "expected_count": {"B1 Amendment 13": 1}, 
        "intent_expected": "compliance_strict"
    },
    
    # B) NZS 3604 timber (expect ≥2 NZS 3604:2011 citations)
    {
        "group": "timber",
        "query": "minimum bearing requirements for beams",
        "expected_sources": ["NZS 3604:2011"],
        "expected_count": {"NZS 3604:2011": 2},
        "intent_expected": "compliance_strict"
    },
    {
        "group": "timber",
        "query": "stud spacing for 2.4 m wall in standard wind zone", 
        "expected_sources": ["NZS 3604:2011"],
        "expected_count": {"NZS 3604:2011": 2},
        "intent_expected": "compliance_strict"
    },
    {
        "group": "timber",
        "query": "lintel sizes over 1.8 m opening, single-storey",
        "expected_sources": ["NZS 3604:2011"],
        "expected_count": {"NZS 3604:2011": 2},
        "intent_expected": "compliance_strict"
    },
    
    # C) E2/AS1 moisture (expect ≥2 E2/AS1 citations)
    {
        "group": "moisture",
        "query": "minimum apron flashing cover",
        "expected_sources": ["E2/AS1"],
        "expected_count": {"E2/AS1": 2},
        "intent_expected": "compliance_strict"
    },
    {
        "group": "moisture",
        "query": "weathertightness risk factors for cladding intersections",
        "expected_sources": ["E2/AS1"], 
        "expected_count": {"E2/AS1": 2},
        "intent_expected": "compliance_strict"
    },
    
    # D) B1/AS1 legacy (expect citations when specifically requested)
    {
        "group": "legacy",
        "query": "show B1/AS1 clause references for bracing calculation examples",
        "expected_sources": ["B1/AS1"],
        "expected_count": {"B1/AS1": 1},
        "intent_expected": "compliance_strict"
    }
]

def run_golden_test(test_case: Dict, chat_function) -> Dict[str, Any]:
    """Run a single golden test case"""
    query = test_case["query"]
    expected_sources = test_case["expected_sources"]
    expected_counts = test_case["expected_count"]
    
    try:
        # Generate query hash for tracking
        query_hash = hashlib.md5(query.encode()).hexdigest()[:12]
        
        # Call the chat function (same pipeline as app)
        result = chat_function(query, f"golden_test_{query_hash}")
        
        # Extract test metrics
        intent = result.get("intent", "unknown")
        citations = result.get("citations", [])
        tier1_hit = result.get("tier1_hit", False)
        source_bias = result.get("source_bias", {})
        
        # Analyze citation sources
        citation_sources = {}
        for cite in citations:
            source = cite.get("source", "Unknown")
            citation_sources[source] = citation_sources.get(source, 0) + 1
        
        # Check expectations
        success_criteria = []
        
        # Intent check
        intent_pass = intent == test_case["intent_expected"]
        success_criteria.append(("intent", intent_pass, f"Expected: {test_case['intent_expected']}, Got: {intent}"))
        
        # Source count check
        for expected_source, min_count in expected_counts.items():
            actual_count = citation_sources.get(expected_source, 0)
            count_pass = actual_count >= min_count
            success_criteria.append((f"{expected_source}_count", count_pass, f"Expected: ≥{min_count}, Got: {actual_count}"))
        
        # Overall pass/fail
        overall_pass = all(passed for _, passed, _ in success_criteria)
        
        return {
            "query": query,
            "query_hash": query_hash,
            "group": test_case["group"],
            "intent": intent,
            "citations": citations,
            "citation_sources": citation_sources,
            "tier1_hit": tier1_hit,
            "source_bias_applied": source_bias,
            "success_criteria": success_criteria,
            "overall_pass": overall_pass,
            "expected": test_case
        }
        
    except Exception as e:
        return {
            "query": query,
            "group": test_case["group"],
            "error": str(e),
            "overall_pass": False
        }

def run_comprehensive_selftest(chat_function) -> Dict[str, Any]:
    """Run complete golden test regression"""
    print("🧪 RUNNING COMPREHENSIVE GOLDEN TEST REGRESSION")
    print("=" * 70)
    
    # Log boot configuration
    boot_config = {
        "retrieval_bias_a13": RETRIEVAL_BIAS_A13,
        "retrieval_debias_b1": RETRIEVAL_DEBIAS_B1,
        "intent_high_conf": INTENT_HIGH_CONF,
        "amend_regex": AMEND_REGEX
    }
    
    if os.getenv("ENABLE_TELEMETRY") == "true":
        print(f"[telemetry] boot_config {boot_config}")
    
    results = []
    passed = 0
    
    for i, test_case in enumerate(GOLDEN_TESTS, 1):
        print(f"\n📋 Test {i}/{len(GOLDEN_TESTS)} ({test_case['group']}): {test_case['query'][:50]}...")
        
        test_result = run_golden_test(test_case, chat_function)
        results.append(test_result)
        
        if test_result.get("overall_pass", False):
            passed += 1
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")
            
            # Show failure details
            if "success_criteria" in test_result:
                for criterion, passed_check, detail in test_result["success_criteria"]:
                    if not passed_check:
                        print(f"      • {criterion}: {detail}")
    
    # Generate summary
    summary = {
        "ok": passed == len(GOLDEN_TESTS),
        "version": "1.4.0",
        "boot_config": boot_config,
        "tests_total": len(GOLDEN_TESTS),
        "tests_passed": passed,
        "tests_failed": len(GOLDEN_TESTS) - passed,
        "pass_rate": (passed / len(GOLDEN_TESTS)) * 100,
        "failures": [r for r in results if not r.get("overall_pass", False)],
        "results": results
    }
    
    print(f"\n📊 GOLDEN TEST SUMMARY:")
    print(f"   Tests passed: {passed}/{len(GOLDEN_TESTS)}")
    print(f"   Pass rate: {summary['pass_rate']:.1f}%")
    print(f"   Status: {'✅ ALL PASS' if summary['ok'] else '❌ SOME FAILURES'}")
    
    return summary

# Export for use in admin endpoint
def get_golden_test_suite():
    return GOLDEN_TESTS, run_comprehensive_selftest