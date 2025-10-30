#!/usr/bin/env python3
"""
Pills Regression Test Suite
Tests CLAUSE_PILLS feature flag behavior and citation quality

Run with:
    python3 tests/pills_regression.py

Expected behavior:
- CLAUSE_PILLS=false → Page-level citations only, no clause IDs
- CLAUSE_PILLS=true → Clause/table/figure pills with IDs when available
"""

import requests
import json
import os
import sys
from typing import List, Dict, Any

API_BASE = "http://localhost:8001"

# Test queries covering different compliance scenarios
TEST_QUERIES = [
    {
        "query": "What are the requirements for studs in Very High wind zone?",
        "category": "compliance_strict",
        "expected_sources": ["NZS 3604", "B1 Amendment 13"],
        "min_citations": 2
    },
    {
        "query": "Show me B1 Amendment 13 changes for bracing",
        "category": "amendment",
        "expected_sources": ["B1 Amendment 13"],
        "min_citations": 1
    },
    {
        "query": "E2/AS1 weathertightness for wall cladding",
        "category": "compliance_strict",
        "expected_sources": ["E2/AS1"],
        "min_citations": 1
    },
    {
        "query": "How are you today?",
        "category": "chitchat",
        "expected_sources": [],
        "min_citations": 0
    }
]


def test_chat_query(query: str, session_id: str = "regression-test") -> Dict[str, Any]:
    """Send a chat query and return the response"""
    try:
        response = requests.post(
            f"{API_BASE}/api/chat",
            json={
                "user_message": query,
                "session_id": session_id
            },
            timeout=30
        )
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def analyze_citations(citations: List[Dict[str, Any]], pills_enabled: bool) -> Dict[str, Any]:
    """Analyze citation structure and content"""
    if not citations:
        return {
            "count": 0,
            "has_clause_ids": False,
            "locator_types": {},
            "priority_order": []
        }
    
    locator_types = {}
    priority_order = []
    clause_ids_found = 0
    
    for cite in citations:
        locator_type = cite.get("locator_type", "page")
        locator_types[locator_type] = locator_types.get(locator_type, 0) + 1
        priority_order.append(locator_type)
        
        if cite.get("clause_id"):
            clause_ids_found += 1
    
    return {
        "count": len(citations),
        "has_clause_ids": clause_ids_found > 0,
        "clause_id_count": clause_ids_found,
        "locator_types": locator_types,
        "priority_order": priority_order
    }


def run_regression_suite(pills_enabled: bool):
    """Run all regression tests"""
    print(f"\n{'='*80}")
    print(f"PILLS REGRESSION TEST - CLAUSE_PILLS={'true' if pills_enabled else 'false'}")
    print(f"{'='*80}\n")
    
    results = {
        "pills_enabled": pills_enabled,
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    for idx, test_case in enumerate(TEST_QUERIES, 1):
        query = test_case["query"]
        category = test_case["category"]
        expected_sources = test_case["expected_sources"]
        min_citations = test_case["min_citations"]
        
        print(f"\n[Test {idx}/{len(TEST_QUERIES)}] {category.upper()}")
        print(f"Query: {query}")
        
        # Send query
        response = test_chat_query(query, session_id=f"regression-{pills_enabled}-{idx}")
        
        if "error" in response:
            print(f"❌ FAIL - API Error: {response['error']}")
            results["failed"] += 1
            results["tests"].append({
                "query": query,
                "status": "FAIL",
                "reason": response["error"]
            })
            continue
        
        # Analyze response
        answer = response.get("answer", "")
        citations = response.get("citations", [])
        intent = response.get("intent", "unknown")
        
        citation_analysis = analyze_citations(citations, pills_enabled)
        
        # Validation checks
        checks = []
        
        # Check 1: Citation count
        if category == "chitchat":
            if len(citations) == 0:
                checks.append("✅ No citations for chitchat (correct)")
            else:
                checks.append(f"⚠️ Unexpected {len(citations)} citations for chitchat")
        else:
            if len(citations) >= min_citations:
                checks.append(f"✅ Citation count: {len(citations)} (min: {min_citations})")
            else:
                checks.append(f"❌ Citation count: {len(citations)} (expected: {min_citations})")
        
        # Check 2: Locator type consistency
        if pills_enabled:
            if citation_analysis["has_clause_ids"]:
                checks.append(f"✅ Clause-level pills present: {citation_analysis['clause_id_count']}/{citation_analysis['count']}")
            else:
                if category == "chitchat":
                    checks.append("✅ No clause IDs for chitchat (correct)")
                else:
                    checks.append("⚠️ No clause IDs found (clause_citations module may be missing)")
        else:
            # CLAUSE_PILLS=false should always return page-level only
            if citation_analysis["locator_types"].get("page", 0) == len(citations):
                checks.append(f"✅ Page-level only (CLAUSE_PILLS=false)")
            else:
                checks.append(f"❌ Expected page-level only, got: {citation_analysis['locator_types']}")
        
        # Check 3: Answer quality
        if category != "chitchat" and len(answer) > 100:
            checks.append(f"✅ Answer length: {len(answer)} chars")
        elif category == "chitchat" and len(answer) > 0:
            checks.append(f"✅ Chitchat response: {len(answer)} chars")
        else:
            checks.append(f"⚠️ Short answer: {len(answer)} chars")
        
        # Print results
        for check in checks:
            print(f"  {check}")
        
        # Overall test result
        failed_checks = sum(1 for c in checks if "❌" in c)
        if failed_checks == 0:
            print(f"  ✅ PASS")
            results["passed"] += 1
            results["tests"].append({
                "query": query,
                "status": "PASS",
                "citations": len(citations),
                "locator_types": citation_analysis["locator_types"]
            })
        else:
            print(f"  ❌ FAIL ({failed_checks} checks failed)")
            results["failed"] += 1
            results["tests"].append({
                "query": query,
                "status": "FAIL",
                "reason": f"{failed_checks} checks failed",
                "citations": len(citations),
                "locator_types": citation_analysis["locator_types"]
            })
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY - CLAUSE_PILLS={'true' if pills_enabled else 'false'}")
    print(f"{'='*80}")
    print(f"Total Tests: {len(TEST_QUERIES)}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Pass Rate: {results['passed']/len(TEST_QUERIES)*100:.0f}%")
    print(f"{'='*80}\n")
    
    return results


def main():
    """Main entry point"""
    # Check backend health
    try:
        health = requests.get(f"{API_BASE}/health", timeout=5).json()
        print(f"✅ Backend health: {health}")
    except Exception as e:
        print(f"❌ Backend not available: {e}")
        sys.exit(1)
    
    # Read current CLAUSE_PILLS setting
    clause_pills_env = os.getenv("CLAUSE_PILLS", "false").lower()
    pills_enabled = clause_pills_env == "true"
    
    print(f"🎛️  Current CLAUSE_PILLS environment: {clause_pills_env}")
    
    # Run tests
    results = run_regression_suite(pills_enabled)
    
    # Exit with appropriate code
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
