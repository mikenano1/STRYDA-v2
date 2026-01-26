#!/usr/bin/env python3
"""
⚡ STRYDA V4 NIGHTLY AUDITOR SERVICE
=====================================
Permanent Background Service for Automated Quality Assurance

Protocol: LAW 9 - The Shadow Audit
Trigger: Daily at 02:00 AM (configurable via cron)
Purpose: Machine-Breaking stress test on all Mastery Segments

Usage:
  Manual:  python3 /app/services/nightly_auditor.py
  Cron:    0 2 * * * /usr/bin/python3 /app/services/nightly_auditor.py

Created: January 2026
Maintained By: STRYDA Data Pipeline Team
"""
import os
import sys
import re
import json
import random
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai

# Import Emergent LLM
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    HAS_EMERGENT = True
except ImportError:
    HAS_EMERGENT = False

# ==============================================================================
# CONFIGURATION
# ==============================================================================

DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')

LOG_FILE = '/app/logs/nightly_mastery.log'
REPORT_DIR = '/app/logs/audit_reports'

# Mastery Segments Configuration
MASTERY_SEGMENTS = {
    'bremick': {
        'name': 'Bremick Fasteners',
        'source_pattern': 'Bremick%',
        'sample_size': 100,
        'status': 'PLATINUM',
        'hallucination_keywords': [
            'nzs 3604', 'nzs3604', 'timber span', 'rafter span', 'joist span',
            'bearer span', 'purlin span', 'wind zone', 'timber grade',
            '90x45', '140x45', '190x45', '240x45', 'roof span', 'floor span'
        ],
        'expected_keywords': [
            'proof load', 'tensile', 'hardness', 'hex nut', 'hex bolt',
            'grade 8', 'class 8', 'unc', 'unf', 'metric', 'spanner'
        ]
    },
    # Future segments to be added:
    # 'pryda': { ... },
    # 'simpson': { ... },
    # 'ecko': { ... },
}

openai_client = openai.OpenAI(api_key=OPENAI_KEY)

# ==============================================================================
# LOGGING
# ==============================================================================

def log(message, level='INFO'):
    """Append to nightly mastery log"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_line)
    
    print(log_line.strip())


def log_section(title):
    """Log a section header"""
    separator = '=' * 70
    log(separator)
    log(f"  {title}")
    log(separator)

# ==============================================================================
# GOD TIER LAW APPLICATION
# ==============================================================================

def apply_god_tier_laws(query):
    """Expand technical terms for search"""
    expanded_terms = []
    
    # LAW 1: Metric Thread
    metric_matches = re.findall(r'\bM(\d{1,3})\b', query, re.IGNORECASE)
    for val in metric_matches:
        expanded_terms.extend([val, f"size {val}", f"Size: {val}"])
    
    # LAW 4: Imperial Fraction
    fraction_map = {
        '1/4': '0.25', '3/8': '0.375', '1/2': '0.5', 
        '5/8': '0.625', '3/4': '0.75', '7/8': '0.875'
    }
    for frac, decimal in fraction_map.items():
        if frac in query.lower():
            expanded_terms.extend([decimal, f"{frac} inch"])
    
    if expanded_terms:
        return f"{query} {' '.join(expanded_terms)}"
    return query

# ==============================================================================
# TRUTH MAP - GROUND TRUTH VALUES
# ==============================================================================

TRUTH_MAP = {
    'bremick': {
        # Format: 'query_signature': 'expected_value_pattern'
        'proof_load_1/2_unc_grade_8': r'21[0-9]{3}',
        'proof_load_m12_class_8': r'74[0-9]{3}',
        'proof_load_m10_class_8': r'50[0-9]{3}',
        'tensile_m12_class_8.8': r'800\s*MPa',
        'hardness_grade_8': r'\d{2}\s*HRC',
    }
}

# ==============================================================================
# TRAP QUESTION GENERATOR
# ==============================================================================

def generate_trap_questions(segment_key, count=100):
    """Generate randomized trap questions for a segment"""
    segment = MASTERY_SEGMENTS.get(segment_key, {})
    questions = []
    
    if segment_key == 'bremick':
        # Size variations
        sizes_imperial = ['1/4', '5/16', '3/8', '7/16', '1/2', '9/16', '5/8', '3/4', '7/8']
        sizes_metric = ['M6', 'M8', 'M10', 'M12', 'M14', 'M16', 'M20', 'M24']
        
        # Property variations
        properties = [
            ('proof load', ['proof load', 'proof strength', 'load capacity']),
            ('tensile strength', ['tensile strength', 'tensile', 'ultimate tensile', 'UTS']),
            ('hardness', ['hardness', 'HV', 'HRC', 'Rockwell hardness']),
        ]
        
        # Product variations
        products = ['hex nut', 'hex bolt', 'flange bolt', 'lock nut', 'set screw']
        grades = ['grade 5', 'grade 8', 'class 4.6', 'class 8.8']
        finishes = ['zinc', 'black', 'galvanised', 'stainless']
        
        # Generate combinations
        for _ in range(count):
            size = random.choice(sizes_imperial + sizes_metric)
            prop_base, prop_variants = random.choice(properties)
            prop = random.choice(prop_variants)
            product = random.choice(products)
            grade = random.choice(grades)
            finish = random.choice(finishes) if random.random() > 0.5 else ''
            
            # Build query
            query_parts = [f"What is the {prop} for"]
            query_parts.append(size)
            if finish:
                query_parts.append(finish)
            query_parts.append(grade)
            query_parts.append(f"Bremick {product}?")
            
            query = ' '.join(query_parts)
            
            questions.append({
                'query': query,
                'segment': segment_key,
                'size': size,
                'property': prop_base,
                'product': product,
                'grade': grade,
                'trap_type': 'value_lookup'
            })
        
        # Add cross-domain traps (10% of questions)
        cross_domain_templates = [
            "What timber span should I use with {size} bolts?",
            "NZS 3604 requirements for {size} fasteners",
            "Wind zone specifications for {product} connections",
            "Rafter spacing for {grade} {product} fixings",
        ]
        
        for _ in range(count // 10):
            template = random.choice(cross_domain_templates)
            size = random.choice(sizes_metric)
            product = random.choice(products)
            grade = random.choice(grades)
            
            query = template.format(size=size, product=product, grade=grade)
            questions.append({
                'query': query,
                'segment': segment_key,
                'trap_type': 'cross_domain'
            })
    
    random.shuffle(questions)
    return questions[:count]

# ==============================================================================
# RETRIEVAL ENGINE
# ==============================================================================

def get_embedding(text):
    """Get embedding for query"""
    r = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
        dimensions=1536
    )
    return r.data[0].embedding


def retrieve_context(query, segment_key, top_k=10):
    """Retrieve context from specific segment"""
    segment = MASTERY_SEGMENTS.get(segment_key, {})
    pattern = segment.get('source_pattern', '%')
    
    expanded = apply_god_tier_laws(query)
    emb = get_embedding(expanded)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content, source, page, 
               1 - (embedding <=> %s::vector) as score
        FROM documents
        WHERE source LIKE %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (emb, pattern, emb, top_k))
    
    results = cur.fetchall()
    conn.close()
    
    return [{'content': r[0], 'source': r[1], 'page': r[2], 'score': r[3]} for r in results]


async def generate_answer(query, context_chunks, segment_key):
    """Generate RAG answer"""
    if not HAS_EMERGENT:
        return "ERROR: Emergent LLM not available"
    
    segment = MASTERY_SEGMENTS.get(segment_key, {})
    
    context = "\n\n---\n\n".join([
        f"[Source: {c['source']} | Page {c['page']} | Score: {c['score']:.2%}]\n{c['content']}"
        for c in context_chunks[:8]
    ])
    
    user_prompt = f"""QUERY: {query}

CONTEXT ({segment.get('name', 'Technical Data')}):
{context}

INSTRUCTIONS:
1. Answer ONLY from the provided context
2. Provide EXACT numeric values with source citations
3. Format: "Value: [X] (Source: [filename], Page [Y])"
4. If not found, say "Not found in {segment.get('name', 'data')}"
5. Do NOT reference NZS 3604, timber spans, or building codes"""

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"nightly-audit-{hashlib.md5(query.encode()).hexdigest()[:8]}",
        system_message="You are a technical data retrieval assistant. Provide precise, cited answers."
    ).with_model("gemini", "gemini-2.5-flash")
    
    response = await chat.send_message(UserMessage(text=user_prompt))
    return response

# ==============================================================================
# FAILURE DETECTION
# ==============================================================================

def check_hallucination(response_text, segment_key):
    """Check for hallucination keywords"""
    segment = MASTERY_SEGMENTS.get(segment_key, {})
    keywords = segment.get('hallucination_keywords', [])
    
    response_lower = response_text.lower()
    found = [kw for kw in keywords if kw in response_lower]
    return found


def check_retrieval_quality(context_chunks, segment_key):
    """Check if retrieval got relevant content"""
    segment = MASTERY_SEGMENTS.get(segment_key, {})
    pattern = segment.get('source_pattern', '').replace('%', '').lower()
    
    if not context_chunks:
        return {'success': False, 'reason': 'No context retrieved'}
    
    relevant_count = sum(1 for c in context_chunks if pattern in c['source'].lower())
    avg_score = sum(c['score'] for c in context_chunks) / len(context_chunks)
    
    return {
        'success': relevant_count >= 3 and avg_score > 0.3,
        'relevant_chunks': relevant_count,
        'avg_score': avg_score
    }

# ==============================================================================
# MAIN AUDIT FUNCTION
# ==============================================================================

async def run_segment_audit(segment_key):
    """Run full audit on a segment"""
    segment = MASTERY_SEGMENTS.get(segment_key)
    if not segment:
        log(f"Unknown segment: {segment_key}", 'ERROR')
        return None
    
    log_section(f"AUDITING SEGMENT: {segment['name']}")
    log(f"Status: {segment['status']}")
    log(f"Sample Size: {segment['sample_size']}")
    
    # Generate questions
    questions = generate_trap_questions(segment_key, segment['sample_size'])
    log(f"Generated {len(questions)} trap questions")
    
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
        
        if i % 20 == 0:
            log(f"Progress: {i}/{len(questions)} ({i/len(questions)*100:.0f}%)")
        
        try:
            # Retrieve
            context = retrieve_context(query, segment_key)
            retrieval_check = check_retrieval_quality(context, segment_key)
            
            # Generate answer
            answer = await generate_answer(query, context, segment_key)
            
            # Check failures
            hallucinations = check_hallucination(answer, segment_key)
            
            is_critical = len(hallucinations) > 0
            is_retrieval_fail = not retrieval_check['success']
            
            if is_critical:
                stats['critical_fails'] += 1
                status = 'CRITICAL_FAIL'
            elif is_retrieval_fail:
                stats['retrieval_fails'] += 1
                status = 'RETRIEVAL_FAIL'
            else:
                stats['passed'] += 1
                status = 'PASS'
            
            results.append({
                'query': query,
                'status': status,
                'hallucinations': hallucinations,
                'retrieval_score': retrieval_check.get('avg_score', 0),
                'answer_snippet': answer[:150] if answer else ''
            })
            
        except Exception as e:
            stats['errors'] += 1
            results.append({
                'query': query,
                'status': 'ERROR',
                'error': str(e)[:100]
            })
        
        # Rate limit protection
        await asyncio.sleep(0.3)
    
    # Calculate success rate
    success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
    
    # Log summary
    log_section(f"SEGMENT AUDIT COMPLETE: {segment['name']}")
    log(f"Total Questions: {stats['total']}")
    log(f"PASSED: {stats['passed']} ({success_rate:.1f}%)")
    log(f"CRITICAL FAILS: {stats['critical_fails']}")
    log(f"RETRIEVAL FAILS: {stats['retrieval_fails']}")
    log(f"ERRORS: {stats['errors']}")
    
    # Determine segment health
    if success_rate >= 90:
        health = 'PLATINUM ✅'
    elif success_rate >= 75:
        health = 'GOLD 🟡'
    elif success_rate >= 50:
        health = 'SILVER 🟠'
    else:
        health = 'NEEDS REPAIR 🔴'
    
    log(f"SEGMENT HEALTH: {health}")
    
    return {
        'segment': segment_key,
        'name': segment['name'],
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
        'success_rate': success_rate,
        'health': health,
        'results': results
    }


async def run_nightly_audit():
    """Run full nightly audit on all segments"""
    log_section("V4 NIGHTLY AUDITOR SERVICE STARTED")
    log(f"Timestamp: {datetime.now().isoformat()}")
    log(f"Segments to Audit: {list(MASTERY_SEGMENTS.keys())}")
    
    all_reports = []
    
    for segment_key in MASTERY_SEGMENTS:
        try:
            report = await run_segment_audit(segment_key)
            if report:
                all_reports.append(report)
        except Exception as e:
            log(f"Failed to audit {segment_key}: {e}", 'ERROR')
    
    # Save detailed report
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = f"{REPORT_DIR}/audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'segments_audited': len(all_reports),
            'reports': all_reports
        }, f, indent=2)
    
    log(f"Detailed report saved: {report_file}")
    
    # Final summary
    log_section("NIGHTLY AUDIT COMPLETE")
    for r in all_reports:
        log(f"  {r['name']}: {r['health']} ({r['success_rate']:.1f}%)")
    
    log(f"Completed: {datetime.now().isoformat()}")
    
    return all_reports


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    asyncio.run(run_nightly_audit())
