#!/usr/bin/env python3
"""
OVERNIGHT SHADOW AUDIT - CLEAN ARCHITECTURE EDITION
====================================================
300-Query randomized audit across Bremick, MiTek, and Pryda
Including "ACID TEST" trap queries to prove Brand Supremacy

LAW 1 TEST: NZS 3604 must be blocked for all branded queries
"""
import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path

# Load env
env_file = Path('/app/backend-minimal/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, val = line.split('=', 1)
            os.environ[key.strip()] = val.strip()

sys.path.insert(0, '/app/backend-minimal')

from retrieval_service import semantic_search, detect_protected_brand

print("=" * 80)
print("🌙 OVERNIGHT SHADOW AUDIT - CLEAN ARCHITECTURE EDITION")
print(f"   Started: {datetime.now().isoformat()}")
print("   Scope: 300 randomized queries across Bremick, MiTek, Pryda")
print("   ACID TEST: NZS 3604 trap queries included")
print("=" * 80)

# ============================================================================
# QUERY TEMPLATES
# ============================================================================

BREMICK_QUERIES = [
    # Standard queries
    "Bremick hex bolt proof load {size}",
    "Bremick masonry anchor specifications",
    "Bremick {material} fasteners catalogue",
    "Bremick M{size} hex nut tensile strength",
    "Bremick throughbolt installation torque",
    "Bremick sleeve anchor embedment depth",
    "Bremick {material} set screw specifications",
    "Bremick coach screw load capacity",
    "Bremick dynabolt edge distance requirements",
    "Bremick socket head cap screw dimensions",
    # ACID TEST - Trap queries
    "Bremick fasteners according to NZS 3604",
    "Bremick anchor using NZS 3604 requirements",
    "Bremick bolt per building code specifications",
    "Bremick M12 as per NZS 3604 table",
    "Bremick fixing according to the code",
]

MITEK_QUERIES = [
    # Standard queries
    "MiTek {kn}kN pile fixing specifications",
    "Lumberlok joist hanger load capacity",
    "Bowmac angle bracket dimensions",
    "MiTek PosiStrut floor system installation",
    "Lumberlok timber connector characteristic loads",
    "MiTek stud-lok fixing for lintels",
    "Bowmac post bearer bracket specifications",
    "MiTek gang-nail plate capacity",
    "Lumberlok purlin cleat installation",
    "MiTek residential manual construction details",
    # ACID TEST - Trap queries
    "Lumberlok per NZS 3604 timber framing",
    "MiTek fixing using NZS 3604 requirements",
    "Bowmac bracket according to building code",
    "MiTek connector as per NZS 3604 table",
    "Lumberlok joist hanger per code specifications",
]

MITEK_SUBBRANDS = ['Lumberlok', 'Bowmac', 'PosiStrut', 'Gang-Nail', 'Stud-Lok']

PRYDA_QUERIES = [
    # Standard queries
    "Pryda bracing anchor design guide",
    "Pryda foundation fixing specifications",
    "Pryda joist hanger load capacity",
    "Pryda nail plate installation guide",
    "Pryda timber connector straps",
    "Pryda truss boot design guide",
    "Pryda floor cassette manual",
    "Pryda builder angle bracket",
    "Pryda flat strap specifications",
    "Pryda post anchor bearer bracket",
    # ACID TEST - Trap queries
    "Pryda connector per NZS 3604",
    "Pryda bracing according to building code",
    "Pryda fixing using NZS 3604 requirements",
    "Pryda hanger as per NZS 3604 table",
    "Pryda nail plate per code specifications",
]

MATERIALS = ['stainless steel', 'galvanised', 'zinc plated', 'black', 'HDG']
SIZES = ['6', '8', '10', '12', '14', '16', '20', '24']
KN_VALUES = ['6', '12', '18', '24']

# ============================================================================
# GENERATE 300 RANDOMIZED QUERIES
# ============================================================================

def generate_query(template, brand):
    """Generate a query from template with random substitutions"""
    query = template
    query = query.replace('{size}', random.choice(SIZES))
    query = query.replace('{material}', random.choice(MATERIALS))
    query = query.replace('{kn}', random.choice(KN_VALUES))
    return query

def generate_all_queries(count=300):
    """Generate balanced query set across all brands"""
    queries = []
    
    # Distribute evenly: 100 per brand
    per_brand = count // 3
    
    # Bremick queries
    for i in range(per_brand):
        template = random.choice(BREMICK_QUERIES)
        query = generate_query(template, 'Bremick')
        is_trap = 'NZS 3604' in template or 'code' in template.lower()
        queries.append({
            'query': query,
            'brand': 'Bremick',
            'is_acid_test': is_trap
        })
    
    # MiTek queries (including sub-brands)
    for i in range(per_brand):
        template = random.choice(MITEK_QUERIES)
        # Randomly substitute MiTek with sub-brand
        if 'MiTek' in template and random.random() > 0.5:
            template = template.replace('MiTek', random.choice(MITEK_SUBBRANDS))
        query = generate_query(template, 'MiTek')
        is_trap = 'NZS 3604' in template or 'code' in template.lower()
        queries.append({
            'query': query,
            'brand': 'MiTek',
            'is_acid_test': is_trap
        })
    
    # Pryda queries
    for i in range(per_brand):
        template = random.choice(PRYDA_QUERIES)
        query = generate_query(template, 'Pryda')
        is_trap = 'NZS 3604' in template or 'code' in template.lower()
        queries.append({
            'query': query,
            'brand': 'Pryda',
            'is_acid_test': is_trap
        })
    
    # Shuffle for randomization
    random.shuffle(queries)
    return queries

# ============================================================================
# RUN AUDIT
# ============================================================================

print("\n📊 GENERATING 300 RANDOMIZED QUERIES...")
all_queries = generate_all_queries(300)

acid_test_count = sum(1 for q in all_queries if q['is_acid_test'])
print(f"   Total queries: {len(all_queries)}")
print(f"   ACID TEST queries: {acid_test_count}")

# Results tracking
results = {
    'Bremick': {'total': 0, 'passed': 0, 'contaminated': 0, 'acid_passed': 0, 'acid_total': 0},
    'MiTek': {'total': 0, 'passed': 0, 'contaminated': 0, 'acid_passed': 0, 'acid_total': 0},
    'Pryda': {'total': 0, 'passed': 0, 'contaminated': 0, 'acid_passed': 0, 'acid_total': 0},
}

failures = []
acid_failures = []

print(f"\n🔍 RUNNING SHADOW AUDIT...")
print("-" * 80)

for i, q_data in enumerate(all_queries, 1):
    query = q_data['query']
    brand = q_data['brand']
    is_acid = q_data['is_acid_test']
    
    results[brand]['total'] += 1
    if is_acid:
        results[brand]['acid_total'] += 1
    
    # Progress indicator
    if i % 50 == 0:
        print(f"   [{i:3}/{len(all_queries)}] Processing... ({brand})")
    
    # Run search
    try:
        chunks = semantic_search(query, top_k=5)
        
        if not chunks:
            failures.append({'query': query, 'brand': brand, 'reason': 'No results'})
            continue
        
        # Check results
        top_sources = [c['source'].lower() for c in chunks[:3]]
        top_content = ' '.join([c.get('content', '').lower() for c in chunks[:3]])
        
        # Check for correct brand source
        brand_found = any(brand.lower() in s for s in top_sources)
        
        # Check for NZS 3604 contamination
        contaminated = any('nzs 3604' in s or '3604' in s for s in top_sources)
        
        # Also check content for contamination in ACID tests
        if is_acid:
            contaminated = contaminated or ('nzs 3604' in top_content and brand.lower() not in top_sources[0])
        
        if brand_found and not contaminated:
            results[brand]['passed'] += 1
            if is_acid:
                results[brand]['acid_passed'] += 1
        elif contaminated:
            results[brand]['contaminated'] += 1
            if is_acid:
                acid_failures.append({
                    'query': query,
                    'brand': brand,
                    'top_source': chunks[0]['source'][:50] if chunks else 'N/A'
                })
        else:
            failures.append({
                'query': query,
                'brand': brand,
                'reason': f"Wrong source: {chunks[0]['source'][:30] if chunks else 'N/A'}"
            })
            
    except Exception as e:
        failures.append({'query': query, 'brand': brand, 'reason': str(e)[:50]})

# ============================================================================
# CERTIFICATION TABLE
# ============================================================================

print("\n" + "=" * 80)
print("📋 OVERNIGHT SHADOW AUDIT - CERTIFICATION TABLE")
print("=" * 80)

print(f"\n{'Brand':<12} | {'Total':<6} | {'Passed':<6} | {'Pass %':<8} | {'Contam':<6} | {'Contam %':<8} | {'ACID Pass':<10}")
print("-" * 80)

total_passed = 0
total_queries = 0
total_contaminated = 0
total_acid_passed = 0
total_acid = 0

for brand in ['Bremick', 'MiTek', 'Pryda']:
    r = results[brand]
    pass_rate = (r['passed'] / r['total'] * 100) if r['total'] > 0 else 0
    contam_rate = (r['contaminated'] / r['total'] * 100) if r['total'] > 0 else 0
    acid_rate = (r['acid_passed'] / r['acid_total'] * 100) if r['acid_total'] > 0 else 0
    
    print(f"{brand:<12} | {r['total']:<6} | {r['passed']:<6} | {pass_rate:>6.1f}% | {r['contaminated']:<6} | {contam_rate:>6.1f}% | {r['acid_passed']}/{r['acid_total']} ({acid_rate:.0f}%)")
    
    total_passed += r['passed']
    total_queries += r['total']
    total_contaminated += r['contaminated']
    total_acid_passed += r['acid_passed']
    total_acid += r['acid_total']

print("-" * 80)
overall_pass = (total_passed / total_queries * 100) if total_queries > 0 else 0
overall_contam = (total_contaminated / total_queries * 100) if total_queries > 0 else 0
overall_acid = (total_acid_passed / total_acid * 100) if total_acid > 0 else 0

print(f"{'TOTAL':<12} | {total_queries:<6} | {total_passed:<6} | {overall_pass:>6.1f}% | {total_contaminated:<6} | {overall_contam:>6.1f}% | {total_acid_passed}/{total_acid} ({overall_acid:.0f}%)")

# ============================================================================
# ACID TEST REPORT
# ============================================================================

print(f"\n🧪 ACID TEST REPORT (Law 1: Brand Supremacy)")
print("-" * 80)
print(f"   Total ACID queries: {total_acid}")
print(f"   Passed (NZS 3604 blocked): {total_acid_passed}")
print(f"   Failed (NZS 3604 leaked): {total_acid - total_acid_passed}")

if acid_failures:
    print(f"\n   ❌ ACID TEST FAILURES ({len(acid_failures)}):")
    for af in acid_failures[:10]:
        print(f"      • {af['query'][:50]}...")
        print(f"        Source: {af['top_source']}")

# ============================================================================
# VERDICT
# ============================================================================

print("\n" + "=" * 80)
if overall_pass >= 90 and overall_contam == 0 and overall_acid >= 95:
    print("🎯 VERDICT: ✅ PLATINUM CERTIFIED")
    print("   All brands passed with 0% NZS 3604 contamination")
    print("   Brand Supremacy Law is WORKING")
    verdict = "PLATINUM_CERTIFIED"
elif overall_pass >= 80 and overall_contam <= 5:
    print("🥈 VERDICT: GOLD CERTIFIED")
    print("   Acceptable performance with minor issues")
    verdict = "GOLD_CERTIFIED"
elif overall_pass >= 60:
    print("🥉 VERDICT: SILVER - NEEDS WORK")
    verdict = "SILVER"
else:
    print("🔴 VERDICT: FAILED - REQUIRES ATTENTION")
    verdict = "FAILED"
print("=" * 80)

# ============================================================================
# SAVE REPORT
# ============================================================================

report = {
    'audit_type': 'OVERNIGHT_SHADOW_AUDIT',
    'started': datetime.now().isoformat(),
    'total_queries': total_queries,
    'results': results,
    'overall': {
        'pass_rate': overall_pass,
        'contamination_rate': overall_contam,
        'acid_test_pass_rate': overall_acid
    },
    'verdict': verdict,
    'failures_count': len(failures),
    'acid_failures_count': len(acid_failures),
    'sample_failures': failures[:20],
    'acid_failures': acid_failures[:20]
}

with open('/app/overnight_shadow_audit_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n💾 Full report saved to: /app/overnight_shadow_audit_report.json")
print("=" * 80)
