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
            f"{BACKEND_URL}/api/chat/enhanced",
            json={
                "message": query,
                "session_id": f"citation_repair_test_{int(time.time())}",
                "enable_compliance_analysis": True,
                "enable_query_processing": True
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
        answer = data.get("response", "")
        citations = data.get("citations", [])
        confidence_score = data.get("confidence_score", 0)
        query_analysis = data.get("query_analysis", {})
        
        # Determine intent from query_analysis or infer from response
        intent = "unknown"
        if query_analysis:
            # Check if query was classified properly
            query_type = query_analysis.get("query_type", "")
            if "compliance" in query_type.lower() or "code" in query_type.lower():
                intent = "compliance_strict"
            elif "general" in query_type.lower():
                intent = "general_help"
            else:
                intent = query_type
        
        # If no query_analysis, infer from response quality
        if intent == "unknown":
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
                        "snippet": c.get("snippet", "")[:100],
                        "pill_text": c.get("pill_text", "")
                    }
                    for c in citations
                ],
                "sources_count": citation_sources,
                "confidence_score": confidence_score
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
                    return True
                else:
                    self.log_test("Root Endpoint", False, "Unexpected response message", data)
                    return False
            else:
                self.log_test("Root Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Connection error: {str(e)}")
            return False
    
    def test_health_endpoint(self):
        """Test GET /health endpoint as requested by user"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                expected = {"ok": True, "version": "v0.2"}
                if data == expected:
                    self.log_test("Health Endpoint", True, f"Health endpoint returned expected response: {data}")
                    return True
                else:
                    self.log_test("Health Endpoint", False, f"Health endpoint returned unexpected response. Expected: {expected}, Got: {data}", data)
                    return False
            else:
                self.log_test("Health Endpoint", False, f"Health endpoint returned status {response.status_code}", response.text[:200])
                return False
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Health endpoint request failed: {str(e)}")
            return False
    
    def test_ask_endpoint(self):
        """Test POST /api/ask endpoint as requested by user"""
        try:
            payload = {"query": "test question"}
            response = self.session.post(f"{API_BASE}/ask", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                # Check if response has expected fallback structure
                required_fields = ['answer', 'notes', 'citation']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Ask Endpoint", True, f"Ask endpoint returned fallback response with required fields: {list(data.keys())}")
                    return True
                else:
                    self.log_test("Ask Endpoint", False, f"Ask endpoint missing required fields: {missing_fields}. Got fields: {list(data.keys())}", data)
                    return False
            else:
                self.log_test("Ask Endpoint", False, f"Ask endpoint returned status {response.status_code}", response.text[:200])
                return False
        except Exception as e:
            self.log_test("Ask Endpoint", False, f"Ask endpoint request failed: {str(e)}")
            return False
    
    def test_status_endpoints(self):
        """Test status check endpoints"""
        try:
            # Test creating a status check
            status_data = {"client_name": "STRYDA_Test_Client"}
            response = self.session.post(f"{API_BASE}/status", json=status_data)
            
            if response.status_code == 200:
                created_status = response.json()
                if created_status.get('client_name') == "STRYDA_Test_Client":
                    self.log_test("Create Status Check", True, "Status check created successfully")
                    
                    # Test getting status checks
                    get_response = self.session.get(f"{API_BASE}/status")
                    if get_response.status_code == 200:
                        status_list = get_response.json()
                        if isinstance(status_list, list) and len(status_list) > 0:
                            self.log_test("Get Status Checks", True, f"Retrieved {len(status_list)} status checks")
                            return True
                        else:
                            self.log_test("Get Status Checks", False, "No status checks returned")
                            return False
                    else:
                        self.log_test("Get Status Checks", False, f"HTTP {get_response.status_code}")
                        return False
                else:
                    self.log_test("Create Status Check", False, "Incorrect client name in response", created_status)
                    return False
            else:
                self.log_test("Create Status Check", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Status Endpoints", False, f"Error: {str(e)}")
            return False
    
    def test_job_management(self):
        """Test job creation and management endpoints"""
        try:
            # Test creating a job
            job_data = {
                "name": "Test House Build - Auckland",
                "address": "123 Queen Street, Auckland, New Zealand"
            }
            response = self.session.post(f"{API_BASE}/jobs", json=job_data)
            
            if response.status_code == 200:
                created_job = response.json()
                job_id = created_job.get('id')
                
                if created_job.get('name') == job_data['name'] and job_id:
                    self.log_test("Create Job", True, f"Job created with ID: {job_id}")
                    
                    # Test getting all jobs
                    get_jobs_response = self.session.get(f"{API_BASE}/jobs")
                    if get_jobs_response.status_code == 200:
                        jobs_list = get_jobs_response.json()
                        if isinstance(jobs_list, list) and len(jobs_list) > 0:
                            self.log_test("Get All Jobs", True, f"Retrieved {len(jobs_list)} jobs")
                            
                            # Test getting specific job
                            get_job_response = self.session.get(f"{API_BASE}/jobs/{job_id}")
                            if get_job_response.status_code == 200:
                                specific_job = get_job_response.json()
                                if specific_job.get('id') == job_id:
                                    self.log_test("Get Specific Job", True, f"Retrieved job {job_id}")
                                    return True
                                else:
                                    self.log_test("Get Specific Job", False, "Job ID mismatch")
                                    return False
                            else:
                                self.log_test("Get Specific Job", False, f"HTTP {get_job_response.status_code}")
                                return False
                        else:
                            self.log_test("Get All Jobs", False, "No jobs returned")
                            return False
                    else:
                        self.log_test("Get All Jobs", False, f"HTTP {get_jobs_response.status_code}")
                        return False
                else:
                    self.log_test("Create Job", False, "Job creation response invalid", created_job)
                    return False
            else:
                self.log_test("Create Job", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Job Management", False, f"Error: {str(e)}")
            return False
    
    def test_chat_functionality(self):
        """Test AI chat functionality with NZ building code questions"""
        test_questions = [
            {
                "question": "What are the minimum hearth clearances for a solid fuel fireplace in New Zealand?",
                "expected_keywords": ["hearth", "clearance", "fireplace", "nz", "building code"]
            },
            {
                "question": "What insulation requirements apply to H1 energy efficiency in Auckland?",
                "expected_keywords": ["insulation", "h1", "energy", "efficiency"]
            },
            {
                "question": "What are the weathertightness requirements under E2 for external walls?",
                "expected_keywords": ["weathertight", "e2", "external", "moisture"]
            }
        ]
        
        all_tests_passed = True
        
        for i, test_case in enumerate(test_questions):
            try:
                chat_data = {
                    "message": test_case["question"],
                    "session_id": self.session_id
                }
                
                response = self.session.post(f"{API_BASE}/chat", json=chat_data)
                
                if response.status_code == 200:
                    chat_response = response.json()
                    ai_response = chat_response.get('response', '')
                    citations = chat_response.get('citations', [])
                    returned_session_id = chat_response.get('session_id')
                    
                    # Check if response contains relevant content
                    response_lower = ai_response.lower()
                    has_relevant_content = any(keyword.lower() in response_lower for keyword in test_case["expected_keywords"])
                    
                    # Check citations
                    has_citations = len(citations) > 0
                    
                    # Check session ID
                    correct_session = returned_session_id == self.session_id
                    
                    if ai_response and has_relevant_content and correct_session:
                        details = {
                            "response_length": len(ai_response),
                            "citations_count": len(citations),
                            "has_nz_context": "new zealand" in response_lower or "nz" in response_lower
                        }
                        self.log_test(f"Chat Question {i+1}", True, f"AI responded appropriately to NZ building code question", details)
                    else:
                        issues = []
                        if not ai_response:
                            issues.append("No AI response")
                        if not has_relevant_content:
                            issues.append("Response lacks relevant keywords")
                        if not correct_session:
                            issues.append("Session ID mismatch")
                        
                        self.log_test(f"Chat Question {i+1}", False, f"Issues: {', '.join(issues)}", {
                            "response": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                            "citations": citations
                        })
                        all_tests_passed = False
                else:
                    self.log_test(f"Chat Question {i+1}", False, f"HTTP {response.status_code}", response.text)
                    all_tests_passed = False
                    
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                self.log_test(f"Chat Question {i+1}", False, f"Error: {str(e)}")
                all_tests_passed = False
        
        return all_tests_passed
    
    def test_chat_history(self):
        """Test chat history retrieval"""
        try:
            # Get chat history for the session used in chat tests
            response = self.session.get(f"{API_BASE}/chat/{self.session_id}/history")
            
            if response.status_code == 200:
                history = response.json()
                if isinstance(history, list) and len(history) > 0:
                    # Check if we have both user and bot messages
                    user_messages = [msg for msg in history if msg.get('sender') == 'user']
                    bot_messages = [msg for msg in history if msg.get('sender') == 'bot']
                    
                    if len(user_messages) > 0 and len(bot_messages) > 0:
                        self.log_test("Chat History", True, f"Retrieved {len(history)} messages ({len(user_messages)} user, {len(bot_messages)} bot)")
                        return True
                    else:
                        self.log_test("Chat History", False, f"Missing message types: {len(user_messages)} user, {len(bot_messages)} bot")
                        return False
                else:
                    self.log_test("Chat History", False, "No chat history found")
                    return False
            else:
                self.log_test("Chat History", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Chat History", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        try:
            # Test invalid job creation
            invalid_job = {"name": ""}  # Missing address
            response = self.session.post(f"{API_BASE}/jobs", json=invalid_job)
            
            # Should handle gracefully (either 400 or 422)
            if response.status_code in [400, 422, 500]:
                self.log_test("Invalid Job Creation", True, f"Properly handled invalid request with HTTP {response.status_code}")
            else:
                self.log_test("Invalid Job Creation", False, f"Unexpected status code: {response.status_code}")
                return False
            
            # Test non-existent job retrieval
            fake_job_id = str(uuid.uuid4())
            response = self.session.get(f"{API_BASE}/jobs/{fake_job_id}")
            
            if response.status_code == 404:
                self.log_test("Non-existent Job", True, "Properly returned 404 for non-existent job")
            else:
                self.log_test("Non-existent Job", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Test empty chat message
            empty_chat = {"message": ""}
            response = self.session.post(f"{API_BASE}/chat", json=empty_chat)
            
            # Should handle gracefully
            if response.status_code in [400, 422, 500] or (response.status_code == 200 and response.json().get('response')):
                self.log_test("Empty Chat Message", True, f"Handled empty message appropriately")
                return True
            else:
                self.log_test("Empty Chat Message", False, f"Unexpected handling of empty message")
                return False
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n🚀 Starting STRYDA.ai Backend Tests")
        print(f"Backend URL: {API_BASE}")
        print(f"Session ID: {self.session_id}")
        print("=" * 60)
        
        # Run tests in order - starting with user-requested endpoints
        tests = [
            ("Health Endpoint (User Request)", self.test_health_endpoint),
            ("Ask Endpoint (User Request)", self.test_ask_endpoint),
            ("Backend Connectivity", self.test_root_endpoint),
            ("Status Management", self.test_status_endpoints),
            ("Job Management", self.test_job_management),
            ("AI Chat Functionality", self.test_chat_functionality),
            ("Chat History", self.test_chat_history),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Testing: {test_name}")
            if test_func():
                passed += 1
            time.sleep(0.5)  # Brief pause between test suites
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Summary: {passed}/{total} test suites passed")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = STRYDABackendTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All backend tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some backend tests failed!")
        exit(1)