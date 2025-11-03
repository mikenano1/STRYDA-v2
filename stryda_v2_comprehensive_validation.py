#!/usr/bin/env python3
"""
STRYDA-v2 Comprehensive System Validation
==========================================
Tests the NZ Building Code RAG system with gpt-4o (primary) and gpt-4o-mini (fallback).
Validates retrieval quality, citation accuracy, response quality, and system performance.
"""

import requests
import json
import time
import psycopg2
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Configuration
BASE_URL = "http://localhost:8001"
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
ADMIN_TOKEN = "stryda_secure_admin_token_2024"

# Test queries organized by category
TEST_QUERIES = {
    "clause_specific": [
        "E2/AS1 minimum apron flashing cover",
        "B1 Amendment 13 verification methods for structural design",
        "G5.3.2 hearth clearance requirements",
        "H1 insulation R-values for Auckland climate zone",
        "F4 means of escape requirements for 2-storey buildings"
    ],
    "table_specific": [
        "NZS 3604 Table 7.1 wind zones",
        "NZS 3604 stud spacing table for standard wind",
        "E2/AS1 table for cladding risk scores"
    ],
    "cross_code": [
        "difference between B1 and B2 compliance verification",
        "how does E2 weathertightness relate to H1 thermal performance",
        "NZS 3604 and B1 structural requirements for deck joists"
    ],
    "general_building": [
        "what grade timber for external decks under NZS 3604",
        "minimum bearer size for 3m span deck"
    ],
    "product_level": [
        "what underlay is acceptable under corrugate roofing",
        "recommended flashing tape for window installations"
    ]
}

class ValidationResults:
    """Store and manage validation results"""
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        
    def add_result(self, query: str, category: str, result: Dict[str, Any]):
        """Add a test result"""
        self.results.append({
            "query": query,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            **result
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("verdict") == "accurate")
        
        avg_latency = sum(r.get("latency_ms", 0) for r in self.results) / total if total > 0 else 0
        avg_word_count = sum(r.get("word_count", 0) for r in self.results) / total if total > 0 else 0
        
        citation_issues = sum(1 for r in self.results if r.get("citation_issues", []))
        
        return {
            "total_queries": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "avg_latency_ms": avg_latency,
            "avg_word_count": avg_word_count,
            "citation_issues_count": citation_issues,
            "test_duration_seconds": (datetime.now() - self.start_time).total_seconds()
        }

def test_version_check() -> Dict[str, Any]:
    """Task 1.1: Version Check"""
    print("\n" + "="*80)
    print("TASK 1.1: VERSION CHECK")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/__version", timeout=10)
        data = response.json()
        
        print(f"✓ Status Code: {response.status_code}")
        print(f"✓ Model: {data.get('model')}")
        print(f"✓ Fallback: {data.get('fallback')}")
        print(f"✓ GPT5 Shadow: {data.get('gpt5_shadow')}")
        print(f"✓ Git SHA: {data.get('git_sha')}")
        print(f"✓ Build Time: {data.get('build_time')}")
        
        # Verify expected values
        checks = {
            "model_correct": data.get('model') == 'gpt-4o',
            "fallback_correct": data.get('fallback') == 'gpt-4o-mini',
            "gpt5_shadow_enabled": data.get('gpt5_shadow') == True
        }
        
        all_passed = all(checks.values())
        
        return {
            "success": all_passed,
            "data": data,
            "checks": checks
        }
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return {"success": False, "error": str(e)}

def test_database_health() -> Dict[str, Any]:
    """Task 1.2: Database Health"""
    print("\n" + "="*80)
    print("TASK 1.2: DATABASE HEALTH")
    print("="*80)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require", connect_timeout=10)
        cursor = conn.cursor()
        
        # Check documents table
        cursor.execute("SELECT COUNT(*) FROM documents;")
        doc_count = cursor.fetchone()[0]
        print(f"✓ Documents count: {doc_count}")
        
        # Check reasoning_responses table
        cursor.execute("SELECT COUNT(*) FROM reasoning_responses;")
        reasoning_count = cursor.fetchone()[0]
        print(f"✓ Reasoning responses count: {reasoning_count}")
        
        # Check table schema
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'documents'
            ORDER BY ordinal_position;
        """)
        schema = cursor.fetchall()
        print(f"✓ Documents table schema: {len(schema)} columns")
        for col_name, col_type in schema:
            print(f"  - {col_name}: {col_type}")
        
        cursor.close()
        conn.close()
        
        checks = {
            "documents_exist": doc_count > 100,
            "reasoning_responses_exist": reasoning_count >= 1,
            "schema_valid": len(schema) >= 5
        }
        
        return {
            "success": all(checks.values()),
            "doc_count": doc_count,
            "reasoning_count": reasoning_count,
            "schema_columns": len(schema),
            "checks": checks
        }
        
    except Exception as e:
        print(f"✗ Database Error: {e}")
        return {"success": False, "error": str(e)}

def test_api_health() -> Dict[str, Any]:
    """Task 1.3: API Health"""
    print("\n" + "="*80)
    print("TASK 1.3: API HEALTH")
    print("="*80)
    
    results = {}
    
    # Test /health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        health_data = response.json()
        print(f"✓ /health: {health_data}")
        results["health"] = {
            "success": health_data.get("ok") == True,
            "data": health_data
        }
    except Exception as e:
        print(f"✗ /health Error: {e}")
        results["health"] = {"success": False, "error": str(e)}
    
    # Test /ready endpoint
    try:
        response = requests.get(f"{BASE_URL}/ready", timeout=10)
        ready_data = response.json()
        print(f"✓ /ready: {ready_data}")
        results["ready"] = {
            "success": ready_data.get("ready") == True and ready_data.get("dependencies", {}).get("database") == "ok",
            "data": ready_data
        }
    except Exception as e:
        print(f"✗ /ready Error: {e}")
        results["ready"] = {"success": False, "error": str(e)}
    
    return {
        "success": all(r.get("success", False) for r in results.values()),
        "results": results
    }

def test_chat_query(query: str, session_id: str = "validation_test") -> Dict[str, Any]:
    """Execute a single chat query and capture metrics"""
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": query,
                "session_id": session_id
            },
            timeout=30
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "latency_ms": latency_ms
            }
        
        data = response.json()
        
        # Extract key metrics
        answer = data.get("answer", "")
        notes = data.get("notes", [])
        citations = data.get("citation", [])
        
        # Calculate word count
        word_count = len(answer.split())
        
        # Determine intent (from notes or infer)
        intent = "unknown"
        if "compliance_strict" in notes:
            intent = "compliance_strict"
        elif "general" in notes or "product" in notes:
            intent = "general"
        
        # Count sources
        sources_count = {}
        for citation in citations:
            source = citation.get("source", "unknown")
            sources_count[source] = sources_count.get(source, 0) + 1
        
        return {
            "success": True,
            "intent": intent,
            "answer": answer,
            "word_count": word_count,
            "citations": citations,
            "citation_count": len(citations),
            "sources_count_by_name": sources_count,
            "latency_ms": latency_ms,
            "notes": notes
        }
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "error": str(e),
            "latency_ms": latency_ms
        }

def validate_citations(query: str, citations: List[Dict], intent: str) -> Dict[str, Any]:
    """Task 3: Citation Accuracy Validation"""
    
    issues = []
    
    # For compliance_strict queries, verify citation requirements
    if intent == "compliance_strict":
        if len(citations) == 0:
            issues.append("No citations provided for compliance query")
        elif len(citations) > 3:
            issues.append(f"Too many citations ({len(citations)} > 3)")
        
        # Check for valid page numbers
        for i, citation in enumerate(citations):
            page = citation.get("page")
            if page is not None:
                if page == 0:
                    issues.append(f"Citation {i+1}: Invalid page number (0)")
                elif page > 500:
                    issues.append(f"Citation {i+1}: Suspicious page number ({page} > 500)")
            
            # Check for fabricated citations
            source = citation.get("source", "")
            if "Table 99" in source or "Clause Z9" in source:
                issues.append(f"Citation {i+1}: Potentially fabricated citation")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "citation_count": len(citations)
    }

def assess_response_quality(query: str, answer: str, citations: List[Dict]) -> str:
    """Task 4: Response Quality Check"""
    
    # Check for NZ Building Code terminology
    nz_terms = ["nzbc", "building code", "nzs", "clause", "compliance", "consent", 
                "weathertightness", "r-value", "clearance", "verification"]
    
    answer_lower = answer.lower()
    has_nz_terminology = any(term in answer_lower for term in nz_terms)
    
    # Check for specific measurements/numbers
    import re
    has_measurements = bool(re.search(r'\d+\s*(mm|m|cm|°C|%)', answer))
    
    # Check for code references
    has_code_refs = bool(re.search(r'(NZS|NZBC|E2|B1|H1|G5|F4)\s*[\d\.]+', answer))
    
    # Determine quality rating
    if has_nz_terminology and has_measurements and len(answer) > 100:
        return "accurate"
    elif has_nz_terminology and len(answer) > 50:
        return "partial"
    else:
        return "off_target"

def test_retrieval_quality() -> ValidationResults:
    """Task 2: Retrieval Quality Assessment (15+ Queries)"""
    print("\n" + "="*80)
    print("TASK 2: RETRIEVAL QUALITY ASSESSMENT")
    print("="*80)
    
    results = ValidationResults()
    
    query_num = 1
    for category, queries in TEST_QUERIES.items():
        print(f"\n--- Testing {category.upper()} queries ---")
        
        for query in queries:
            print(f"\n[{query_num}] Query: {query}")
            
            # Execute query
            result = test_chat_query(query, session_id=f"validation_{query_num}")
            
            if not result.get("success"):
                print(f"  ✗ Failed: {result.get('error')}")
                results.add_result(query, category, {
                    "verdict": "failed",
                    "error": result.get("error"),
                    "latency_ms": result.get("latency_ms", 0)
                })
                query_num += 1
                continue
            
            # Validate citations
            citation_validation = validate_citations(
                query, 
                result.get("citations", []), 
                result.get("intent", "unknown")
            )
            
            # Assess response quality
            quality = assess_response_quality(
                query,
                result.get("answer", ""),
                result.get("citations", [])
            )
            
            # Print results
            print(f"  ✓ Intent: {result.get('intent')}")
            print(f"  ✓ Word Count: {result.get('word_count')}")
            print(f"  ✓ Citations: {result.get('citation_count')}")
            print(f"  ✓ Sources: {result.get('sources_count_by_name')}")
            print(f"  ✓ Latency: {result.get('latency_ms'):.0f}ms")
            print(f"  ✓ Quality: {quality}")
            
            if citation_validation.get("issues"):
                print(f"  ⚠ Citation Issues: {citation_validation['issues']}")
            
            # Store result
            results.add_result(query, category, {
                "verdict": quality,
                "intent": result.get("intent"),
                "word_count": result.get("word_count"),
                "citation_count": result.get("citation_count"),
                "sources_count_by_name": result.get("sources_count_by_name"),
                "latency_ms": result.get("latency_ms"),
                "citation_issues": citation_validation.get("issues", []),
                "answer_preview": result.get("answer", "")[:200]
            })
            
            query_num += 1
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
    
    return results

def test_stress_test() -> Dict[str, Any]:
    """Task 5: Stress Test - 5 concurrent requests"""
    print("\n" + "="*80)
    print("TASK 5: STRESS TEST (5 concurrent requests)")
    print("="*80)
    
    import concurrent.futures
    
    test_query = "minimum apron flashing cover"
    
    def make_request(i):
        start = time.time()
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={
                    "message": test_query,
                    "session_id": f"stress_{i}"
                },
                timeout=30
            )
            latency = (time.time() - start) * 1000
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "latency_ms": latency,
                "request_id": i
            }
        except Exception as e:
            latency = (time.time() - start) * 1000
            return {
                "success": False,
                "error": str(e),
                "latency_ms": latency,
                "request_id": i
            }
    
    # Execute concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(1, 6)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    # Analyze results
    all_success = all(r.get("success", False) for r in results)
    max_latency = max(r.get("latency_ms", 0) for r in results)
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / len(results)
    
    print(f"\n✓ All requests completed: {all_success}")
    print(f"✓ Max latency: {max_latency:.0f}ms")
    print(f"✓ Avg latency: {avg_latency:.0f}ms")
    print(f"✓ All under 10s: {max_latency < 10000}")
    
    for r in results:
        status = "✓" if r.get("success") else "✗"
        print(f"  {status} Request {r['request_id']}: {r.get('latency_ms', 0):.0f}ms")
    
    return {
        "success": all_success and max_latency < 10000,
        "all_completed": all_success,
        "max_latency_ms": max_latency,
        "avg_latency_ms": avg_latency,
        "under_10s": max_latency < 10000,
        "results": results
    }

def test_admin_endpoint() -> Dict[str, Any]:
    """Task 6: Admin Endpoint Verification"""
    print("\n" + "="*80)
    print("TASK 6: ADMIN ENDPOINT VERIFICATION")
    print("="*80)
    
    # Test without token (should fail)
    try:
        response = requests.get(f"{BASE_URL}/admin/reasoning/recent?limit=10", timeout=10)
        no_auth_status = response.status_code
        print(f"✓ Without token: HTTP {no_auth_status} (expected 403)")
    except Exception as e:
        print(f"✗ Error testing without token: {e}")
        no_auth_status = None
    
    # Test with token (should succeed)
    try:
        response = requests.get(
            f"{BASE_URL}/admin/reasoning/recent?limit=10",
            headers={"X-Admin-Token": ADMIN_TOKEN},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ With token: HTTP 200")
            print(f"✓ Records returned: {data.get('count', 0)}")
            
            # Check if test record exists (id=1, model=gpt-5)
            results = data.get("results", [])
            if results:
                print(f"✓ Sample record: id={results[0].get('id')}, model={results[0].get('model')}")
            
            return {
                "success": True,
                "auth_working": no_auth_status == 403,
                "records_count": data.get("count", 0),
                "data": data
            }
        else:
            print(f"✗ With token: HTTP {response.status_code}")
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "auth_working": no_auth_status == 403
            }
            
    except Exception as e:
        print(f"✗ Error testing with token: {e}")
        return {
            "success": False,
            "error": str(e),
            "auth_working": no_auth_status == 403
        }

def generate_report(all_results: Dict[str, Any]):
    """Generate comprehensive validation report"""
    
    report_md = f"""# STRYDA-v2 System Validation Report

Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: gpt-4o
Database: Supabase PostgreSQL

## Summary

- **Total Queries**: {all_results['retrieval']['summary']['total_queries']}
- **Pass Rate**: {all_results['retrieval']['summary']['pass_rate']:.1f}%
- **Average Latency**: {all_results['retrieval']['summary']['avg_latency_ms']:.0f}ms
- **Citation Issues**: {all_results['retrieval']['summary']['citation_issues_count']}

## System Health

### Version Check
- Model: {all_results['version']['data'].get('model', 'N/A')}
- Fallback: {all_results['version']['data'].get('fallback', 'N/A')}
- GPT5 Shadow: {all_results['version']['data'].get('gpt5_shadow', 'N/A')}
- Status: {'✅ PASS' if all_results['version']['success'] else '❌ FAIL'}

### Database Health
- Documents: {all_results['database'].get('doc_count', 0)}
- Reasoning Responses: {all_results['database'].get('reasoning_count', 0)}
- Status: {'✅ PASS' if all_results['database']['success'] else '❌ FAIL'}

### API Health
- /health: {'✅ PASS' if all_results['api']['results']['health']['success'] else '❌ FAIL'}
- /ready: {'✅ PASS' if all_results['api']['results']['ready']['success'] else '❌ FAIL'}

## Detailed Query Results

| # | Query | Category | Verdict | Citations | Latency (ms) |
|---|-------|----------|---------|-----------|--------------|
"""
    
    for i, result in enumerate(all_results['retrieval']['results'], 1):
        report_md += f"| {i} | {result['query'][:50]}... | {result['category']} | {result['verdict']} | {result['citation_count']} | {result['latency_ms']:.0f} |\n"
    
    report_md += f"""
## Stress Test Results

- All Completed: {'✅ YES' if all_results['stress']['all_completed'] else '❌ NO'}
- Max Latency: {all_results['stress']['max_latency_ms']:.0f}ms
- Avg Latency: {all_results['stress']['avg_latency_ms']:.0f}ms
- Under 10s: {'✅ YES' if all_results['stress']['under_10s'] else '❌ NO'}

## Admin Endpoint

- Authentication: {'✅ WORKING' if all_results['admin']['auth_working'] else '❌ FAILED'}
- Records Retrieved: {all_results['admin'].get('records_count', 0)}
- Status: {'✅ PASS' if all_results['admin']['success'] else '❌ FAIL'}

## Findings

### ✅ What Works Well
"""
    
    # Analyze what works well
    accurate_count = sum(1 for r in all_results['retrieval']['results'] if r['verdict'] == 'accurate')
    if accurate_count > 0:
        report_md += f"- {accurate_count} queries returned accurate responses with proper NZ Building Code context\n"
    
    if all_results['retrieval']['summary']['avg_latency_ms'] < 7000:
        report_md += f"- Average response latency ({all_results['retrieval']['summary']['avg_latency_ms']:.0f}ms) is excellent\n"
    
    if all_results['database']['success']:
        report_md += f"- Database contains {all_results['database']['doc_count']} documents with proper schema\n"
    
    report_md += "\n### ⚠️ Partial Issues\n"
    
    # Analyze partial issues
    partial_count = sum(1 for r in all_results['retrieval']['results'] if r['verdict'] == 'partial')
    if partial_count > 0:
        report_md += f"- {partial_count} queries returned partial responses (may need improvement)\n"
    
    citation_issues = sum(1 for r in all_results['retrieval']['results'] if r.get('citation_issues'))
    if citation_issues > 0:
        report_md += f"- {citation_issues} queries had citation validation issues\n"
    
    report_md += "\n### ❌ Critical Problems\n"
    
    # Analyze critical problems
    failed_count = sum(1 for r in all_results['retrieval']['results'] if r['verdict'] == 'off_target' or r['verdict'] == 'failed')
    if failed_count > 0:
        report_md += f"- {failed_count} queries failed or returned off-target responses\n"
    
    if not all_results['stress']['success']:
        report_md += "- Stress test revealed performance or reliability issues\n"
    
    report_md += """
## Recommendations

"""
    
    pass_rate = all_results['retrieval']['summary']['pass_rate']
    if pass_rate >= 80:
        report_md += "- ✅ System meets >80% pass rate requirement - ready for production\n"
    else:
        report_md += f"- ⚠️ System pass rate ({pass_rate:.1f}%) below 80% target - needs improvement\n"
    
    if all_results['retrieval']['summary']['avg_latency_ms'] < 7000:
        report_md += "- ✅ Latency performance excellent (<7s average)\n"
    else:
        report_md += "- ⚠️ Consider optimizing query processing to reduce latency\n"
    
    if citation_issues > 0:
        report_md += "- ⚠️ Review citation generation logic to ensure accuracy\n"
    
    return report_md

def save_json_results(all_results: Dict[str, Any]):
    """Save structured JSON results"""
    
    json_output = {
        "test_date": datetime.now().isoformat(),
        "model": all_results['version']['data'].get('model', 'unknown'),
        "total_queries": all_results['retrieval']['summary']['total_queries'],
        "pass_count": all_results['retrieval']['summary']['passed'],
        "pass_rate": all_results['retrieval']['summary']['pass_rate'],
        "avg_latency_ms": all_results['retrieval']['summary']['avg_latency_ms'],
        "results": all_results['retrieval']['results'],
        "system_health": {
            "version": all_results['version'],
            "database": all_results['database'],
            "api": all_results['api']
        },
        "stress_test": all_results['stress'],
        "admin_endpoint": all_results['admin']
    }
    
    with open('/app/tests/system_validation_results.json', 'w') as f:
        json.dump(json_output, f, indent=2)
    
    print(f"\n✓ JSON results saved to /app/tests/system_validation_results.json")

def main():
    """Main validation execution"""
    
    print("="*80)
    print("STRYDA-v2 COMPREHENSIVE SYSTEM VALIDATION")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    all_results = {}
    
    # Task 1: System Health Verification
    all_results['version'] = test_version_check()
    all_results['database'] = test_database_health()
    all_results['api'] = test_api_health()
    
    # Task 2-4: Retrieval Quality Assessment
    retrieval_results = test_retrieval_quality()
    all_results['retrieval'] = {
        "summary": retrieval_results.get_summary(),
        "results": retrieval_results.results
    }
    
    # Task 5: Stress Test
    all_results['stress'] = test_stress_test()
    
    # Task 6: Admin Endpoint
    all_results['admin'] = test_admin_endpoint()
    
    # Generate reports
    print("\n" + "="*80)
    print("GENERATING REPORTS")
    print("="*80)
    
    report_md = generate_report(all_results)
    
    # Save reports
    with open('/app/tests/SYSTEM_VALIDATION_REPORT.md', 'w') as f:
        f.write(report_md)
    print("✓ Markdown report saved to /app/tests/SYSTEM_VALIDATION_REPORT.md")
    
    save_json_results(all_results)
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print(f"Total Queries: {all_results['retrieval']['summary']['total_queries']}")
    print(f"Pass Rate: {all_results['retrieval']['summary']['pass_rate']:.1f}%")
    print(f"Average Latency: {all_results['retrieval']['summary']['avg_latency_ms']:.0f}ms")
    print(f"System Health: {'✅ PASS' if all_results['version']['success'] and all_results['database']['success'] and all_results['api']['success'] else '❌ FAIL'}")
    print(f"Stress Test: {'✅ PASS' if all_results['stress']['success'] else '❌ FAIL'}")
    print(f"Admin Endpoint: {'✅ PASS' if all_results['admin']['success'] else '❌ FAIL'}")
    
    # Overall verdict
    overall_pass = (
        all_results['retrieval']['summary']['pass_rate'] >= 80 and
        all_results['retrieval']['summary']['avg_latency_ms'] < 7000 and
        all_results['version']['success'] and
        all_results['database']['success'] and
        all_results['api']['success']
    )
    
    print(f"\n{'='*80}")
    print(f"OVERALL VERDICT: {'✅ SYSTEM READY FOR PRODUCTION' if overall_pass else '⚠️ SYSTEM NEEDS IMPROVEMENT'}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
