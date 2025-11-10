#!/usr/bin/env python3
"""
STRYDA-v2 Citation Repair Validation Test
Retest 20 queries from citation precision audit after intent router fixes
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os

# Backend URL from environment
BACKEND_URL = "https://citation-guard.preview.emergentagent.com"

# Test queries organized by category
TEST_QUERIES = {
    "clause_specific": [
        "E2/AS1 minimum apron flashing cover",
        "B1 Amendment 13 verification methods for structural design",
        "G5.3.2 hearth clearance requirements for solid fuel appliances",
        "H1 insulation R-values for Auckland climate zone",
        "F4 means of escape requirements for 2-storey residential buildings",
        "E2.3.7 cladding requirements for horizontal weatherboards",
        "B1.3.3 foundation requirements for standard soil conditions",
        "NZS 3604 clause 5.4.2 bracing requirements"
    ],
    "table_specific": [
        "NZS 3604 Table 7.1 wind zones for New Zealand regions",
        "NZS 3604 stud spacing table for standard wind zone",
        "E2/AS1 table for cladding risk scores and weathertightness",
        "NZS 3604 Table 8.3 bearer and joist sizing for decks"
    ],
    "cross_reference": [
        "difference between B1 and B2 structural compliance verification methods",
        "how does E2 weathertightness relate to H1 thermal performance at wall penetrations",
        "NZS 3604 and B1 Amendment 13 requirements for deck joist connections",
        "relationship between F7 warning systems and G5 solid fuel heating"
    ],
    "product_practical": [
        "what underlay is acceptable under corrugate metal roofing per NZMRM",
        "recommended flashing tape specifications for window installations",
        "what grade timber for external deck joists under NZS 3604",
        "minimum fixing requirements for cladding in Very High wind zone"
    ]
}

# Load previous audit results for comparison
def load_previous_audit():
    """Load previous audit results from citation_precision_audit.json"""
    try:
        with open('/app/tests/citation_precision_audit.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load previous audit: {e}")
        return None

def test_single_query(query: str, category: str) -> Dict[str, Any]:
    """Test a single query and return detailed results"""
    print(f"\n🔍 Testing: {query[:60]}...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json={
                "message": query,
                "session_id": f"citation_repair_test_{int(time.time())}"
            },
            timeout=30
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return {
                "query": query,
                "category": category,
                "error": f"HTTP {response.status_code}",
                "latency_ms": latency_ms,
                "verdict": "❌ FAIL"
            }
        
        data = response.json()
        
        # Extract response details
        answer = data.get("answer", "")
        citations = data.get("citation", [])
        
        # Determine intent from response characteristics
        intent = "unknown"
        if len(answer) > 100 and citations:
            intent = "compliance_strict"
        elif len(answer) < 50 and not citations:
            intent = "chitchat"
        else:
            intent = "general_help"
        
        # Count words
        word_count = len(answer.split())
        
        # Extract citation sources
        citation_sources = {}
        for citation in citations:
            source = citation.get("source", "Unknown")
            citation_sources[source] = citation_sources.get(source, 0) + 1
        
        # Determine verdict
        verdict = determine_verdict(
            intent=intent,
            citations_count=len(citations),
            word_count=word_count,
            latency_ms=latency_ms,
            citation_sources=citation_sources,
            category=category
        )
        
        result = {
            "query": query,
            "category": category,
            "intent": intent,
            "response": {
                "word_count": word_count,
                "answer_preview": answer[:100] + "..." if len(answer) > 100 else answer,
                "full_answer": answer,
                "citations": [
                    {
                        "source": c.get("source", "Unknown"),
                        "page": c.get("page", 0),
                        "snippet": c.get("snippet", "")[:100] if c.get("snippet") else ""
                    }
                    for c in citations
                ],
                "sources_count": citation_sources,
                "confidence_score": 0
            },
            "latency_ms": round(latency_ms, 2),
            "verdict": verdict,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"   Intent: {intent}, Citations: {len(citations)}, Words: {word_count}, Latency: {latency_ms:.0f}ms")
        print(f"   Verdict: {verdict}")
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "query": query,
            "category": category,
            "error": "Timeout (>30s)",
            "latency_ms": 30000,
            "verdict": "❌ FAIL"
        }
    except Exception as e:
        return {
            "query": query,
            "category": category,
            "error": str(e),
            "latency_ms": (time.time() - start_time) * 1000,
            "verdict": "❌ FAIL"
        }

def determine_verdict(intent: str, citations_count: int, word_count: int, 
                     latency_ms: float, citation_sources: Dict[str, int], 
                     category: str) -> str:
    """Determine if query passes, partially passes, or fails"""
    
    # Check for critical failures
    if intent == "chitchat" and category in ["clause_specific", "cross_reference"]:
        return "❌ FAIL"
    
    if citations_count == 0 and category in ["clause_specific", "table_specific"]:
        return "❌ FAIL"
    
    if latency_ms > 15000:
        return "❌ FAIL"
    
    # Check for "Unknown" sources
    has_unknown_sources = "Unknown" in citation_sources
    
    # Check for pass criteria
    pass_criteria = {
        "intent_correct": intent in ["compliance_strict", "general_help"],
        "has_citations": citations_count >= 1,
        "sufficient_words": word_count >= 80,
        "good_latency": latency_ms < 10000,
        "known_sources": not has_unknown_sources
    }
    
    # Full pass requires all criteria
    if all(pass_criteria.values()):
        return "✅ PASS"
    
    # Partial pass if most criteria met
    met_count = sum(pass_criteria.values())
    if met_count >= 3:
        return "⚠️ PARTIAL"
    
    return "❌ FAIL"

def run_citation_repair_tests():
    """Run all 20 queries and generate comparison report"""
    
    print("=" * 80)
    print("STRYDA-v2 CITATION REPAIR VALIDATION")
    print("Testing 20 queries after intent router fixes")
    print("=" * 80)
    
    # Load previous audit for comparison
    previous_audit = load_previous_audit()
    previous_results = {}
    if previous_audit:
        for result in previous_audit.get("detailed_results", []):
            previous_results[result["query"]] = result
    
    # Run all tests
    all_results = []
    query_number = 1
    
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'=' * 80}")
        print(f"Category: {category.upper().replace('_', ' ')}")
        print(f"{'=' * 80}")
        
        for query in queries:
            result = test_single_query(query, category)
            result["query_number"] = query_number
            all_results.append(result)
            query_number += 1
            
            # Brief pause between requests
            time.sleep(0.5)
    
    # Calculate statistics
    pass_count = sum(1 for r in all_results if r["verdict"] == "✅ PASS")
    partial_count = sum(1 for r in all_results if r["verdict"] == "⚠️ PARTIAL")
    fail_count = sum(1 for r in all_results if r["verdict"] == "❌ FAIL")
    
    avg_latency = sum(r.get("latency_ms", 0) for r in all_results) / len(all_results)
    
    # Count citation accuracy (non-Unknown sources)
    total_citations = 0
    known_citations = 0
    for r in all_results:
        if "response" in r:
            sources = r["response"].get("sources_count", {})
            for source, count in sources.items():
                total_citations += count
                if source != "Unknown":
                    known_citations += count
    
    citation_accuracy = (known_citations / total_citations * 100) if total_citations > 0 else 0
    
    # Generate comparison report
    generate_comparison_report(all_results, previous_results, {
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "pass_rate": pass_count / len(all_results) * 100,
        "avg_latency_ms": avg_latency,
        "citation_accuracy": citation_accuracy
    })
    
    # Save JSON results
    save_json_results(all_results, {
        "pass": pass_count,
        "partial": partial_count,
        "fail": fail_count,
        "avg_latency_ms": avg_latency
    })
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ PASS: {pass_count}/20 ({pass_count/20*100:.1f}%)")
    print(f"⚠️ PARTIAL: {partial_count}/20 ({partial_count/20*100:.1f}%)")
    print(f"❌ FAIL: {fail_count}/20 ({fail_count/20*100:.1f}%)")
    print(f"Average Latency: {avg_latency:.0f}ms")
    print(f"Citation Accuracy: {citation_accuracy:.1f}%")
    
    if previous_audit:
        prev_pass = previous_audit["summary_statistics"]["pass_count"]
        prev_latency = previous_audit["summary_statistics"]["average_latency_ms"]
        print(f"\nImprovement: {pass_count - prev_pass:+d} passes, {avg_latency - prev_latency:+.0f}ms latency")
    
    print("=" * 80)
    
    return all_results

def generate_comparison_report(results: List[Dict], previous_results: Dict, stats: Dict):
    """Generate markdown comparison report"""
    
    report = f"""# Citation Repair Validation Report

## Test Information

- **Test Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Backend URL**: {BACKEND_URL}
- **Total Queries**: 20
- **Fixes Applied**: Intent router clause patterns, comparative query detection

## Before vs After Comparison

| Query # | Query | Before Intent | After Intent | Before Citations | After Citations | Before Verdict | After Verdict |
|---------|-------|---------------|--------------|------------------|-----------------|----------------|---------------|
"""
    
    for result in results:
        query = result["query"]
        query_num = result["query_number"]
        
        # Get previous result
        prev = previous_results.get(query, {})
        prev_intent = prev.get("intent", "N/A")
        prev_citations = len(prev.get("response", {}).get("citations", []))
        prev_verdict = prev.get("verdict", "N/A")
        
        # Current result
        curr_intent = result.get("intent", "N/A")
        curr_citations = len(result.get("response", {}).get("citations", []))
        curr_verdict = result.get("verdict", "N/A")
        
        # Determine if fixed
        is_fixed = ""
        if prev_verdict in ["❌ FAIL", "⚠️ PARTIAL"] and curr_verdict == "✅ PASS":
            is_fixed = " ✅ FIXED"
        elif prev_verdict == "❌ FAIL" and curr_verdict == "⚠️ PARTIAL":
            is_fixed = " 🔧 IMPROVED"
        
        report += f"| {query_num} | {query[:40]}... | {prev_intent} | {curr_intent} | {prev_citations} | {curr_citations} | {prev_verdict} | {curr_verdict}{is_fixed} |\n"
    
    report += f"""
## Summary Statistics

### Before Fixes (Previous Audit)
- **Pass Rate**: 2/20 (10.0%)
- **Avg Latency**: 9,347ms
- **Citation Accuracy**: 65.0%

### After Fixes (Current Test)
- **Pass Rate**: {stats['pass_count']}/20 ({stats['pass_rate']:.1f}%)
- **Avg Latency**: {stats['avg_latency_ms']:.0f}ms
- **Citation Accuracy**: {stats['citation_accuracy']:.1f}%

### Improvement
- **Pass Rate Change**: {stats['pass_count'] - 2:+d} ({stats['pass_rate'] - 10.0:+.1f}%)
- **Latency Change**: {stats['avg_latency_ms'] - 9347:+.0f}ms
- **Citation Accuracy Change**: {stats['citation_accuracy'] - 65.0:+.1f}%

## Detailed Results by Category

"""
    
    # Group by category
    by_category = {}
    for result in results:
        cat = result["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(result)
    
    for category, cat_results in by_category.items():
        report += f"### {category.upper().replace('_', ' ')}\n\n"
        
        for result in cat_results:
            query = result["query"]
            verdict = result["verdict"]
            intent = result.get("intent", "unknown")
            citations = len(result.get("response", {}).get("citations", []))
            word_count = result.get("response", {}).get("word_count", 0)
            latency = result.get("latency_ms", 0)
            
            report += f"**Query {result['query_number']}**: {query}\n"
            report += f"- **Verdict**: {verdict}\n"
            report += f"- **Intent**: {intent}\n"
            report += f"- **Citations**: {citations}\n"
            report += f"- **Word Count**: {word_count}\n"
            report += f"- **Latency**: {latency:.0f}ms\n"
            
            # Show citation sources
            if "response" in result:
                sources = result["response"].get("sources_count", {})
                if sources:
                    report += f"- **Sources**: {', '.join(f'{k} ({v})' for k, v in sources.items())}\n"
            
            report += "\n"
    
    report += """## Sample Fixed Queries

"""
    
    # Find top 3 fixed queries
    fixed_queries = []
    for result in results:
        query = result["query"]
        prev = previous_results.get(query, {})
        if prev.get("verdict") == "❌ FAIL" and result["verdict"] in ["✅ PASS", "⚠️ PARTIAL"]:
            fixed_queries.append((result, prev))
    
    for i, (curr, prev) in enumerate(fixed_queries[:3], 1):
        report += f"### Query {curr['query_number']}: \"{curr['query']}\"\n\n"
        report += f"**Before**: intent={prev.get('intent', 'N/A')}, "
        report += f"answer=\"{prev.get('response', {}).get('answer_preview', 'N/A')}\", "
        report += f"citations={len(prev.get('response', {}).get('citations', []))}\n\n"
        report += f"**After**: intent={curr.get('intent', 'N/A')}, "
        report += f"answer=\"{curr.get('response', {}).get('answer_preview', 'N/A')}\", "
        report += f"citations={len(curr.get('response', {}).get('citations', []))}\n\n"
    
    report += """## Citation Source Mapping

"""
    
    # Check for Unknown sources
    unknown_count = 0
    known_sources = set()
    for result in results:
        if "response" in result:
            sources = result["response"].get("sources_count", {})
            for source in sources:
                if source == "Unknown":
                    unknown_count += sources[source]
                else:
                    known_sources.add(source)
    
    if unknown_count == 0:
        report += "✅ No 'Unknown' sources found - all citations properly mapped\n\n"
    else:
        report += f"❌ {unknown_count} citations still showing 'Unknown' source\n\n"
    
    if known_sources:
        report += "**Known Sources Found**:\n"
        for source in sorted(known_sources):
            report += f"- {source}\n"
    
    report += """
## Conclusion

"""
    
    if stats['pass_rate'] >= 80:
        report += "✅ **EXCELLENT**: System now meets expected citation accuracy standards (≥80% pass rate)\n"
    elif stats['pass_rate'] >= 60:
        report += "⚠️ **GOOD PROGRESS**: Significant improvement but not yet at target (60-80% pass rate)\n"
    elif stats['pass_rate'] >= 40:
        report += "⚠️ **MODERATE IMPROVEMENT**: Some fixes working but more work needed (40-60% pass rate)\n"
    else:
        report += "❌ **INSUFFICIENT**: Intent router fixes not achieving expected results (<40% pass rate)\n"
    
    # Save report
    with open('/app/tests/CITATION_REPAIR_REPORT.md', 'w') as f:
        f.write(report)
    
    print("\n✅ Comparison report saved to /app/tests/CITATION_REPAIR_REPORT.md")

def save_json_results(results: List[Dict], summary: Dict):
    """Save JSON results file"""
    
    output = {
        "test_date": datetime.utcnow().isoformat(),
        "fixes_applied": [
            "intent_router_clause_patterns",
            "comparative_query_detection"
        ],
        "before": {
            "pass": 2,
            "partial": 11,
            "fail": 7,
            "avg_latency_ms": 9347
        },
        "after": {
            "pass": summary["pass"],
            "partial": summary["partial"],
            "fail": summary["fail"],
            "avg_latency_ms": round(summary["avg_latency_ms"], 2)
        },
        "improvement_pct": ((summary["pass"] - 2) / 2 * 100) if summary["pass"] > 2 else 0,
        "results": results
    }
    
    with open('/app/tests/citation_repair_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("✅ JSON results saved to /app/tests/citation_repair_results.json")

if __name__ == "__main__":
    run_citation_repair_tests()
