"""
STRYDA-v2 Retrieval Debugging & Consistency Fix Test
Tests source detection and filtering logic for failing queries
"""

import psycopg2
import psycopg2.extras
import sys
import json
from typing import List, Dict

# Database configuration
DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def task1_database_content_verification():
    """Task 1: Check what documents actually exist in the database"""
    print_section("TASK 1: Database Content Verification")
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        
        # Check all document sources
        print("📊 Checking all document sources...")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT source, COUNT(*) as chunk_count, 
                       COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as with_embeddings
                FROM documents 
                GROUP BY source
                ORDER BY chunk_count DESC;
            """)
            
            sources = cur.fetchall()
            
            print(f"\n{'Source':<40} {'Chunks':<10} {'With Embeddings':<15}")
            print("-" * 70)
            for source in sources:
                print(f"{source['source']:<40} {source['chunk_count']:<10} {source['with_embeddings']:<15}")
        
        # Check for problem documents (H1, F4, G5, NZS 3604)
        print("\n\n🔍 Checking for problem documents (H1, F4, G5, NZS 3604)...")
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT source, page, LEFT(content, 100) as content_preview
                FROM documents
                WHERE source LIKE '%3604%' OR source LIKE '%Building Code%' 
                   OR content ILIKE '%H1%' OR content ILIKE '%F4%' OR content ILIKE '%G5%'
                LIMIT 20;
            """)
            
            problem_docs = cur.fetchall()
            
            if problem_docs:
                print(f"\nFound {len(problem_docs)} documents matching problem patterns:")
                for doc in problem_docs:
                    print(f"\n  Source: {doc['source']}")
                    print(f"  Page: {doc['page']}")
                    print(f"  Content: {doc['content_preview']}...")
            else:
                print("\n⚠️ NO documents found matching H1, F4, G5, or NZS 3604 patterns!")
        
        conn.close()
        
        return {
            "status": "completed",
            "total_sources": len(sources),
            "problem_docs_found": len(problem_docs) if problem_docs else 0
        }
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return {"status": "failed", "error": str(e)}

def task2_test_source_detection():
    """Task 2: Test source detection logic for failing queries"""
    print_section("TASK 2: Test Source Detection Logic")
    
    # Import the source detection logic
    sys.path.insert(0, '/app/backend-minimal')
    from simple_tier1_retrieval import simple_tier1_retrieval
    
    failing_queries = [
        {
            "query": "H1 insulation R-values for Auckland climate zone",
            "expected_keywords": ["h1", "insulation", "r-value", "thermal"],
            "expected_source": "NZ Building Code or H1 document"
        },
        {
            "query": "NZS 3604 stud spacing requirements",
            "expected_keywords": ["nzs 3604", "stud", "spacing"],
            "expected_source": "NZS 3604:2011"
        },
        {
            "query": "F4 means of escape for 2-storey building",
            "expected_keywords": ["f4", "escape"],
            "expected_source": "NZ Building Code or F4 document"
        },
        {
            "query": "G5.3.2 hearth clearance requirements",
            "expected_keywords": ["g5", "hearth", "clearance"],
            "expected_source": "NZ Building Code or G5 document"
        }
    ]
    
    results = []
    
    for test in failing_queries:
        print(f"\n🔍 Testing query: '{test['query']}'")
        print(f"   Expected keywords: {test['expected_keywords']}")
        print(f"   Expected source: {test['expected_source']}")
        
        try:
            # Test the retrieval
            docs = simple_tier1_retrieval(test['query'], top_k=6)
            
            print(f"\n   ✅ Retrieved {len(docs)} chunks")
            
            if docs:
                sources_found = {}
                for doc in docs:
                    source = doc.get('source', 'Unknown')
                    sources_found[source] = sources_found.get(source, 0) + 1
                
                print(f"   📊 Sources found: {sources_found}")
                
                # Show first chunk details
                first_doc = docs[0]
                print(f"\n   Top result:")
                print(f"     Source: {first_doc.get('source')}")
                print(f"     Page: {first_doc.get('page')}")
                print(f"     Score: {first_doc.get('score', 0):.3f}")
                print(f"     Snippet: {first_doc.get('snippet', '')[:100]}...")
            else:
                print(f"   ❌ NO CHUNKS FOUND - This is the problem!")
            
            results.append({
                "query": test['query'],
                "chunks_found": len(docs),
                "sources": list(set([doc.get('source') for doc in docs])) if docs else [],
                "status": "pass" if len(docs) >= 3 else "fail"
            })
            
        except Exception as e:
            print(f"   ❌ Retrieval failed: {e}")
            results.append({
                "query": test['query'],
                "chunks_found": 0,
                "error": str(e),
                "status": "error"
            })
    
    # Summary
    print("\n\n📊 Source Detection Test Summary:")
    print(f"{'Query':<50} {'Chunks':<10} {'Status':<10}")
    print("-" * 70)
    for result in results:
        print(f"{result['query'][:48]:<50} {result['chunks_found']:<10} {result['status']:<10}")
    
    return results

def task3_comprehensive_retest():
    """Task 4: Comprehensive retest of all 10 compliance queries"""
    print_section("TASK 4: Comprehensive Retest (10 Compliance Queries)")
    
    sys.path.insert(0, '/app/backend-minimal')
    from simple_tier1_retrieval import simple_tier1_retrieval
    
    compliance_queries = [
        "E2/AS1 minimum apron flashing cover",
        "NZS 3604 stud spacing requirements",
        "B1 Amendment 13 verification methods",
        "H1 insulation R-values for Auckland climate zone",
        "F4 means of escape for 2-storey building",
        "NZS 3604 Table 7.1 wind zones",
        "E2/AS1 cladding risk scores",
        "B1.3.3 foundation requirements",
        "G5.3.2 hearth clearance requirements",
        "NZS 3604 bearer and joist sizing"
    ]
    
    results = []
    
    for i, query in enumerate(compliance_queries, 1):
        print(f"\n[{i}/10] Testing: '{query}'")
        
        try:
            import time
            start_time = time.time()
            
            docs = simple_tier1_retrieval(query, top_k=6)
            
            latency = (time.time() - start_time) * 1000
            
            # Count citations (top 3 chunks)
            citations = docs[:3] if docs else []
            
            # Get sources
            sources = list(set([doc.get('source') for doc in docs])) if docs else []
            
            # Determine verdict
            verdict = "✅" if len(docs) >= 3 and len(citations) >= 1 and latency < 15000 else "❌"
            
            print(f"   Chunks: {len(docs)}, Citations: {len(citations)}, Sources: {sources[:2]}, Latency: {latency:.0f}ms")
            print(f"   Verdict: {verdict}")
            
            results.append({
                "query": query,
                "chunks_found": len(docs),
                "citations": len(citations),
                "sources": sources,
                "latency_ms": latency,
                "verdict": verdict
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "query": query,
                "chunks_found": 0,
                "citations": 0,
                "sources": [],
                "latency_ms": 0,
                "verdict": "❌",
                "error": str(e)
            })
    
    # Summary
    print("\n\n📊 Comprehensive Retest Summary:")
    print(f"{'Query':<50} {'Chunks':<8} {'Citations':<10} {'Latency':<10} {'Verdict':<8}")
    print("-" * 90)
    for result in results:
        print(f"{result['query'][:48]:<50} {result['chunks_found']:<8} {result['citations']:<10} {result['latency_ms']:<10.0f} {result['verdict']:<8}")
    
    # Calculate pass rate
    pass_count = sum(1 for r in results if r['verdict'] == "✅")
    pass_rate = (pass_count / len(results)) * 100
    
    print(f"\n✅ Pass Rate: {pass_count}/{len(results)} ({pass_rate:.1f}%)")
    
    return results

def generate_report(task1_result, task2_results, task4_results):
    """Task 5: Generate comprehensive report"""
    print_section("TASK 5: Generate Report")
    
    report = f"""# Retrieval Debugging & Fix Report

## Root Cause Analysis

**Issue:** Source detection and filtering logic causing 0 chunks for H1, F4, G5, NZS 3604 queries

**Source Names in DB:** {task1_result.get('total_sources', 'Unknown')} unique sources found

**Detection Logic Problem:** 
- Source filtering may be too restrictive
- Document names in database may not match expected patterns
- Some building code clauses (H1, F4, G5) may be in different documents than expected

## Database Content Verification

- Total sources in database: {task1_result.get('total_sources', 'Unknown')}
- Documents matching problem patterns: {task1_result.get('problem_docs_found', 0)}

## Source Detection Test Results

| Query | Chunks Found | Sources | Verdict |
|-------|--------------|---------|---------|
"""
    
    for result in task2_results:
        sources_str = ', '.join(result.get('sources', [])[:2]) if result.get('sources') else 'None'
        report += f"| {result['query'][:40]} | {result['chunks_found']} | {sources_str} | {result['status']} |\n"
    
    report += f"""

## Comprehensive Retest Results (10 Compliance Queries)

| Query | Before Chunks | After Chunks | Citations | Latency (ms) | Verdict |
|-------|---------------|--------------|-----------|--------------|---------|
"""
    
    for result in task4_results:
        sources_str = ', '.join(result.get('sources', [])[:2]) if result.get('sources') else 'None'
        report += f"| {result['query'][:35]} | N/A | {result['chunks_found']} | {result['citations']} | {result['latency_ms']:.0f} | {result['verdict']} |\n"
    
    # Calculate summary stats
    pass_count = sum(1 for r in task4_results if r['verdict'] == "✅")
    avg_chunks = sum(r['chunks_found'] for r in task4_results) / len(task4_results) if task4_results else 0
    avg_latency = sum(r['latency_ms'] for r in task4_results) / len(task4_results) if task4_results else 0
    
    report += f"""

## Summary

- **Queries Fixed:** {pass_count}/10 ({(pass_count/10)*100:.1f}%)
- **Average Chunks:** {avg_chunks:.1f} per query
- **Average Latency:** {avg_latency:.0f}ms
- **Citation Accuracy:** {sum(1 for r in task4_results if r['citations'] > 0)}/10 queries returned citations

## Recommendations

1. **Source Filtering:** Review source detection logic in simple_tier1_retrieval.py
2. **Database Content:** Verify that H1, F4, G5, NZS 3604 documents are properly indexed
3. **Fallback Strategy:** Consider searching all documents when no specific source match is found
4. **Performance:** Optimize latency to meet <15s target

## Next Steps

1. Review database content to confirm document names
2. Update source detection patterns if needed
3. Consider removing source filtering for broader search
4. Re-test after fixes
"""
    
    # Write report to file
    report_path = "/app/tests/RETRIEVAL_DEBUG_REPORT.md"
    try:
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"✅ Report written to: {report_path}")
    except Exception as e:
        print(f"❌ Failed to write report: {e}")
    
    return report

def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("  STRYDA-v2 RETRIEVAL DEBUGGING & CONSISTENCY FIX TEST")
    print("="*80)
    
    # Task 1: Database Content Verification
    task1_result = task1_database_content_verification()
    
    # Task 2: Test Source Detection Logic
    task2_results = task2_test_source_detection()
    
    # Task 4: Comprehensive Retest (Task 3 is fixing, which we'll report on)
    task4_results = task3_comprehensive_retest()
    
    # Task 5: Generate Report
    report = generate_report(task1_result, task2_results, task4_results)
    
    print("\n" + "="*80)
    print("  TEST EXECUTION COMPLETE")
    print("="*80)
    
    # Print summary
    print("\n📊 FINAL SUMMARY:")
    print(f"   Database sources: {task1_result.get('total_sources', 'Unknown')}")
    print(f"   Source detection tests: {len(task2_results)}")
    print(f"   Comprehensive retest: {len(task4_results)} queries")
    print(f"   Pass rate: {sum(1 for r in task4_results if r['verdict'] == '✅')}/{len(task4_results)}")
    print(f"\n   Report saved to: /app/tests/RETRIEVAL_DEBUG_REPORT.md")

if __name__ == "__main__":
    main()
