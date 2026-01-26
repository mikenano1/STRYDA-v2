#!/usr/bin/env python3
"""
⚡ STRYDA V4 PRYDA RED-TEAM AUDIT
=================================
50 "Machine-Breaking" queries targeting SG8 vs SG10 timber grade capacities.

Target: 0% hallucination on characteristic capacities
Focus: kN load differences between timber grades

Protocol: LAW 9 - The Shadow Audit
"""
import os
import sys
import re
import json
import random
import asyncio
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Config
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# ==============================================================================
# PRYDA HALLUCINATION KEYWORDS
# ==============================================================================
HALLUCINATION_KEYWORDS = [
    # Wrong domain
    'nzs 3604', 'nzs3604', 'timber span', 'rafter span', 'joist span',
    'bearer span', 'purlin span', 'roof span', 'floor span',
    '90x45', '140x45', '190x45', '240x45',
    # Evasions
    'consult the manual', 'refer to documentation', 'contact manufacturer',
    'beyond scope', 'cannot determine', 'not available'
]

# ==============================================================================
# GOD TIER LAW EXPANSION
# ==============================================================================
def apply_god_tier_laws(query):
    """Expand technical terms for search"""
    expanded = query
    
    # Timber grade expansions
    if 'sg8' in query.lower():
        expanded += ' SG8 stress grade 8 timber'
    if 'sg10' in query.lower():
        expanded += ' SG10 stress grade 10 timber'
    if 'sg12' in query.lower():
        expanded += ' SG12 stress grade 12 timber'
    
    # Joint group expansions
    if 'j2' in query.lower():
        expanded += ' J2 joint group radiata pine'
    if 'jd4' in query.lower():
        expanded += ' JD4 joint group hardwood'
    
    # Product code expansions
    product_codes = re.findall(r'\b([A-Z]{1,3}\s*\d+(?:/\d+)?)\b', query)
    for code in product_codes:
        expanded += f' {code} Pryda connector'
    
    return expanded

# ==============================================================================
# 50 RED-TEAM QUERIES - SG8 vs SG10 FOCUS
# ==============================================================================
def generate_pryda_trap_questions():
    """
    Generate 50 trap questions targeting:
    - SG8 vs SG10 capacity differences
    - Joint group specific loads
    - Product code + timber grade combinations
    """
    questions = []
    
    # CATEGORY 1: Direct SG8 vs SG10 comparisons (15 questions)
    sg_comparison_templates = [
        "What is the capacity difference between SG8 and SG10 for a {product}?",
        "Compare the kN load rating of {product} in SG8 versus SG10 timber",
        "Is there a different capacity for {product} when using SG8 compared to SG10?",
        "{product} characteristic capacity in SG8 timber?",
        "{product} load capacity for SG10 timber?",
    ]
    
    products = [
        'joist hanger', 'H2 connector', 'PB 90 post anchor',
        'tie-down strap', 'bracing anchor', 'truss boot',
        'nail plate', 'flat strap', 'angle bracket'
    ]
    
    for template in sg_comparison_templates:
        for product in random.sample(products, 3):
            questions.append({
                'query': template.format(product=product),
                'category': 'sg_comparison',
                'expected_domain': 'pryda_connectors',
                'trap_type': 'timber_grade_differentiation'
            })
    
    # CATEGORY 2: Joint Group Specific (10 questions)
    joint_templates = [
        "What is the {property} for Pryda {product} in joint group {jg}?",
        "{product} capacity in {jg} timber joint group?",
    ]
    
    joint_groups = ['J2', 'J3', 'J4', 'JD4', 'JD5']
    properties = ['uplift capacity', 'shear capacity', 'characteristic load']
    
    for _ in range(10):
        template = random.choice(joint_templates)
        product = random.choice(products)
        jg = random.choice(joint_groups)
        prop = random.choice(properties)
        questions.append({
            'query': template.format(product=product, jg=jg, property=prop),
            'category': 'joint_group',
            'expected_domain': 'pryda_connectors',
            'trap_type': 'joint_group_specificity'
        })
    
    # CATEGORY 3: Specific kN Value Lookups (10 questions)
    kn_lookup_queries = [
        "What is the kN capacity of Pryda H2 connector?",
        "Pryda PB 90 post anchor uplift load in kN?",
        "Characteristic capacity of Pryda joist hanger JH 120/45?",
        "Bracing anchor BA 100 design load?",
        "Pryda framing anchor shear capacity?",
        "Truss boot TB uplift rating?",
        "Nail plate NP load capacity per 100mm?",
        "Flat strap FS tensile capacity?",
        "Multi-grip connector capacity?",
        "Pryda cyclonic tie-down C3 zone rating?",
    ]
    
    for q in kn_lookup_queries:
        questions.append({
            'query': q,
            'category': 'kn_lookup',
            'expected_domain': 'pryda_connectors',
            'trap_type': 'exact_value'
        })
    
    # CATEGORY 4: Installation & Nailing Pattern (5 questions)
    install_queries = [
        "What nailing pattern is required for Pryda H2 to achieve full capacity?",
        "Minimum nail count for joist hanger JH to SG8 timber?",
        "Edge distance requirement for Pryda post anchor?",
        "Fixing pattern for tie-down strap to achieve rated capacity?",
        "Can I use 3.15mm nails instead of 3.75mm for Pryda connectors?",
    ]
    
    for q in install_queries:
        questions.append({
            'query': q,
            'category': 'installation',
            'expected_domain': 'pryda_connectors',
            'trap_type': 'installation_spec'
        })
    
    # CATEGORY 5: Cross-Domain Traps (5 questions) - Should detect hallucination
    cross_domain_traps = [
        "What timber span should I use with Pryda connectors?",
        "NZS 3604 requirements for Pryda joist hangers?",
        "Wind zone calculation for Pryda tie-downs?",
        "Bearer size for Pryda post anchor connection?",
        "Floor joist spacing with Pryda connectors?",
    ]
    
    for q in cross_domain_traps:
        questions.append({
            'query': q,
            'category': 'cross_domain',
            'expected_domain': 'should_clarify',
            'trap_type': 'cross_domain_trap'
        })
    
    # CATEGORY 6: Nomenclature Variations (5 questions)
    nomenclature_queries = [
        "Pryda H-2 connector capacity",  # H-2 vs H2
        "JH120/45 joist hanger load",     # No space
        "joist hanger 120/45 Pryda",      # Reversed order
        "Pryda connector for 45mm timber", # Dimension first
        "tie down vs tie-down Pryda capacity", # Hyphenation
    ]
    
    for q in nomenclature_queries:
        questions.append({
            'query': q,
            'category': 'nomenclature',
            'expected_domain': 'pryda_connectors',
            'trap_type': 'naming_variation'
        })
    
    random.shuffle(questions)
    return questions[:50]  # Ensure exactly 50

# ==============================================================================
# RETRIEVAL & GENERATION
# ==============================================================================
def get_embedding(text):
    """Get embedding for query"""
    r = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
        dimensions=1536
    )
    return r.data[0].embedding


def retrieve_pryda_context(query, top_k=12):
    """Retrieve context from Pryda documents"""
    expanded = apply_god_tier_laws(query)
    emb = get_embedding(expanded)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content, source, page, 
               1 - (embedding <=> %s::vector) as score
        FROM documents
        WHERE source LIKE 'Pryda%%'
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (emb, emb, top_k))
    
    results = cur.fetchall()
    conn.close()
    
    return [{'content': r[0], 'source': r[1], 'page': r[2], 'score': r[3]} for r in results]


async def generate_rag_answer(query, context_chunks):
    """Generate RAG answer using Gemini"""
    context = "\n\n---\n\n".join([
        f"[Source: {c['source']} | Page {c['page']} | Score: {c['score']:.2%}]\n{c['content']}"
        for c in context_chunks[:8]
    ])
    
    user_prompt = f"""QUERY: {query}

CONTEXT (Pryda Technical Data):
{context}

INSTRUCTIONS:
1. Answer ONLY from the provided Pryda context
2. For capacity questions, provide EXACT kN values with source citations
3. For SG8 vs SG10 comparisons, explicitly state both values if different
4. Format: "Value: [X] kN (Source: [filename], Page [Y])"
5. If asking about timber grades, specify which grade the capacity applies to
6. If data not found, say "Not found in Pryda data"
7. Do NOT reference NZS 3604, timber spans, or general building code
8. Do NOT tell user to "consult the manual" - provide the actual data"""

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"pryda-audit-{hashlib.md5(query.encode()).hexdigest()[:8]}",
        system_message="You are a technical data retrieval assistant for Pryda structural connectors. Provide precise, cited answers with exact kN values."
    ).with_model("gemini", "gemini-2.5-flash")
    
    response = await chat.send_message(UserMessage(text=user_prompt))
    return response

# ==============================================================================
# FAILURE DETECTION
# ==============================================================================
def check_hallucination(response_text):
    """Check for hallucination keywords"""
    response_lower = response_text.lower()
    found = [kw for kw in HALLUCINATION_KEYWORDS if kw in response_lower]
    return found


def check_capacity_answer(response_text, category):
    """Check if capacity question has a numeric answer"""
    if category in ['kn_lookup', 'sg_comparison', 'joint_group']:
        # Should have a numeric value
        has_kn = bool(re.search(r'\d+\.?\d*\s*kN', response_text, re.IGNORECASE))
        has_number = bool(re.search(r'\b\d+\.?\d*\b', response_text))
        return has_kn or has_number
    return True  # Non-capacity questions pass by default


def check_retrieval_quality(context_chunks):
    """Check retrieval quality"""
    if not context_chunks:
        return {'success': False, 'reason': 'No context'}
    
    pryda_count = sum(1 for c in context_chunks if 'pryda' in c['source'].lower())
    avg_score = sum(c['score'] for c in context_chunks) / len(context_chunks)
    
    return {
        'success': pryda_count >= 3 and avg_score > 0.25,
        'pryda_chunks': pryda_count,
        'avg_score': avg_score
    }

# ==============================================================================
# MAIN AUDIT
# ==============================================================================
async def run_pryda_audit():
    """Execute full V4 Pryda Red-Team Audit"""
    
    print("=" * 80)
    print("   ⚡ STRYDA V4 PRYDA RED-TEAM AUDIT")
    print(f"   Started: {datetime.now().isoformat()}")
    print("   Target: 0% hallucination on characteristic capacities")
    print("   Focus: SG8 vs SG10 timber grade differences")
    print("=" * 80)
    
    # Generate questions
    questions = generate_pryda_trap_questions()
    print(f"\n📋 Generated {len(questions)} trap questions")
    
    # Count by category
    categories = {}
    for q in questions:
        cat = q.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("   Distribution:")
    for cat, count in sorted(categories.items()):
        print(f"      {cat}: {count}")
    
    # Execute
    print(f"\n⚡ EXECUTING {len(questions)} QUERIES...")
    print("-" * 60)
    
    results = []
    stats = {
        'total': len(questions),
        'passed': 0,
        'critical_fails': 0,
        'retrieval_fails': 0,
        'data_fails': 0,
        'errors': 0
    }
    
    for i, q in enumerate(questions, 1):
        query = q['query']
        category = q.get('category', 'unknown')
        
        if i % 10 == 0:
            print(f"\n   [{i}/{len(questions)}] Progress: {i/len(questions)*100:.0f}%")
        
        try:
            # Retrieve
            context = retrieve_pryda_context(query)
            retrieval_check = check_retrieval_quality(context)
            
            # Generate
            answer = await generate_rag_answer(query, context)
            
            # Check failures
            hallucinations = check_hallucination(answer)
            has_capacity = check_capacity_answer(answer, category)
            
            is_critical = len(hallucinations) > 0
            is_retrieval_fail = not retrieval_check['success']
            is_data_fail = not has_capacity and category in ['kn_lookup', 'sg_comparison']
            
            # Cross-domain traps SHOULD have hallucinations echoed (expected behavior)
            if category == 'cross_domain' and is_critical:
                # Check if it's just echoing the query term vs actual hallucination
                if 'not found' in answer.lower() or 'cannot provide' in answer.lower():
                    is_critical = False  # Proper response to cross-domain
            
            status = "✅ PASS"
            if is_critical:
                status = "🔴 CRITICAL"
                stats['critical_fails'] += 1
            elif is_retrieval_fail:
                status = "🟠 RETRIEVAL"
                stats['retrieval_fails'] += 1
            elif is_data_fail:
                status = "🟡 DATA"
                stats['data_fails'] += 1
            else:
                stats['passed'] += 1
            
            results.append({
                'query': query,
                'category': category,
                'trap_type': q.get('trap_type'),
                'status': status,
                'is_critical': is_critical,
                'hallucinations': hallucinations,
                'retrieval_score': retrieval_check.get('avg_score', 0),
                'has_numeric': has_capacity,
                'answer_snippet': answer[:200] if answer else ''
            })
            
        except Exception as e:
            stats['errors'] += 1
            results.append({
                'query': query,
                'category': category,
                'status': '❌ ERROR',
                'error': str(e)[:50]
            })
        
        await asyncio.sleep(0.3)
    
    # Final Report
    success_rate = (stats['passed'] / stats['total']) * 100
    hallucination_rate = (stats['critical_fails'] / stats['total']) * 100
    
    print(f"\n{'='*80}")
    print(f"   📊 V4 PRYDA AUDIT - FINAL REPORT")
    print(f"{'='*80}")
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  PRYDA SEGMENT AUDIT RESULTS                               │
├─────────────────────────────────────────────────────────────┤
│  Total Queries:        {stats['total']:4}                                  │
│  ✅ PASSED:            {stats['passed']:4} ({stats['passed']/stats['total']*100:.1f}%)                           │
│  🔴 CRITICAL FAILS:    {stats['critical_fails']:4} (Hallucination)                  │
│  🟠 RETRIEVAL FAILS:   {stats['retrieval_fails']:4} (Wrong/No Context)              │
│  🟡 DATA FAILS:        {stats['data_fails']:4} (Missing kN Value)               │
│  ❌ ERRORS:            {stats['errors']:4}                                    │
├─────────────────────────────────────────────────────────────┤
│  📈 SUCCESS RATE:      {success_rate:5.1f}%                              │
│  🚨 HALLUCINATION:     {hallucination_rate:5.1f}%                              │
│  TARGET: 0%            {'✅ ACHIEVED' if hallucination_rate == 0 else '❌ NOT MET'}                           │
└─────────────────────────────────────────────────────────────┘
""")
    
    # Certification Level
    if success_rate >= 90:
        cert = '⚡ PLATINUM'
    elif success_rate >= 75:
        cert = '✅ GOLD'
    elif success_rate >= 50:
        cert = '🟡 SILVER'
    else:
        cert = '🔴 NEEDS REPAIR'
    
    print(f"   CERTIFICATION: {cert}")
    
    # List failures
    if stats['critical_fails'] > 0:
        print(f"\n🔴 CRITICAL FAILURES (HALLUCINATION):")
        print("-" * 60)
        for r in results:
            if r.get('is_critical'):
                print(f"   Q: {r['query'][:55]}...")
                print(f"   Hallucinations: {r['hallucinations']}")
                print()
    
    if stats['data_fails'] > 0:
        print(f"\n🟡 DATA FAILURES (Missing kN):")
        print("-" * 60)
        for r in results:
            if r.get('status') == '🟡 DATA':
                print(f"   Q: {r['query'][:55]}...")
                print()
    
    # Category breakdown
    print(f"\n📊 RESULTS BY CATEGORY:")
    print("-" * 60)
    cat_stats = {}
    for r in results:
        cat = r.get('category', 'unknown')
        if cat not in cat_stats:
            cat_stats[cat] = {'total': 0, 'passed': 0}
        cat_stats[cat]['total'] += 1
        if r.get('status') == '✅ PASS':
            cat_stats[cat]['passed'] += 1
    
    for cat, s in sorted(cat_stats.items()):
        rate = (s['passed'] / s['total']) * 100 if s['total'] > 0 else 0
        print(f"   {cat:20} {s['passed']:2}/{s['total']:2} ({rate:.0f}%)")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'segment': 'Pryda Structural Connectors',
        'protocol': 'V4 Red-Team Audit',
        'focus': 'SG8 vs SG10 timber grade differences',
        'total_questions': stats['total'],
        'success_rate': success_rate,
        'hallucination_rate': hallucination_rate,
        'certification': cert,
        'stats': stats,
        'category_breakdown': cat_stats,
        'results': results
    }
    
    report_path = f"/app/logs/audit_reports/pryda_v4_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Full report: {report_path}")
    print(f"\n   Completed: {datetime.now().isoformat()}")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    asyncio.run(run_pryda_audit())
