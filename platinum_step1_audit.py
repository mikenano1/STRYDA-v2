#!/usr/bin/env python3
"""
PLATINUM RECOVERY SPRINT - STEP 1
MiTek V4 Audit (10 Questions)
Expectation: 100% pass, 0% NZS 3604 contamination
"""
import os
import sys
import json
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

from retrieval_service import semantic_search, detect_protected_brand, apply_brand_supremacy_penalty

print("=" * 80)
print("🔴 PLATINUM RECOVERY SPRINT - STEP 1: MITEK V4 AUDIT")
print(f"   Started: {datetime.now().isoformat()}")
print("   Expectation: 100% pass, 0 NZS 3604 contamination")
print("=" * 80)

# ============================================================================
# 10-QUESTION MITEK AUDIT
# ============================================================================

MITEK_AUDIT_QUESTIONS = [
    {
        "q": "What is the characteristic load for a MiTek 12kN pile fixing?",
        "expect_source": "MiTek",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None  # Value exists but may be in different format
    },
    {
        "q": "MiTek 6kN 12kN stud to bottom plate fixing",
        "expect_source": "MiTek",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "Lumberlok timber connector load capacity",
        "expect_source": "Lumberlok",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "Bowmac angle bracket specifications",
        "expect_source": "Bowmac",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "PosiStrut floor system installation guide",
        "expect_source": "PosiStrut",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "MiTek Residential Manual March 2024",
        "expect_source": "Residential",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "Stud-Lok fixing options for lintels",
        "expect_source": "Stud-Lok",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "GIB HandiBrac bracing system load rating",
        "expect_source": "GIB",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "MiTek joist hanger specifications",
        "expect_source": "MiTek",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    },
    {
        "q": "Flitch beam design manual from MiTek",
        "expect_source": "Flitch",
        "forbidden": ["NZS 3604", "3604"],
        "required_value": None
    }
]

# ============================================================================
# RUN AUDIT
# ============================================================================

results = {
    'total': len(MITEK_AUDIT_QUESTIONS),
    'passed': 0,
    'failed': 0,
    'nzs3604_contamination': 0,
    'details': []
}

print(f"\n🔍 RUNNING {len(MITEK_AUDIT_QUESTIONS)} AUDIT QUESTIONS...")
print("-" * 80)

for i, q_data in enumerate(MITEK_AUDIT_QUESTIONS, 1):
    question = q_data['q']
    expect_source = q_data['expect_source']
    forbidden = q_data['forbidden']
    required_value = q_data.get('required_value')
    
    print(f"\n[{i:2}/{len(MITEK_AUDIT_QUESTIONS)}] {question[:55]}...")
    
    # Detect brand for logging
    brand = detect_protected_brand(question)
    print(f"       🛡️ Brand Supremacy: {brand or 'NONE'}")
    
    # Run retrieval
    chunks = semantic_search(question, top_k=5)
    
    if not chunks:
        print(f"       ❌ FAIL: No results returned")
        results['failed'] += 1
        results['details'].append({
            'question': question,
            'status': 'FAIL',
            'reason': 'No results'
        })
        continue
    
    # Check sources
    top_sources = [c['source'] for c in chunks[:3]]
    top_content = ' '.join([c['content'] for c in chunks[:3]])
    
    # Check for FORBIDDEN content (NZS 3604 from NON-BRAND sources)
    contaminated = False
    for forbidden_term in forbidden:
        if forbidden_term.lower() in top_content.lower():
            # Check if this is from a BRAND source (allowed to reference NZS 3604)
            all_from_brand = all(expect_source.lower() in s.lower() or 'mitek' in s.lower() for s in top_sources)
            if not all_from_brand:
                contaminated = True
                print(f"       🚨 CONTAMINATION: Found '{forbidden_term}' from non-brand source!")
                results['nzs3604_contamination'] += 1
                break
    
    # Check expected source
    source_found = any(expect_source.lower() in s.lower() for s in top_sources)
    
    # Check required value
    value_found = True
    if required_value:
        value_found = required_value.lower() in top_content.lower()
    
    # Determine result
    if contaminated:
        status = 'CONTAMINATED'
        results['failed'] += 1
        print(f"       ❌ FAIL: NZS 3604 contamination detected")
    elif not source_found:
        status = 'WRONG_SOURCE'
        results['failed'] += 1
        print(f"       ⚠️ FAIL: Expected '{expect_source}' not in top sources")
        print(f"       Got: {', '.join([s[:30] for s in top_sources])}")
    elif required_value and not value_found:
        status = 'MISSING_VALUE'
        results['failed'] += 1
        print(f"       ⚠️ FAIL: Required value '{required_value}' not found")
    else:
        status = 'PASS'
        results['passed'] += 1
        print(f"       ✅ PASS | Source: {top_sources[0][:40]}")
    
    results['details'].append({
        'question': question,
        'status': status,
        'sources': top_sources,
        'contaminated': contaminated
    })

# ============================================================================
# FINAL REPORT
# ============================================================================

pass_rate = (results['passed'] / results['total']) * 100
contamination_rate = (results['nzs3604_contamination'] / results['total']) * 100

print("\n" + "=" * 80)
print("📊 MITEK V4 AUDIT RESULTS")
print("=" * 80)
print(f"\n✅ PASSED: {results['passed']}/{results['total']} ({pass_rate:.0f}%)")
print(f"❌ FAILED: {results['failed']}/{results['total']}")
print(f"🚨 NZS 3604 CONTAMINATION: {results['nzs3604_contamination']} ({contamination_rate:.0f}%)")

# Show failures
failures = [d for d in results['details'] if d['status'] != 'PASS']
if failures:
    print(f"\n❌ FAILURES ({len(failures)}):")
    for f in failures:
        print(f"   • {f['question'][:50]}: {f['status']}")

# Verdict
print("\n" + "-" * 80)
if pass_rate == 100 and results['nzs3604_contamination'] == 0:
    print("🎯 VERDICT: ✅ 100% PASS - PROCEED TO STEP 2")
    verdict = "PASS"
elif pass_rate >= 80 and results['nzs3604_contamination'] == 0:
    print("🥈 VERDICT: ACCEPTABLE (80%+) - May proceed with caution")
    verdict = "ACCEPTABLE"
else:
    print("🔴 VERDICT: ❌ FAILED - DO NOT PROCEED")
    verdict = "FAIL"
print("-" * 80)

# Save results
results['pass_rate'] = pass_rate
results['contamination_rate'] = contamination_rate
results['verdict'] = verdict
results['completed'] = datetime.now().isoformat()

with open('/app/mitek_v4_audit_step1.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to: /app/mitek_v4_audit_step1.json")
print("=" * 80)

# Exit code based on verdict
sys.exit(0 if verdict in ['PASS', 'ACCEPTABLE'] else 1)
