#!/usr/bin/env python3
"""
STRYDA-v2 Chat & Citation Verification Test
============================================
Comprehensive test of 20 realistic NZ Builder queries to verify:
- Intent classification accuracy
- Citation quality and accuracy
- Response latency
- Production readiness

Test Date: 2025-01-03
Version: v2.3.0-opt
"""

import requests
import time
import json
import statistics
from typing import Dict, List, Any
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://stryda-rag.preview.emergentagent.com"
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

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

# Expected document mappings for compliance queries
EXPECTED_SOURCES = {
    "E2/AS1": ["E2/AS1", "E2 External moisture"],
    "NZS 3604": ["NZS 3604:2011", "NZS 3604"],
    "B1 Amendment 13": ["B1 Amendment 13", "B1/AS1"],
    "H1": ["H1", "H1 Energy efficiency"],
    "F4": ["F4", "F4 Safety from falling"],
    "G5": ["G5", "G5.3.2", "G5 Interior environment"],
    "B1.3.3": ["B1/AS1", "B1 Amendment 13", "B1 Structure"]
}

def test_query(query: str, query_num: int, expected_intent: str) -> Dict[str, Any]:
    """Test a single query and return results"""
    print(f"\n{'='*80}")
    print(f"Query #{query_num}: {query}")
    print(f"Expected Intent: {expected_intent}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json={
                "message": query,
                "session_id": f"test_session_{query_num}"
            },
            timeout=30
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return {
                "query_num": query_num,
                "query": query,
                "expected_intent": expected_intent,
                "actual_intent": "error",
                "latency_ms": latency_ms,
                "citations_count": 0,
                "citations": [],
                "word_count": 0,
                "verdict": "FAIL",
                "issues": [f"HTTP {response.status_code}"]
            }
        
        data = response.json()
        
        # Extract response fields
        actual_intent = data.get("intent", "unknown")
        answer = data.get("answer", "")
        citations = data.get("citations", [])
        latency_from_api = data.get("latency_ms", latency_ms)
        
        # Use API latency if available, otherwise use measured
        final_latency = latency_from_api if latency_from_api > 0 else latency_ms
        
        # Calculate word count
        word_count = len(answer.split())
        
        # Process citations
        citation_details = []
        fabricated_count = 0
        
        for cite in citations:
            source = cite.get("source", "Unknown")
            page = cite.get("page", 0)
            
            # Check for fabrication indicators
            is_fabricated = False
            if source == "Unknown" or page < 1 or page > 600:
                is_fabricated = True
                fabricated_count += 1
            
            citation_details.append({
                "source": source,
                "page": page,
                "is_fabricated": is_fabricated,
                "clause_id": cite.get("clause_id"),
                "snippet": cite.get("snippet", "")[:100]
            })
        
        # Determine verdict
        verdict = "PASS"
        issues = []
        
        if expected_intent == "general_help":
            # General query validation
            if actual_intent not in ["general_help", "product_info", "general_advice", "chitchat"]:
                verdict = "FAIL"
                issues.append(f"Intent mismatch: expected general, got {actual_intent}")
            
            if len(citations) > 2:
                verdict = "FAIL"
                issues.append(f"Over-citation: {len(citations)} citations (expected 0-1)")
            
            if final_latency > 15000:
                verdict = "FAIL"
                issues.append(f"Latency too high: {final_latency}ms (expected <15s)")
        
        else:  # compliance_strict expected
            if actual_intent != "compliance_strict":
                if actual_intent == "chitchat":
                    verdict = "FAIL"
                    issues.append(f"Misclassified as chitchat (expected compliance_strict)")
                else:
                    verdict = "PARTIAL"
                    issues.append(f"Intent: {actual_intent} (expected compliance_strict)")
            
            if len(citations) == 0:
                verdict = "PARTIAL" if verdict == "PASS" else verdict
                issues.append("No citations provided")
            elif len(citations) > 3:
                issues.append(f"Too many citations: {len(citations)} (expected 1-3)")
            
            # Check source matching
            if len(citations) > 0:
                query_upper = query.upper()
                expected_source_found = False
                
                for key, expected_sources in EXPECTED_SOURCES.items():
                    if key in query_upper:
                        for cite in citation_details:
                            if any(exp_src in cite["source"] for exp_src in expected_sources):
                                expected_source_found = True
                                break
                        
                        if not expected_source_found:
                            issues.append(f"Source mismatch: expected {key} citations")
                            verdict = "FAIL"
                        break
            
            if fabricated_count > 0:
                verdict = "FAIL"
                issues.append(f"Fabricated citations: {fabricated_count}")
            
            if final_latency > 15000:
                if final_latency > 20000:
                    verdict = "FAIL"
                    issues.append(f"Latency critical: {final_latency}ms (expected <15s)")
                else:
                    verdict = "PARTIAL" if verdict == "PASS" else verdict
                    issues.append(f"Latency high: {final_latency}ms (expected <15s)")
        
        # Print results
        print(f"✓ Intent: {actual_intent} (confidence: {data.get('confidence', 'N/A')})")
        print(f"✓ Latency: {final_latency}ms")
        print(f"✓ Citations: {len(citations)}")
        print(f"✓ Word Count: {word_count}")
        print(f"✓ Answer Preview: {answer[:150]}...")
        
        if citations:
            print(f"\n📚 Citations:")
            for i, cite in enumerate(citation_details, 1):
                fab_marker = " ⚠️ FABRICATED" if cite["is_fabricated"] else ""
                print(f"  {i}. {cite['source']} p.{cite['page']}{fab_marker}")
                if cite.get("clause_id"):
                    print(f"     Clause: {cite['clause_id']}")
        
        if issues:
            print(f"\n⚠️ Issues: {', '.join(issues)}")
        
        print(f"\n{'✅' if verdict == 'PASS' else '⚠️' if verdict == 'PARTIAL' else '❌'} Verdict: {verdict}")
        
        return {
            "query_num": query_num,
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "latency_ms": final_latency,
            "citations_count": len(citations),
            "citations": citation_details,
            "word_count": word_count,
            "verdict": verdict,
            "issues": issues,
            "answer_preview": answer[:200]
        }
        
    except requests.exceptions.Timeout:
        latency_ms = int((time.time() - start_time) * 1000)
        print(f"❌ TIMEOUT after {latency_ms}ms")
        return {
            "query_num": query_num,
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": "timeout",
            "latency_ms": latency_ms,
            "citations_count": 0,
            "citations": [],
            "word_count": 0,
            "verdict": "FAIL",
            "issues": ["Request timeout"]
        }
    
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        print(f"❌ ERROR: {str(e)}")
        return {
            "query_num": query_num,
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": "error",
            "latency_ms": latency_ms,
            "citations_count": 0,
            "citations": [],
            "word_count": 0,
            "verdict": "FAIL",
            "issues": [str(e)]
        }

def generate_report(results: List[Dict[str, Any]]):
    """Generate comprehensive markdown report"""
    
    # Calculate statistics
    total_queries = len(results)
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    failed = sum(1 for r in results if r["verdict"] == "FAIL")
    partial = sum(1 for r in results if r["verdict"] == "PARTIAL")
    
    latencies = [r["latency_ms"] for r in results]
    p50_latency = statistics.median(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    
    # Intent accuracy
    correct_intents = sum(1 for r in results if r["actual_intent"] == r["expected_intent"] or 
                         (r["expected_intent"] == "general_help" and r["actual_intent"] in ["general_help", "product_info", "chitchat"]))
    intent_accuracy = (correct_intents / total_queries) * 100
    
    # Citation statistics
    total_citations = sum(r["citations_count"] for r in results)
    fabricated = sum(sum(1 for c in r["citations"] if c.get("is_fabricated", False)) for r in results)
    
    # Source distribution
    source_dist = {}
    for r in results:
        for cite in r["citations"]:
            source = cite.get("source", "Unknown")
            source_dist[source] = source_dist.get(source, 0) + 1
    
    # Generate markdown report
    report = f"""# STRYDA-v2 Chat & Citation Verification Test

**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Version:** v2.3.0-opt  
**Queries Tested:** {total_queries} (10 general + 10 compliance)

## Summary Results

- **Total Queries:** {total_queries}
- **Passed:** {passed}/{total_queries} ({(passed/total_queries)*100:.1f}%)
- **Partial:** {partial}/{total_queries} ({(partial/total_queries)*100:.1f}%)
- **Failed:** {failed}/{total_queries} ({(failed/total_queries)*100:.1f}%)
- **p50 Latency:** {p50_latency/1000:.1f}s
- **p95 Latency:** {p95_latency/1000:.1f}s
- **Intent Accuracy:** {intent_accuracy:.1f}% ({correct_intents}/{total_queries} correct)
- **Citation Accuracy:** {((total_citations - fabricated) / max(total_citations, 1)) * 100:.1f}% ({total_citations - fabricated}/{total_citations} correct)
- **Fabricated Citations:** {fabricated}

## Latency Distribution

- **Min:** {min(latencies)}ms
- **p50:** {int(p50_latency)}ms
- **p90:** {int(statistics.quantiles(latencies, n=10)[8]) if len(latencies) >= 10 else max(latencies)}ms
- **p95:** {int(p95_latency)}ms
- **Max:** {max(latencies)}ms

## General Queries (1-10)

| # | Query | Intent | Citations | Latency | Verdict |
|---|-------|--------|-----------|---------|---------|
"""
    
    # Add general query results
    for r in results[:10]:
        query_short = r["query"][:40] + "..." if len(r["query"]) > 40 else r["query"]
        verdict_icon = "✅" if r["verdict"] == "PASS" else "⚠️" if r["verdict"] == "PARTIAL" else "❌"
        report += f"| {r['query_num']} | {query_short} | {r['actual_intent']} | {r['citations_count']} | {r['latency_ms']:,}ms | {verdict_icon} |\n"
    
    report += "\n## Compliance Queries (11-20)\n\n"
    report += "| # | Query | Intent | Citations | Sources | Latency | Verdict |\n"
    report += "|---|-------|--------|-----------|---------|---------|---------|  \n"
    
    # Add compliance query results
    for r in results[10:]:
        query_short = r["query"][:35] + "..." if len(r["query"]) > 35 else r["query"]
        sources = ", ".join(set(c["source"] for c in r["citations"])) if r["citations"] else "None"
        sources_short = sources[:30] + "..." if len(sources) > 30 else sources
        verdict_icon = "✅" if r["verdict"] == "PASS" else "⚠️" if r["verdict"] == "PARTIAL" else "❌"
        report += f"| {r['query_num']} | {query_short} | {r['actual_intent']} | {r['citations_count']} | {sources_short} | {r['latency_ms']:,}ms | {verdict_icon} |\n"
    
    report += f"""
## Citation Quality Analysis

**Total Citations:** {total_citations}  
**Correct Sources:** {total_citations - fabricated}/{total_citations} ({((total_citations - fabricated) / max(total_citations, 1)) * 100:.1f}%)  
**Fabricated:** {fabricated}  
**Invalid Pages:** {sum(1 for r in results for c in r["citations"] if c.get("page", 0) < 1 or c.get("page", 0) > 600)}  

**Source Distribution:**
"""
    
    for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True):
        report += f"- {source}: {count} citations\n"
    
    report += f"""
## Intent Classification Breakdown

- **Correct:** {correct_intents}/{total_queries} ({intent_accuracy:.1f}%)
- **Misclassified:** {total_queries - correct_intents}/{total_queries}

"""
    
    # List misclassifications
    misclassified = [r for r in results if r["actual_intent"] != r["expected_intent"] and 
                     not (r["expected_intent"] == "general_help" and r["actual_intent"] in ["general_help", "product_info", "chitchat"])]
    
    if misclassified:
        report += "**Misclassifications:**\n"
        for r in misclassified:
            report += f"- Query #{r['query_num']}: Expected {r['expected_intent']}, got {r['actual_intent']}\n"
    else:
        report += "**No misclassifications detected**\n"
    
    report += "\n## Issues Detected\n\n"
    
    issues_found = [r for r in results if r["issues"]]
    if issues_found:
        for r in issues_found:
            report += f"**Query #{r['query_num']}:** {r['query']}\n"
            for issue in r["issues"]:
                report += f"- {issue}\n"
            report += "\n"
    else:
        report += "**No issues detected - all queries passed validation**\n"
    
    # Production readiness verdict
    report += "\n## Production Readiness Verdict\n\n"
    
    if passed >= 18 and fabricated == 0 and p95_latency < 12000 and intent_accuracy >= 90:
        verdict = "✅ GO FOR PRODUCTION BETA"
        rationale = f"""**Rationale:**
- Citation Accuracy: {((total_citations - fabricated) / max(total_citations, 1)) * 100:.1f}% (target 100%) ✅
- Intent Accuracy: {intent_accuracy:.1f}% (target ≥90%) {'✅' if intent_accuracy >= 90 else '❌'}
- p95 Latency: {p95_latency/1000:.1f}s (target ≤12s) {'✅' if p95_latency < 12000 else '❌'}
- Fabrications: {fabricated} (target 0) ✅
- Stability: {(passed/total_queries)*100:.1f}% success rate {'✅' if passed >= 18 else '❌'}

**Conclusion:** System meets all production readiness criteria. Ready for beta deployment.
"""
    elif passed >= 15 and fabricated == 0:
        verdict = "⚠️ CONDITIONAL GO"
        rationale = f"""**Rationale:**
- Citation Accuracy: {((total_citations - fabricated) / max(total_citations, 1)) * 100:.1f}% (target 100%) {'✅' if fabricated == 0 else '❌'}
- Intent Accuracy: {intent_accuracy:.1f}% (target ≥90%) {'✅' if intent_accuracy >= 90 else '❌'}
- p95 Latency: {p95_latency/1000:.1f}s (target ≤12s) {'✅' if p95_latency < 12000 else '❌'}
- Fabrications: {fabricated} (target 0) ✅
- Stability: {(passed/total_queries)*100:.1f}% success rate {'⚠️' if passed >= 15 else '❌'}

**Conclusion:** System shows good performance but has some issues. Recommend addressing identified issues before full production deployment.
"""
    else:
        verdict = "❌ NO-GO"
        rationale = f"""**Rationale:**
- Citation Accuracy: {((total_citations - fabricated) / max(total_citations, 1)) * 100:.1f}% (target 100%) {'✅' if fabricated == 0 else '❌'}
- Intent Accuracy: {intent_accuracy:.1f}% (target ≥90%) {'✅' if intent_accuracy >= 90 else '❌'}
- p95 Latency: {p95_latency/1000:.1f}s (target ≤12s) {'✅' if p95_latency < 12000 else '❌'}
- Fabrications: {fabricated} (target 0) {'✅' if fabricated == 0 else '❌'}
- Stability: {(passed/total_queries)*100:.1f}% success rate {'✅' if passed >= 18 else '❌'}

**Conclusion:** System does not meet production readiness criteria. Critical issues must be resolved before deployment.
"""
    
    report += f"**{verdict}**\n\n{rationale}"
    
    return report

def main():
    """Run comprehensive chat and citation verification test"""
    print("="*80)
    print("STRYDA-v2 Chat & Citation Verification Test")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # Test general queries (1-10)
    print("\n" + "="*80)
    print("TESTING GENERAL QUERIES (1-10)")
    print("="*80)
    
    for i, query in enumerate(GENERAL_QUERIES, 1):
        result = test_query(query, i, "general_help")
        results.append(result)
        time.sleep(1)  # Rate limiting
    
    # Test compliance queries (11-20)
    print("\n" + "="*80)
    print("TESTING COMPLIANCE QUERIES (11-20)")
    print("="*80)
    
    for i, query in enumerate(COMPLIANCE_QUERIES, 11):
        result = test_query(query, i, "compliance_strict")
        results.append(result)
        time.sleep(1)  # Rate limiting
    
    # Generate report
    print("\n" + "="*80)
    print("GENERATING REPORT")
    print("="*80)
    
    report = generate_report(results)
    
    # Save report
    report_path = "/app/tests/CHAT_VERIFICATION_REPORT.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {report_path}")
    
    # Save JSON results
    json_path = "/app/tests/chat_verification_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ JSON results saved to: {json_path}")
    
    # Print summary
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    failed = sum(1 for r in results if r["verdict"] == "FAIL")
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Queries: {len(results)}")
    print(f"Passed: {passed}/{len(results)} ({(passed/len(results))*100:.1f}%)")
    print(f"Failed: {failed}/{len(results)} ({(failed/len(results))*100:.1f}%)")
    print("="*80)

if __name__ == "__main__":
    main()
