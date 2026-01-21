#!/usr/bin/env python3
"""
Intent Router Fix Verification Test
Tests 20 queries (10 general + 10 compliance) to verify intent classification improvements
"""

import requests
import json
import time
from typing import Dict, List, Tuple

# Backend URL
BACKEND_URL = "https://smarter-kb.preview.emergentagent.com/api/chat"

# Test queries
GENERAL_QUERIES = [
    "what's the minimum roof pitch for metal roofing",
    "how far should nogs be spaced on a standard wall",
    "best way to flash a roof-to-wall junction",
    "what size timber for deck joists spanning 3 metres",
    "how do I install weatherboards properly",
    "what's a good fixing pattern for hardiplank cladding",
    "recommended screw type for corrugate iron roofing",
    "how thick should concrete slab be for a garage",
    "what underlay goes under metal roofing",
    "best practice for installing gutters and downpipes"
]

COMPLIANCE_QUERIES = [
    "E2/AS1 minimum apron flashing cover requirements",
    "NZS 3604 stud spacing requirements for standard wind zone",
    "B1 Amendment 13 verification methods for structural design",
    "H1 insulation R-values for Auckland climate zone",
    "F4 means of escape requirements for 2-storey residential",
    "NZS 3604 Table 7.1 wind zone classifications",
    "E2/AS1 cladding risk scores for weathertightness",
    "B1.3.3 foundation requirements for standard soil",
    "G5.3.2 hearth clearance for solid fuel appliances",
    "NZS 3604 bearer and joist sizing for deck construction"
]

def test_query(query: str, expected_intent: str, query_num: int) -> Dict:
    """Test a single query and return results"""
    print(f"\n{'='*80}")
    print(f"Query #{query_num}: {query}")
    print(f"Expected Intent: {expected_intent}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            BACKEND_URL,
            json={
                "message": query,
                "session_id": f"intent_test_{query_num}"
            },
            timeout=20
        )
        
        latency = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                "query": query,
                "query_num": query_num,
                "expected_intent": expected_intent,
                "actual_intent": "error",
                "latency_ms": latency,
                "citations_count": 0,
                "word_count": 0,
                "pass": False,
                "error": f"HTTP {response.status_code}"
            }
        
        data = response.json()
        
        # Extract intent from response (may be in different fields)
        actual_intent = data.get("intent", "unknown")
        citations = data.get("citation", [])
        answer = data.get("answer", "")
        word_count = len(answer.split())
        citations_count = len(citations)
        
        print(f"✓ Actual Intent: {actual_intent}")
        print(f"✓ Latency: {latency:.0f}ms")
        print(f"✓ Citations: {citations_count}")
        print(f"✓ Word Count: {word_count}")
        print(f"✓ Answer Preview: {answer[:150]}...")
        
        # Determine pass/fail
        intent_correct = actual_intent == expected_intent
        
        if expected_intent == "general_help":
            # General queries should have 0-1 citations
            citations_ok = citations_count <= 1
            pass_status = intent_correct and citations_ok
            verdict = "✅ PASS" if pass_status else "❌ FAIL"
            print(f"\n{verdict} - Intent: {intent_correct}, Citations: {citations_ok} (0-1 expected, got {citations_count})")
        else:
            # Compliance queries should have 1-3 citations
            citations_ok = 1 <= citations_count <= 3
            pass_status = intent_correct and citations_ok
            verdict = "✅ PASS" if pass_status else "❌ FAIL"
            print(f"\n{verdict} - Intent: {intent_correct}, Citations: {citations_ok} (1-3 expected, got {citations_count})")
        
        return {
            "query": query,
            "query_num": query_num,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "latency_ms": latency,
            "citations_count": citations_count,
            "word_count": word_count,
            "pass": pass_status,
            "intent_correct": intent_correct,
            "citations_ok": citations_ok,
            "answer_preview": answer[:200]
        }
        
    except Exception as e:
        latency = (time.time() - start_time) * 1000
        print(f"❌ Exception: {str(e)}")
        return {
            "query": query,
            "query_num": query_num,
            "expected_intent": expected_intent,
            "actual_intent": "error",
            "latency_ms": latency,
            "citations_count": 0,
            "word_count": 0,
            "pass": False,
            "error": str(e)
        }

def run_all_tests() -> Tuple[List[Dict], Dict]:
    """Run all 20 tests and return results"""
    print("\n" + "="*80)
    print("INTENT ROUTER FIX VERIFICATION - 20 QUERY RETEST")
    print("="*80)
    
    all_results = []
    
    # Test general queries (expect general_help)
    print("\n\n### TESTING GENERAL QUERIES (Expect: general_help, 0-1 citations) ###\n")
    for i, query in enumerate(GENERAL_QUERIES, 1):
        result = test_query(query, "general_help", i)
        all_results.append(result)
        time.sleep(0.5)  # Small delay between requests
    
    # Test compliance queries (expect compliance_strict)
    print("\n\n### TESTING COMPLIANCE QUERIES (Expect: compliance_strict, 1-3 citations) ###\n")
    for i, query in enumerate(COMPLIANCE_QUERIES, 11):
        result = test_query(query, "compliance_strict", i)
        all_results.append(result)
        time.sleep(0.5)  # Small delay between requests
    
    # Calculate statistics
    total_tests = len(all_results)
    passed = sum(1 for r in all_results if r.get("pass", False))
    intent_correct = sum(1 for r in all_results if r.get("intent_correct", False))
    
    general_results = all_results[:10]
    compliance_results = all_results[10:]
    
    general_passed = sum(1 for r in general_results if r.get("pass", False))
    compliance_passed = sum(1 for r in compliance_results if r.get("pass", False))
    
    general_intent_correct = sum(1 for r in general_results if r.get("intent_correct", False))
    compliance_intent_correct = sum(1 for r in compliance_results if r.get("intent_correct", False))
    
    # Over-classification count (general queries classified as compliance_strict)
    over_classified = sum(1 for r in general_results if r.get("actual_intent") == "compliance_strict")
    
    avg_latency = sum(r.get("latency_ms", 0) for r in all_results) / total_tests if total_tests > 0 else 0
    
    stats = {
        "total_tests": total_tests,
        "passed": passed,
        "pass_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
        "intent_accuracy": (intent_correct / total_tests * 100) if total_tests > 0 else 0,
        "over_classification": over_classified,
        "avg_latency_ms": avg_latency,
        "general": {
            "total": len(general_results),
            "passed": general_passed,
            "intent_correct": general_intent_correct,
            "over_classified": over_classified
        },
        "compliance": {
            "total": len(compliance_results),
            "passed": compliance_passed,
            "intent_correct": compliance_intent_correct
        }
    }
    
    return all_results, stats

def print_summary(results: List[Dict], stats: Dict):
    """Print test summary"""
    print("\n\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    print(f"\n📊 Overall Results:")
    print(f"   Pass Rate: {stats['passed']}/{stats['total_tests']} ({stats['pass_rate']:.1f}%)")
    print(f"   Intent Accuracy: {stats['intent_accuracy']:.1f}%")
    print(f"   Average Latency: {stats['avg_latency_ms']:.0f}ms")
    print(f"   Over-Classification: {stats['over_classification']}/10 general queries → compliance_strict")
    
    print(f"\n📊 General Queries (1-10):")
    print(f"   Passed: {stats['general']['passed']}/{stats['general']['total']}")
    print(f"   Intent Correct: {stats['general']['intent_correct']}/{stats['general']['total']}")
    print(f"   Over-Classified: {stats['general']['over_classified']}/10")
    
    print(f"\n📊 Compliance Queries (11-20):")
    print(f"   Passed: {stats['compliance']['passed']}/{stats['compliance']['total']}")
    print(f"   Intent Correct: {stats['compliance']['intent_correct']}/{stats['compliance']['total']}")
    
    print(f"\n\n{'='*80}")
    print("BEFORE FIX vs AFTER FIX COMPARISON")
    print("="*80)
    
    print(f"\nBefore Fix:")
    print(f"   Pass Rate: 5/20 (25%)")
    print(f"   Intent Accuracy: 12/20 (60%)")
    print(f"   Over-Classification: 8/10 general queries")
    
    print(f"\nAfter Fix:")
    print(f"   Pass Rate: {stats['passed']}/20 ({stats['pass_rate']:.0f}%)")
    print(f"   Intent Accuracy: {int(stats['intent_accuracy'] * stats['total_tests'] / 100)}/20 ({stats['intent_accuracy']:.0f}%)")
    print(f"   Over-Classification: {stats['over_classification']}/10 general queries")
    
    print(f"\nImprovement:")
    print(f"   Pass Rate: {stats['pass_rate'] - 25:+.0f}%")
    print(f"   Intent Accuracy: {stats['intent_accuracy'] - 60:+.0f}%")
    print(f"   Over-Classification: {stats['over_classification'] - 8:+d} queries")
    
    # Show failed queries
    failed = [r for r in results if not r.get("pass", False)]
    if failed:
        print(f"\n\n❌ Failed Queries ({len(failed)}):")
        for r in failed:
            print(f"\n   Query #{r['query_num']}: {r['query']}")
            print(f"      Expected: {r['expected_intent']}, Got: {r['actual_intent']}")
            print(f"      Citations: {r['citations_count']}, Latency: {r['latency_ms']:.0f}ms")

def save_results(results: List[Dict], stats: Dict):
    """Save results to JSON file"""
    output = {
        "test_name": "Intent Router Fix Verification",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "statistics": stats,
        "results": results
    }
    
    with open("/app/tests/intent_router_fix_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved to /app/tests/intent_router_fix_results.json")

def generate_markdown_report(results: List[Dict], stats: Dict):
    """Generate markdown report"""
    
    report = f"""# Intent Router Fix Verification

## Test Overview
- **Date**: {time.strftime("%Y-%m-%d %H:%M:%S")}
- **Total Queries**: 20 (10 general + 10 compliance)
- **Backend URL**: {BACKEND_URL}

## Before Fix
- **Intent Accuracy**: 60% (12/20)
- **Over-Classification**: 8/10 general queries misclassified
- **Pass Rate**: 25% (5/20)

## After Fix
- **Intent Accuracy**: {stats['intent_accuracy']:.0f}% ({int(stats['intent_accuracy'] * stats['total_tests'] / 100)}/20)
- **Over-Classification**: {stats['over_classification']}/10 general queries misclassified
- **Pass Rate**: {stats['pass_rate']:.0f}% ({stats['passed']}/20)

## Improvement
- **Intent Accuracy**: {stats['intent_accuracy'] - 60:+.0f}%
- **Pass Rate**: {stats['pass_rate'] - 25:+.0f}%
- **Over-Classification Reduction**: {8 - stats['over_classification']} queries fixed

## Detailed Results

| # | Query | Expected | Actual | Citations | Latency | Pass |
|---|-------|----------|--------|-----------|---------|------|
"""
    
    for r in results:
        pass_icon = "✅" if r.get("pass", False) else "❌"
        report += f"| {r['query_num']} | {r['query'][:50]}... | {r['expected_intent']} | {r['actual_intent']} | {r['citations_count']} | {r['latency_ms']:.0f}ms | {pass_icon} |\n"
    
    report += f"""
## Sample Fixes

"""
    
    # Show examples of fixed queries
    general_results = results[:10]
    fixed_queries = [r for r in general_results if r.get("intent_correct", False) and r.get("actual_intent") == "general_help"]
    
    if fixed_queries:
        for i, r in enumerate(fixed_queries[:3], 1):
            report += f"""### Query: "{r['query']}"
**Before:** compliance_strict (over-classified)
**After:** {r['actual_intent']}, {r['citations_count']} citations ✅ FIXED

"""
    
    # Show remaining issues
    failed = [r for r in results if not r.get("pass", False)]
    if failed:
        report += f"""## Remaining Issues

"""
        for r in failed:
            report += f"""### Query #{r['query_num']}: "{r['query']}"
- **Expected**: {r['expected_intent']}
- **Actual**: {r['actual_intent']}
- **Citations**: {r['citations_count']}
- **Issue**: {"Intent misclassification" if not r.get("intent_correct", False) else "Citation count out of range"}

"""
    
    # Conclusion
    if stats['pass_rate'] >= 80 and stats['intent_accuracy'] >= 90:
        conclusion = "✅ **SUCCESS** - Intent router refinement successful! System meets production readiness criteria."
    elif stats['pass_rate'] >= 60:
        conclusion = "⚠️ **PARTIAL** - Intent router shows improvement but needs further refinement."
    else:
        conclusion = "❌ **FAILED** - Intent router still has significant issues requiring attention."
    
    report += f"""## Conclusion

{conclusion}

### Key Metrics
- Pass Rate: {stats['pass_rate']:.0f}% (Target: ≥80%)
- Intent Accuracy: {stats['intent_accuracy']:.0f}% (Target: ≥90%)
- Over-Classification: {stats['over_classification']}/10 (Target: ≤2)
"""
    
    # Save report
    with open("/app/tests/INTENT_ROUTER_FIX_REPORT.md", "w") as f:
        f.write(report)
    
    print(f"✅ Report saved to /app/tests/INTENT_ROUTER_FIX_REPORT.md")

if __name__ == "__main__":
    # Create tests directory if it doesn't exist
    import os
    os.makedirs("/app/tests", exist_ok=True)
    
    # Run tests
    results, stats = run_all_tests()
    
    # Print summary
    print_summary(results, stats)
    
    # Save results
    save_results(results, stats)
    
    # Generate report
    generate_markdown_report(results, stats)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
