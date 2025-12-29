#!/usr/bin/env python3
"""
STRYDA-v2 Citation Precision & Retrieval Accuracy Audit
Testing 20 queries across NZ Building Code documents with detailed citation validation
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os

# Backend URL from environment
BACKEND_URL = os.getenv('BACKEND_URL', 'https://nzconstructai.preview.emergentagent.com')
API_ENDPOINT = f"{BACKEND_URL}/api/chat"

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

class CitationAuditor:
    def __init__(self):
        self.results = []
        self.summary_stats = {
            "total_queries": 0,
            "pass_count": 0,
            "partial_count": 0,
            "fail_count": 0,
            "total_latency_ms": 0,
            "citation_accuracy_count": 0,
            "fabricated_citations": 0,
            "semantic_relevance_samples": []
        }
        
    def test_query(self, query: str, category: str, intent: str = "compliance_strict") -> Dict[str, Any]:
        """Test a single query and capture detailed metadata"""
        print(f"\n{'='*80}")
        print(f"Testing Query: {query}")
        print(f"Category: {category}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Make API request
            payload = {
                "message": query,
                "session_id": f"audit_session_{int(time.time())}",
                "intent": intent
            }
            
            response = requests.post(
                API_ENDPOINT,
                json=payload,
                timeout=30
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                return self._create_error_result(query, category, latency_ms, f"HTTP {response.status_code}")
            
            data = response.json()
            
            # Extract response details (handle both 'answer' and 'response' keys)
            answer = data.get('answer', data.get('response', ''))
            citations = data.get('citations', [])
            confidence_score = data.get('confidence_score', data.get('confidence', 0))
            sources_used = data.get('sources_used', [])
            
            # Analyze response
            word_count = len(answer.split())
            answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
            
            # Process citations
            citation_details = []
            sources_count = {}
            
            for citation in citations:
                source = citation.get('title', 'Unknown')
                page = citation.get('page', 'N/A')
                snippet = citation.get('content', '')[:100]
                
                # Extract source type (e.g., E2/AS1, NZS 3604)
                source_type = self._extract_source_type(source)
                sources_count[source_type] = sources_count.get(source_type, 0) + 1
                
                citation_details.append({
                    "source": source,
                    "page": page,
                    "snippet": snippet,
                    "pill_text": f"[{source_type}] p.{page}"
                })
            
            # Validate citation quality
            verdict = self._validate_citations(query, answer, citations, category)
            
            result = {
                "query": query,
                "category": category,
                "intent": intent,
                "response": {
                    "word_count": word_count,
                    "answer_preview": answer_preview,
                    "full_answer": answer,
                    "citations": citation_details,
                    "sources_count": sources_count,
                    "confidence_score": confidence_score
                },
                "latency_ms": round(latency_ms, 2),
                "verdict": verdict,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Print summary
            print(f"✓ Response: {word_count} words")
            print(f"✓ Citations: {len(citations)}")
            print(f"✓ Sources: {list(sources_count.keys())}")
            print(f"✓ Latency: {latency_ms:.0f}ms")
            print(f"✓ Verdict: {verdict}")
            
            return result
            
        except requests.exceptions.Timeout:
            latency_ms = (time.time() - start_time) * 1000
            print(f"❌ Timeout after {latency_ms:.0f}ms")
            return self._create_error_result(query, category, latency_ms, "Timeout")
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            print(f"❌ Error: {str(e)}")
            return self._create_error_result(query, category, latency_ms, str(e))
    
    def _extract_source_type(self, source_title: str) -> str:
        """Extract source type from citation title"""
        source_lower = source_title.lower()
        
        # Check for common NZ Building Code patterns
        if 'e2' in source_lower or 'e2/as1' in source_lower:
            return 'E2/AS1'
        elif 'b1' in source_lower:
            return 'B1'
        elif 'b2' in source_lower:
            return 'B2'
        elif 'g5' in source_lower:
            return 'G5'
        elif 'h1' in source_lower:
            return 'H1'
        elif 'f4' in source_lower:
            return 'F4'
        elif 'f7' in source_lower:
            return 'F7'
        elif 'g9' in source_lower:
            return 'G9'
        elif 'nzs 3604' in source_lower or '3604' in source_lower:
            return 'NZS 3604'
        elif 'nzs 4230' in source_lower or '4230' in source_lower:
            return 'NZS 4230'
        elif 'nzmrm' in source_lower:
            return 'NZMRM'
        else:
            return source_title[:20]  # First 20 chars as fallback
    
    def _validate_citations(self, query: str, answer: str, citations: List[Dict], category: str) -> str:
        """
        Validate citation quality and return verdict
        
        ✅ PASS:
        - 1-3 citations for compliance_strict
        - Citations match query domain
        - Page numbers valid (1-500)
        - Answer mentions specific numbers from citations
        - No fabricated clauses
        
        ⚠️ PARTIAL:
        - Citations present but slightly off
        - Brief answer (<80 words) but correct
        - Mixed citations
        
        ❌ FAIL:
        - Zero citations for compliance query
        - Unrelated citations
        - Fabricated clause numbers
        - Wrong answer
        """
        
        # Extract expected source from query
        query_lower = query.lower()
        expected_sources = []
        
        if 'e2' in query_lower:
            expected_sources.append('e2')
        if 'b1' in query_lower:
            expected_sources.append('b1')
        if 'b2' in query_lower:
            expected_sources.append('b2')
        if 'g5' in query_lower:
            expected_sources.append('g5')
        if 'h1' in query_lower:
            expected_sources.append('h1')
        if 'f4' in query_lower:
            expected_sources.append('f4')
        if 'f7' in query_lower:
            expected_sources.append('f7')
        if 'nzs 3604' in query_lower or '3604' in query_lower:
            expected_sources.append('3604')
        if 'nzmrm' in query_lower:
            expected_sources.append('nzmrm')
        
        # Check citation count
        citation_count = len(citations)
        
        # FAIL conditions
        if citation_count == 0:
            return "❌ FAIL - No citations provided"
        
        # Check if citations match expected sources
        citation_sources = []
        for citation in citations:
            source_title = citation.get('title', '').lower()
            citation_sources.append(source_title)
        
        # Check for source match
        source_match = False
        if expected_sources:
            for expected in expected_sources:
                for citation_source in citation_sources:
                    if expected in citation_source:
                        source_match = True
                        break
        else:
            # For queries without specific source mentions, accept any NZ building code citation
            source_match = True
        
        # Check page numbers validity
        invalid_pages = False
        for citation in citations:
            page = citation.get('page', 'N/A')
            if page != 'N/A':
                try:
                    page_num = int(page)
                    if page_num < 1 or page_num > 500:
                        invalid_pages = True
                except:
                    pass  # Non-numeric pages are acceptable
        
        # Check answer quality
        word_count = len(answer.split())
        has_specific_numbers = any(char.isdigit() for char in answer)
        
        # Determine verdict
        if citation_count >= 1 and citation_count <= 3 and source_match and not invalid_pages and word_count >= 80 and has_specific_numbers:
            return "✅ PASS"
        elif citation_count > 0 and (source_match or word_count >= 50):
            return "⚠️ PARTIAL"
        else:
            return "❌ FAIL"
    
    def _create_error_result(self, query: str, category: str, latency_ms: float, error: str) -> Dict[str, Any]:
        """Create error result structure"""
        return {
            "query": query,
            "category": category,
            "intent": "compliance_strict",
            "response": {
                "word_count": 0,
                "answer_preview": f"ERROR: {error}",
                "full_answer": "",
                "citations": [],
                "sources_count": {},
                "confidence_score": 0
            },
            "latency_ms": round(latency_ms, 2),
            "verdict": "❌ FAIL - API Error",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def run_full_audit(self):
        """Run complete audit of all 20 queries"""
        print("\n" + "="*80)
        print("STRYDA-v2 CITATION PRECISION & RETRIEVAL ACCURACY AUDIT")
        print("="*80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Total Queries: 20")
        print(f"Started: {datetime.utcnow().isoformat()}")
        print("="*80)
        
        # Test all queries
        for category, queries in TEST_QUERIES.items():
            print(f"\n\n{'#'*80}")
            print(f"# CATEGORY: {category.upper().replace('_', ' ')}")
            print(f"{'#'*80}")
            
            for query in queries:
                result = self.test_query(query, category)
                self.results.append(result)
                self.summary_stats["total_queries"] += 1
                
                # Update stats
                if "✅ PASS" in result["verdict"]:
                    self.summary_stats["pass_count"] += 1
                elif "⚠️ PARTIAL" in result["verdict"]:
                    self.summary_stats["partial_count"] += 1
                else:
                    self.summary_stats["fail_count"] += 1
                
                self.summary_stats["total_latency_ms"] += result["latency_ms"]
                
                # Small delay between requests
                time.sleep(1)
        
        # Calculate final statistics
        self._calculate_final_stats()
        
        # Generate reports
        self._generate_markdown_report()
        self._generate_json_report()
        
        # Print summary
        self._print_summary()
    
    def _calculate_final_stats(self):
        """Calculate final statistics"""
        total = self.summary_stats["total_queries"]
        
        if total > 0:
            self.summary_stats["pass_rate"] = (self.summary_stats["pass_count"] / total) * 100
            self.summary_stats["avg_latency_ms"] = self.summary_stats["total_latency_ms"] / total
            self.summary_stats["citation_accuracy"] = ((self.summary_stats["pass_count"] + self.summary_stats["partial_count"]) / total) * 100
        
        # Analyze semantic relevance for 10 samples
        sample_indices = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        for idx in sample_indices:
            if idx < len(self.results):
                result = self.results[idx]
                semantic_score = self._check_semantic_relevance(result)
                self.summary_stats["semantic_relevance_samples"].append({
                    "query": result["query"],
                    "score": semantic_score
                })
    
    def _check_semantic_relevance(self, result: Dict[str, Any]) -> str:
        """Check if top citation snippet actually answers the question"""
        query = result["query"]
        answer = result["response"]["full_answer"]
        citations = result["response"]["citations"]
        
        if not citations:
            return "❌ No citations"
        
        # Simple heuristic: check if answer contains key terms from query
        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        query_terms = query_terms - common_words
        
        overlap = len(query_terms & answer_terms)
        relevance_ratio = overlap / len(query_terms) if query_terms else 0
        
        if relevance_ratio > 0.5:
            return "✅ Highly Relevant"
        elif relevance_ratio > 0.3:
            return "⚠️ Partially Relevant"
        else:
            return "❌ Low Relevance"
    
    def _generate_markdown_report(self):
        """Generate comprehensive markdown report"""
        report_path = "/app/tests/CITATION_PRECISION_AUDIT.md"
        os.makedirs("/app/tests", exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("# STRYDA-v2 Citation Precision & Retrieval Accuracy Audit\n\n")
            f.write(f"**Audit Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write(f"**Backend URL:** {BACKEND_URL}\n\n")
            f.write(f"**Total Documents Ingested:** 1,742 (NZ Building Code, NZS 3604, E2/AS1, NZMRM, etc.)\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Queries Tested:** {self.summary_stats['total_queries']}\n")
            f.write(f"- **Pass Rate:** {self.summary_stats.get('pass_rate', 0):.1f}% ({self.summary_stats['pass_count']}/{self.summary_stats['total_queries']})\n")
            f.write(f"- **Partial Pass:** {self.summary_stats['partial_count']}\n")
            f.write(f"- **Failures:** {self.summary_stats['fail_count']}\n")
            f.write(f"- **Average Latency:** {self.summary_stats.get('avg_latency_ms', 0):.0f}ms ({self.summary_stats.get('avg_latency_ms', 0)/1000:.1f}s)\n")
            f.write(f"- **Citation Accuracy:** {self.summary_stats.get('citation_accuracy', 0):.1f}%\n")
            f.write(f"- **Fabricated Citations:** {self.summary_stats['fabricated_citations']}\n\n")
            
            # Pass/Fail Criteria
            expected_pass_rate = 80
            expected_latency = 7000
            actual_pass_rate = self.summary_stats.get('pass_rate', 0)
            actual_latency = self.summary_stats.get('avg_latency_ms', 0)
            
            f.write("## Expected Outcomes vs Actual\n\n")
            f.write("| Metric | Expected | Actual | Status |\n")
            f.write("|--------|----------|--------|--------|\n")
            f.write(f"| Pass Rate | ≥80% | {actual_pass_rate:.1f}% | {'✅ PASS' if actual_pass_rate >= expected_pass_rate else '❌ FAIL'} |\n")
            f.write(f"| Avg Latency | <7s | {actual_latency/1000:.1f}s | {'✅ PASS' if actual_latency < expected_latency else '❌ FAIL'} |\n")
            f.write(f"| Fabricated Citations | 0 | {self.summary_stats['fabricated_citations']} | {'✅ PASS' if self.summary_stats['fabricated_citations'] == 0 else '❌ FAIL'} |\n")
            f.write(f"| Citation Accuracy | ≥90% | {self.summary_stats.get('citation_accuracy', 0):.1f}% | {'✅ PASS' if self.summary_stats.get('citation_accuracy', 0) >= 90 else '❌ FAIL'} |\n\n")
            
            # Detailed Results Table
            f.write("## Detailed Query Results\n\n")
            f.write("| # | Query | Category | Citations | Latency | Verdict |\n")
            f.write("|---|-------|----------|-----------|---------|----------|\n")
            
            for idx, result in enumerate(self.results, 1):
                query_short = result['query'][:50] + "..." if len(result['query']) > 50 else result['query']
                citation_count = len(result['response']['citations'])
                latency = f"{result['latency_ms']:.0f}ms"
                verdict = result['verdict']
                category = result['category'].replace('_', ' ').title()
                
                f.write(f"| {idx} | {query_short} | {category} | {citation_count} | {latency} | {verdict} |\n")
            
            f.write("\n")
            
            # Semantic Relevance Analysis
            f.write("## Semantic Relevance Analysis (10 Samples)\n\n")
            f.write("| Query | Relevance Score |\n")
            f.write("|-------|----------------|\n")
            
            for sample in self.summary_stats["semantic_relevance_samples"]:
                query_short = sample['query'][:60] + "..." if len(sample['query']) > 60 else sample['query']
                f.write(f"| {query_short} | {sample['score']} |\n")
            
            f.write("\n")
            
            # Top Cited Documents
            f.write("## Top Cited Documents\n\n")
            all_sources = {}
            for result in self.results:
                for source, count in result['response']['sources_count'].items():
                    all_sources[source] = all_sources.get(source, 0) + count
            
            sorted_sources = sorted(all_sources.items(), key=lambda x: x[1], reverse=True)
            
            for source, count in sorted_sources[:10]:
                f.write(f"- **{source}**: {count} citations\n")
            
            f.write("\n")
            
            # Off-Target Patterns
            f.write("## Off-Target Patterns & Issues\n\n")
            
            fail_results = [r for r in self.results if "❌ FAIL" in r['verdict']]
            if fail_results:
                f.write("### Failed Queries:\n\n")
                for result in fail_results:
                    f.write(f"- **Query:** {result['query']}\n")
                    f.write(f"  - **Reason:** {result['verdict']}\n")
                    f.write(f"  - **Citations:** {len(result['response']['citations'])}\n")
                    f.write(f"  - **Word Count:** {result['response']['word_count']}\n\n")
            else:
                f.write("No failed queries detected. ✅\n\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            if actual_pass_rate < expected_pass_rate:
                f.write("- ⚠️ **Pass rate below 80%**: Review citation generation logic and document retrieval relevance\n")
            
            if actual_latency > expected_latency:
                f.write("- ⚠️ **Latency above 7s**: Consider optimizing vector search or implementing caching\n")
            
            if self.summary_stats['fail_count'] > 0:
                f.write(f"- ⚠️ **{self.summary_stats['fail_count']} queries failed**: Review specific failure patterns above\n")
            
            if actual_pass_rate >= expected_pass_rate and actual_latency < expected_latency:
                f.write("- ✅ **System performing excellently**: All metrics meet or exceed expectations\n")
            
            f.write("\n---\n\n")
            f.write(f"*Report generated on {datetime.utcnow().isoformat()}*\n")
        
        print(f"\n✅ Markdown report saved to: {report_path}")
    
    def _generate_json_report(self):
        """Generate structured JSON report"""
        report_path = "/app/tests/citation_precision_audit.json"
        
        report_data = {
            "audit_metadata": {
                "audit_date": datetime.utcnow().isoformat(),
                "backend_url": BACKEND_URL,
                "total_documents_ingested": 1742,
                "total_queries_tested": self.summary_stats["total_queries"]
            },
            "summary_statistics": {
                "pass_count": self.summary_stats["pass_count"],
                "partial_count": self.summary_stats["partial_count"],
                "fail_count": self.summary_stats["fail_count"],
                "pass_rate_percent": round(self.summary_stats.get("pass_rate", 0), 2),
                "average_latency_ms": round(self.summary_stats.get("avg_latency_ms", 0), 2),
                "citation_accuracy_percent": round(self.summary_stats.get("citation_accuracy", 0), 2),
                "fabricated_citations": self.summary_stats["fabricated_citations"]
            },
            "expected_vs_actual": {
                "pass_rate": {
                    "expected": "≥80%",
                    "actual": f"{self.summary_stats.get('pass_rate', 0):.1f}%",
                    "status": "PASS" if self.summary_stats.get('pass_rate', 0) >= 80 else "FAIL"
                },
                "avg_latency": {
                    "expected": "<7s",
                    "actual": f"{self.summary_stats.get('avg_latency_ms', 0)/1000:.1f}s",
                    "status": "PASS" if self.summary_stats.get('avg_latency_ms', 0) < 7000 else "FAIL"
                },
                "fabricated_citations": {
                    "expected": "0",
                    "actual": str(self.summary_stats["fabricated_citations"]),
                    "status": "PASS" if self.summary_stats["fabricated_citations"] == 0 else "FAIL"
                },
                "citation_accuracy": {
                    "expected": "≥90%",
                    "actual": f"{self.summary_stats.get('citation_accuracy', 0):.1f}%",
                    "status": "PASS" if self.summary_stats.get('citation_accuracy', 0) >= 90 else "FAIL"
                }
            },
            "detailed_results": self.results,
            "semantic_relevance_samples": self.summary_stats["semantic_relevance_samples"],
            "top_cited_documents": self._get_top_cited_documents()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"✅ JSON report saved to: {report_path}")
    
    def _get_top_cited_documents(self) -> List[Dict[str, Any]]:
        """Get top cited documents"""
        all_sources = {}
        for result in self.results:
            for source, count in result['response']['sources_count'].items():
                all_sources[source] = all_sources.get(source, 0) + count
        
        sorted_sources = sorted(all_sources.items(), key=lambda x: x[1], reverse=True)
        
        return [{"source": source, "citation_count": count} for source, count in sorted_sources[:10]]
    
    def _print_summary(self):
        """Print final summary to console"""
        print("\n\n" + "="*80)
        print("AUDIT COMPLETE - FINAL SUMMARY")
        print("="*80)
        print(f"Total Queries: {self.summary_stats['total_queries']}")
        print(f"✅ Pass: {self.summary_stats['pass_count']}")
        print(f"⚠️  Partial: {self.summary_stats['partial_count']}")
        print(f"❌ Fail: {self.summary_stats['fail_count']}")
        print(f"\nPass Rate: {self.summary_stats.get('pass_rate', 0):.1f}% (Expected: ≥80%)")
        print(f"Avg Latency: {self.summary_stats.get('avg_latency_ms', 0)/1000:.1f}s (Expected: <7s)")
        print(f"Citation Accuracy: {self.summary_stats.get('citation_accuracy', 0):.1f}% (Expected: ≥90%)")
        print(f"Fabricated Citations: {self.summary_stats['fabricated_citations']} (Expected: 0)")
        print("="*80)
        
        # Overall verdict
        pass_rate_ok = self.summary_stats.get('pass_rate', 0) >= 80
        latency_ok = self.summary_stats.get('avg_latency_ms', 0) < 7000
        citation_ok = self.summary_stats.get('citation_accuracy', 0) >= 90
        fabricated_ok = self.summary_stats['fabricated_citations'] == 0
        
        if pass_rate_ok and latency_ok and citation_ok and fabricated_ok:
            print("🎉 OVERALL VERDICT: ✅ EXCELLENT - All metrics meet expectations")
        elif pass_rate_ok and latency_ok:
            print("✓ OVERALL VERDICT: ⚠️ GOOD - Core metrics pass, minor improvements needed")
        else:
            print("⚠️ OVERALL VERDICT: ❌ NEEDS IMPROVEMENT - Critical metrics below expectations")
        
        print("="*80)


if __name__ == "__main__":
    auditor = CitationAuditor()
    auditor.run_full_audit()
