#!/usr/bin/env python3
"""
V4 AUTO-AUDIT: MITEK MINI-STRESS TEST
=====================================
20-Question stress test for MiTek/Lumberlok/Bowmac products
Focus: 12kN Pile Fixings, kN ratings, structural connectors
"""
import os
import sys
import json
import re
import asyncio
from pathlib import Path
from datetime import datetime

# Load env
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

sys.path.insert(0, '/app/backend-minimal')

from retrieval_service import semantic_search, expand_brand_synonyms
from emergentintegrations.llm.chat import LlmChat, UserMessage
from core_prompts import STRYDA_SYSTEM_PROMPT

EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

print("=" * 80)
print("🔴 V4 AUTO-AUDIT: MITEK MINI-STRESS TEST")
print(f"   Started: {datetime.now().isoformat()}")
print("=" * 80)

# ============================================================================
# TEST QUESTIONS - 20 targeted queries
# ============================================================================

STRESS_TEST_QUESTIONS = [
    # Brand Synonym Tests (should expand Lumberlok -> MiTek)
    {"q": "What products does Lumberlok make?", "expect_source": "MiTek", "test_type": "synonym"},
    {"q": "Show me Bowmac bracket options", "expect_source": "Bowmac", "test_type": "synonym"},
    {"q": "What is a GIB HandiBrac?", "expect_source": "GIB", "test_type": "cross_brand"},
    {"q": "PosiStrut floor systems", "expect_source": "PosiStrut", "test_type": "synonym"},
    
    # kN Rating Tests
    {"q": "What is the 12kN pile fixing?", "expect_value": "12kN", "test_type": "kn_rating"},
    {"q": "6kN stud to bottom plate fixing options", "expect_value": "6kN", "test_type": "kn_rating"},
    {"q": "What are the characteristic loads for Lumberlok connectors?", "expect_value": "kN", "test_type": "kn_rating"},
    {"q": "HandiBrac load rating", "expect_value": "12kN", "test_type": "kn_rating"},
    
    # Product Specific Tests
    {"q": "MiTek joist hangers", "expect_source": "Joist", "test_type": "product"},
    {"q": "Top plate stiffener from MiTek", "expect_source": "Stiffener", "test_type": "product"},
    {"q": "Stud-Lok fixing options", "expect_source": "Stud-Lok", "test_type": "product"},
    {"q": "Purlin cleats for roof fixing", "expect_source": "Purlin", "test_type": "product"},
    
    # BPIR Compliance Tests
    {"q": "Is Bowmac BPIR certified?", "expect_source": "BPIR", "test_type": "compliance"},
    {"q": "Lumberlok BPIR certificate", "expect_source": "BPIR", "test_type": "compliance"},
    {"q": "Gang-Nail compliance NZ", "expect_source": "Gang", "test_type": "compliance"},
    
    # Technical Manual Tests (Bible Priority)
    {"q": "MiTek residential construction guide", "expect_source": "Residential", "test_type": "bible"},
    {"q": "Flitch beam design manual", "expect_source": "Flitch", "test_type": "bible"},
    {"q": "PosiStrut installation instructions", "expect_source": "PosiStrut", "test_type": "bible"},
    
    # Edge Cases
    {"q": "timber connector characteristic strength", "expect_value": "kN", "test_type": "technical"},
    {"q": "multi-brace bracing system", "expect_source": "Multi-Brace", "test_type": "product"},
]

# ============================================================================
# HALLUCINATION DETECTION
# ============================================================================

HALLUCINATION_MARKERS = [
    "NZS 3604",  # Timber framing standard - not in MiTek docs
    "timber span",  # Wrong context
    "rafter span",  # Wrong context
    "consult the manual",  # Lazy response
    "I don't have",  # Admission of failure
    "not available",  # Failure
    "outside my knowledge",  # Failure
]

def check_hallucination(response):
    """Check if response contains hallucination markers"""
    response_lower = response.lower()
    for marker in HALLUCINATION_MARKERS:
        if marker.lower() in response_lower:
            return True, marker
    return False, None

# ============================================================================
# RUN STRESS TEST
# ============================================================================

results = {
    'total': len(STRESS_TEST_QUESTIONS),
    'passed': 0,
    'failed': 0,
    'hallucinations': 0,
    'details': []
}

async def run_test(question_data, index):
    """Run a single stress test question"""
    question = question_data['q']
    test_type = question_data['test_type']
    expect_source = question_data.get('expect_source', '')
    expect_value = question_data.get('expect_value', '')
    
    print(f"\n[{index+1:2}/{len(STRESS_TEST_QUESTIONS)}] {question[:50]}...")
    print(f"       Type: {test_type} | Expect: {expect_source or expect_value}")
    
    # Test brand expansion
    expanded = expand_brand_synonyms(question)
    if expanded != question:
        print(f"       🔗 Synonym expanded: {expanded[:60]}...")
    
    # Run retrieval
    try:
        chunks = semantic_search(question, top_k=5)
        
        if not chunks:
            print(f"       ❌ FAIL: No results returned")
            return {'status': 'FAIL', 'reason': 'No results', 'question': question}
        
        # Check source relevance
        top_sources = [c['source'] for c in chunks[:3]]
        sources_str = ', '.join([s[:30] for s in top_sources])
        
        # Check for expected source in results
        source_found = any(expect_source.lower() in s.lower() for s in top_sources) if expect_source else True
        
        # Check for expected value in content
        top_content = ' '.join([c['content'] for c in chunks[:3]])
        value_found = expect_value.lower() in top_content.lower() if expect_value else True
        
        # Check for hallucination
        is_hallucination, marker = check_hallucination(top_content)
        
        if is_hallucination:
            print(f"       🚨 HALLUCINATION DETECTED: '{marker}'")
            return {'status': 'HALLUCINATION', 'reason': f'Contains: {marker}', 'question': question}
        
        if source_found and value_found:
            print(f"       ✅ PASS | Sources: {sources_str}")
            return {'status': 'PASS', 'sources': top_sources, 'question': question}
        else:
            reason = []
            if not source_found:
                reason.append(f"Expected '{expect_source}' not in sources")
            if not value_found:
                reason.append(f"Expected '{expect_value}' not in content")
            print(f"       ⚠️ WEAK | {'; '.join(reason)}")
            return {'status': 'WEAK', 'reason': '; '.join(reason), 'question': question, 'sources': top_sources}
            
    except Exception as e:
        print(f"       ❌ ERROR: {str(e)[:50]}")
        return {'status': 'ERROR', 'reason': str(e)[:100], 'question': question}


async def main():
    print("\n" + "-" * 80)
    print("🔍 RUNNING 20 STRESS TEST QUESTIONS...")
    print("-" * 80)
    
    for i, q_data in enumerate(STRESS_TEST_QUESTIONS):
        result = await run_test(q_data, i)
        results['details'].append(result)
        
        if result['status'] == 'PASS':
            results['passed'] += 1
        elif result['status'] == 'HALLUCINATION':
            results['hallucinations'] += 1
            results['failed'] += 1
        elif result['status'] in ['FAIL', 'ERROR']:
            results['failed'] += 1
        # WEAK counts as partial pass
    
    # Calculate pass rate
    pass_rate = (results['passed'] / results['total']) * 100
    hallucination_rate = (results['hallucinations'] / results['total']) * 100
    
    print("\n" + "=" * 80)
    print("📊 V4 AUTO-AUDIT RESULTS")
    print("=" * 80)
    print(f"\n✅ PASSED: {results['passed']}/{results['total']} ({pass_rate:.1f}%)")
    print(f"❌ FAILED: {results['failed']}/{results['total']}")
    print(f"🚨 HALLUCINATIONS: {results['hallucinations']} ({hallucination_rate:.1f}%)")
    
    # Show failed/weak questions
    failed_qs = [d for d in results['details'] if d['status'] in ['FAIL', 'HALLUCINATION', 'ERROR']]
    weak_qs = [d for d in results['details'] if d['status'] == 'WEAK']
    
    if failed_qs:
        print(f"\n❌ CRITICAL FAILURES ({len(failed_qs)}):")
        for f in failed_qs:
            print(f"   • {f['question'][:50]}: {f.get('reason', 'Unknown')}")
    
    if weak_qs:
        print(f"\n⚠️ WEAK RESULTS ({len(weak_qs)}):")
        for w in weak_qs:
            print(f"   • {w['question'][:50]}: {w.get('reason', 'Unknown')}")
    
    # Overall verdict
    print("\n" + "-" * 80)
    if pass_rate >= 80 and hallucination_rate == 0:
        print("🎯 VERDICT: PLATINUM CERTIFIED ✓")
    elif pass_rate >= 60 and hallucination_rate < 5:
        print("🥈 VERDICT: GOLD CERTIFIED")
    elif pass_rate >= 40:
        print("🥉 VERDICT: SILVER - NEEDS IMPROVEMENT")
    else:
        print("🔴 VERDICT: FAILED - REQUIRES ATTENTION")
    print("-" * 80)
    
    # Save results
    results['pass_rate'] = pass_rate
    results['hallucination_rate'] = hallucination_rate
    results['completed'] = datetime.now().isoformat()
    
    with open('/app/mitek_stress_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: /app/mitek_stress_test_results.json")
    print("=" * 80)

# Run
asyncio.run(main())
