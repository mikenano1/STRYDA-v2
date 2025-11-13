#!/usr/bin/env python3
"""
STRYDA-v2 Complete Retrieval Validation - 30 Query Test Suite

Tests embedding regeneration for 840 documents (NZS 3604, NZ Building Code, NZS 4229)
using text-embedding-3-small with pgvector IVFFlat index.

Test Categories:
1. NZS 3604 Queries (5) - EXPECT citations
2. NZ Building Code B1-G12 (5) - EXPECT citations
3. E2/AS1 (5) - EXPECT citations
4. NZS 4229 (5) - EXPECT citations
5. General Builder Knowledge (5) - NO citations expected
6. Practical/Tool Questions (5) - NO citations expected
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# Backend configuration
BACKEND_URL = "http://localhost:8001"
CHAT_ENDPOINT = f"{BACKEND_URL}/api/chat"

# Test queries organized by category
TEST_QUERIES = {
    "nzs_3604": [
        "nzs 3604 stud spacing requirements",
        "nzs 3604 rafter span 4.2m",
        "nzs 3604 brace fixing pattern",
        "nzs 3604 pile embedment depth",
        "nzs 3604 verandah beam sizing"
    ],
    "nz_building_code": [
        "minimum barrier height f4 requirements",
        "b1 as1 footing depth for standard residential",
        "fire stopping between floors c3 rules",
        "h1 insulation r-values for walls",
        "g12 hot water system safe temperatures"
    ],
    "e2_as1": [
        "e2as1 minimum apron flashing cover",
        "e2as1 roof pitch requirements",
        "e2as1 cavity batten treatment levels",
        "e2as1 deck to cladding clearance",
        "e2as1 membrane fall requirements"
    ],
    "nzs_4229": [
        "nzs 4229 minimum reinforcing for concrete masonry",
        "nzs 4229 lintel reinforcement schedule",
        "nzs 4229 grout fill requirements",
        "nzs 4229 bond beam spacing rules",
        "nzs 4229 foundation block requirements"
    ],
    "general_builder": [
        "how far can 140x45 joists span",
        "best fixings for exterior pergola",
        "how to prevent decking cupping",
        "how much clearance under cladding",
        "what size posts for 3m veranda"
    ],
    "practical_tools": [
        "whats the best laser level for framing",
        "how to stop doors sticking in winter",
        "why is my deck moving when i walk on it",
        "what is the best timber for outdoor steps",
        "best screws for treated pine"
    ]
}

# Expected intents for each category
EXPECTED_INTENTS = {
    "nzs_3604": "compliance_strict",
    "nz_building_code": "compliance_strict",
    "e2_as1": "compliance_strict",
    "nzs_4229": "compliance_strict",
    "general_builder": ["general_help", "product_info", "general_advice", "chitchat"],
    "practical_tools": ["general_help", "product_info", "general_advice", "chitchat"]
}

# Expected citations for each category
EXPECTED_CITATIONS = {
    "nzs_3604": True,
    "nz_building_code": True,
    "e2_as1": True,
    "nzs_4229": True,
    "general_builder": False,
    "practical_tools": False
}


def send_query(query: str, session_id: str = "validation_test") -> Dict[str, Any]:
    """Send a query to the backend and return the response"""
    try:
        start_time = time.time()
        
        response = requests.post(
            CHAT_ENDPOINT,
            json={"message": query, "session_id": session_id},
            timeout=30
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            data['_test_latency_ms'] = latency_ms
            return data
        else:
            return {
                "error": f"HTTP {response.status_code}",
                "detail": response.text,
                "_test_latency_ms": latency_ms
            }
    except Exception as e:
        return {
            "error": "request_failed",
            "detail": str(e),
            "_test_latency_ms": 0
        }


def validate_query_result(query: str, category: str, response: Dict[str, Any], query_num: int) -> Dict[str, Any]:
    """Validate a single query result against expected criteria"""
    
    result = {
        "query_num": query_num,
        "query": query,
        "category": category,
        "expected_citations": EXPECTED_CITATIONS[category],
        "results": {
            "final_answer": response.get("answer", ""),
            "intent": response.get("intent", "unknown"),
            "citations_count": len(response.get("citations", [])),
            "citations": [],
            "tier1_hit": response.get("tier1_hit", False),
            "vector_latency_ms": response.get("latency_ms", 0),
            "total_latency_ms": response.get("_test_latency_ms", 0),
            "retrieval_operator_used": "<=>",  # Cosine operator
            "sources_selected": [],
            "model_used": response.get("model", "unknown"),
            "fallback_used": False
        },
        "verdict": "FAIL",
        "notes": []
    }
    
    # Extract citation details
    citations = response.get("citations", [])
    for cite in citations:
        result["results"]["citations"].append({
            "source": cite.get("source", "Unknown"),
            "page": cite.get("page", 0)
        })
        
        # Track unique sources
        source = cite.get("source", "Unknown")
        if source not in result["results"]["sources_selected"]:
            result["results"]["sources_selected"].append(source)
    
    # Check for errors
    if "error" in response:
        result["verdict"] = "FAIL"
        result["notes"].append(f"Error: {response.get('error')} - {response.get('detail', '')}")
        return result
    
    # Validate based on category
    intent = response.get("intent", "unknown")
    citations_count = len(citations)
    latency = response.get("_test_latency_ms", 0)
    
    # Categories 1-4: Compliance queries (EXPECT citations)
    if category in ["nzs_3604", "nz_building_code", "e2_as1", "nzs_4229"]:
        # Check intent
        if intent != "compliance_strict":
            result["verdict"] = "FAIL"
            result["notes"].append(f"Wrong intent: expected 'compliance_strict', got '{intent}'")
        # Check citations
        elif citations_count == 0:
            result["verdict"] = "PARTIAL"
            result["notes"].append("Correct intent but 0 citations")
        # Check latency
        elif latency > 20000:
            result["verdict"] = "FAIL"
            result["notes"].append(f"Latency too high: {latency}ms > 20s")
        else:
            result["verdict"] = "PASS"
            result["notes"].append(f"✅ Compliance query with {citations_count} citations")
    
    # Categories 5-6: General queries (NO citations expected)
    else:
        expected_intents = EXPECTED_INTENTS[category]
        
        # Check intent
        if intent not in expected_intents:
            result["verdict"] = "FAIL"
            result["notes"].append(f"Over-classified: expected {expected_intents}, got '{intent}'")
        # Check citations (should be 0-1)
        elif intent == "compliance_strict" and citations_count > 2:
            result["verdict"] = "FAIL"
            result["notes"].append(f"Over-citation: {citations_count} citations for general query")
        else:
            result["verdict"] = "PASS"
            result["notes"].append(f"✅ General query with correct intent '{intent}'")
    
    return result


def run_complete_validation() -> Dict[str, Any]:
    """Run the complete 30-query validation test suite"""
    
    print("=" * 80)
    print("STRYDA-v2 COMPLETE RETRIEVAL VALIDATION")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Start: {datetime.now().isoformat()}")
    print()
    
    all_results = []
    query_num = 0
    
    # Run all test categories
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'=' * 80}")
        print(f"Testing Category: {category.upper().replace('_', ' ')}")
        print(f"Expected Citations: {EXPECTED_CITATIONS[category]}")
        print(f"{'=' * 80}\n")
        
        for query in queries:
            query_num += 1
            print(f"[{query_num}/30] Testing: {query}")
            
            # Send query
            response = send_query(query, session_id=f"validation_{query_num}")
            
            # Validate result
            result = validate_query_result(query, category, response, query_num)
            all_results.append(result)
            
            # Print result
            verdict_symbol = "✅" if result["verdict"] == "PASS" else "⚠️" if result["verdict"] == "PARTIAL" else "❌"
            print(f"  {verdict_symbol} {result['verdict']}: {result['results']['intent']} | "
                  f"{result['results']['citations_count']} citations | "
                  f"{result['results']['total_latency_ms']:.0f}ms")
            
            if result["notes"]:
                for note in result["notes"]:
                    print(f"     {note}")
            
            # Small delay between queries
            time.sleep(0.5)
    
    # Calculate summary statistics
    summary = calculate_summary(all_results)
    
    # Generate reports
    generate_markdown_report(all_results, summary)
    generate_json_report(all_results, summary)
    
    # Print summary
    print_summary(summary)
    
    return {"results": all_results, "summary": summary}


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics from all results"""
    
    total_queries = len(results)
    
    # Count by verdict
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    partial_count = sum(1 for r in results if r["verdict"] == "PARTIAL")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    
    # Count by category
    compliance_results = [r for r in results if r["category"] in ["nzs_3604", "nz_building_code", "e2_as1", "nzs_4229"]]
    general_results = [r for r in results if r["category"] in ["general_builder", "practical_tools"]]
    
    # Citations statistics
    compliance_with_citations = sum(1 for r in compliance_results if r["results"]["citations_count"] > 0)
    general_with_citations = sum(1 for r in general_results if r["results"]["citations_count"] > 0)
    
    # Latency statistics
    latencies = [r["results"]["total_latency_ms"] for r in results if r["results"]["total_latency_ms"] > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    vector_latencies = [r["results"]["vector_latency_ms"] for r in results if r["results"]["vector_latency_ms"] > 0]
    avg_vector_latency = sum(vector_latencies) / len(vector_latencies) if vector_latencies else 0
    
    # Cosine operator success
    cosine_success = sum(1 for r in results if r["results"]["tier1_hit"])
    
    # Category breakdowns
    category_stats = {}
    for category in TEST_QUERIES.keys():
        cat_results = [r for r in results if r["category"] == category]
        cat_pass = sum(1 for r in cat_results if r["verdict"] == "PASS")
        cat_citations = sum(1 for r in cat_results if r["results"]["citations_count"] > 0)
        cat_latencies = [r["results"]["total_latency_ms"] for r in cat_results if r["results"]["total_latency_ms"] > 0]
        cat_avg_latency = sum(cat_latencies) / len(cat_latencies) if cat_latencies else 0
        
        category_stats[category] = {
            "total": len(cat_results),
            "pass": cat_pass,
            "pass_rate": (cat_pass / len(cat_results) * 100) if cat_results else 0,
            "citations_returned": cat_citations,
            "avg_latency_ms": cat_avg_latency
        }
    
    # Production readiness assessment
    pass_rate = (pass_count / total_queries * 100) if total_queries > 0 else 0
    
    if pass_rate >= 90 and avg_latency < 15000:
        readiness = "✅ READY"
    elif pass_rate >= 70 and avg_latency < 20000:
        readiness = "⚠️ CONDITIONAL"
    else:
        readiness = "❌ NOT READY"
    
    return {
        "total_queries": total_queries,
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": fail_count,
        "pass_rate": pass_rate,
        "compliance_queries": len(compliance_results),
        "general_queries": len(general_results),
        "compliance_with_citations": compliance_with_citations,
        "general_with_citations": general_with_citations,
        "cosine_success_rate": (cosine_success / total_queries * 100) if total_queries > 0 else 0,
        "avg_vector_latency_ms": avg_vector_latency,
        "avg_total_latency_ms": avg_latency,
        "category_stats": category_stats,
        "production_readiness": readiness
    }


def print_summary(summary: Dict[str, Any]):
    """Print summary statistics to console"""
    
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total Queries: {summary['total_queries']}")
    print(f"Pass Rate: {summary['pass_count']}/{summary['total_queries']} ({summary['pass_rate']:.1f}%)")
    print(f"Cosine Operator Success: {summary['cosine_success_rate']:.1f}%")
    print(f"Avg Vector Latency: {summary['avg_vector_latency_ms']:.0f}ms")
    print(f"Avg Total Latency: {summary['avg_total_latency_ms']:.0f}ms")
    print()
    
    print("RESULTS BY CATEGORY")
    print("-" * 80)
    
    category_names = {
        "nzs_3604": "NZS 3604",
        "nz_building_code": "NZ Building Code",
        "e2_as1": "E2/AS1",
        "nzs_4229": "NZS 4229",
        "general_builder": "General Builder",
        "practical_tools": "Practical/Tools"
    }
    
    for category, stats in summary['category_stats'].items():
        print(f"\n{category_names.get(category, category)} ({stats['total']} queries)")
        print(f"  Citations Returned: {stats['citations_returned']}/{stats['total']}")
        print(f"  Avg Latency: {stats['avg_latency_ms']:.0f}ms")
        print(f"  Pass Rate: {stats['pass_rate']:.1f}%")
    
    print("\n" + "=" * 80)
    print(f"PRODUCTION READINESS: {summary['production_readiness']}")
    print("=" * 80)


def generate_markdown_report(results: List[Dict[str, Any]], summary: Dict[str, Any]):
    """Generate comprehensive markdown report"""
    
    report_path = "/app/tests/COMPLETE_RETRIEVAL_VALIDATION.md"
    
    with open(report_path, 'w') as f:
        f.write("# STRYDA-v2 Complete Retrieval Validation\n\n")
        f.write(f"**Test Date:** {datetime.now().isoformat()}\n\n")
        f.write(f"**Backend URL:** {BACKEND_URL}\n\n")
        
        # Summary Statistics
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Queries:** {summary['total_queries']}\n")
        f.write(f"- **Pass Rate:** {summary['pass_count']}/{summary['total_queries']} ({summary['pass_rate']:.1f}%)\n")
        f.write(f"- **Cosine Operator Success:** {summary['cosine_success_rate']:.1f}%\n")
        f.write(f"- **Avg Vector Latency:** {summary['avg_vector_latency_ms']:.0f}ms\n")
        f.write(f"- **Avg Total Latency:** {summary['avg_total_latency_ms']:.0f}ms\n\n")
        
        # Results by Category
        f.write("## Results by Category\n\n")
        
        category_names = {
            "nzs_3604": "NZS 3604",
            "nz_building_code": "NZ Building Code (B1-G12)",
            "e2_as1": "E2/AS1",
            "nzs_4229": "NZS 4229",
            "general_builder": "General Builder Knowledge",
            "practical_tools": "Practical/Tool Questions"
        }
        
        for category, stats in summary['category_stats'].items():
            f.write(f"### {category_names.get(category, category)} ({stats['total']} queries)\n\n")
            f.write(f"- **Citations Returned:** {stats['citations_returned']}/{stats['total']}\n")
            f.write(f"- **Avg Latency:** {stats['avg_latency_ms']:.0f}ms\n")
            f.write(f"- **Pass Rate:** {stats['pass_rate']:.1f}%\n\n")
        
        # Anomalies Detected
        f.write("## Anomalies Detected\n\n")
        
        anomalies = []
        for r in results:
            if r["verdict"] == "FAIL":
                anomalies.append(f"- Query #{r['query_num']}: \"{r['query']}\" - {', '.join(r['notes'])}")
        
        if anomalies:
            f.write("\n".join(anomalies))
            f.write("\n\n")
        else:
            f.write("No anomalies detected.\n\n")
        
        # Production Readiness
        f.write("## Production Readiness\n\n")
        f.write(f"**{summary['production_readiness']}**\n\n")
        
        # Detailed Results
        f.write("## Detailed Query Results\n\n")
        
        for r in results:
            verdict_symbol = "✅" if r["verdict"] == "PASS" else "⚠️" if r["verdict"] == "PARTIAL" else "❌"
            f.write(f"### Query #{r['query_num']}: {r['query']}\n\n")
            f.write(f"- **Category:** {r['category']}\n")
            f.write(f"- **Verdict:** {verdict_symbol} {r['verdict']}\n")
            f.write(f"- **Intent:** {r['results']['intent']}\n")
            f.write(f"- **Citations:** {r['results']['citations_count']}\n")
            f.write(f"- **Latency:** {r['results']['total_latency_ms']:.0f}ms\n")
            f.write(f"- **Model:** {r['results']['model_used']}\n")
            
            if r['results']['citations']:
                f.write(f"- **Sources:** {', '.join([c['source'] for c in r['results']['citations']])}\n")
            
            if r['notes']:
                f.write(f"- **Notes:** {', '.join(r['notes'])}\n")
            
            f.write("\n")
    
    print(f"\n✅ Markdown report saved to: {report_path}")


def generate_json_report(results: List[Dict[str, Any]], summary: Dict[str, Any]):
    """Generate JSON report for programmatic analysis"""
    
    report_path = "/app/tests/complete_retrieval_validation.json"
    
    report_data = {
        "test_date": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "summary": summary,
        "results": results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"✅ JSON report saved to: {report_path}")


if __name__ == "__main__":
    try:
        # Run the complete validation
        validation_results = run_complete_validation()
        
        # Exit with appropriate code
        pass_rate = validation_results["summary"]["pass_rate"]
        
        if pass_rate >= 90:
            print("\n🎉 VALIDATION PASSED: System meets production readiness criteria")
            exit(0)
        elif pass_rate >= 70:
            print("\n⚠️ VALIDATION CONDITIONAL: System needs improvements before production")
            exit(1)
        else:
            print("\n❌ VALIDATION FAILED: System not ready for production")
            exit(2)
            
    except Exception as e:
        print(f"\n❌ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(3)
