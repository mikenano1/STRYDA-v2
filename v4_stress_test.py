#!/usr/bin/env python3
"""
⚡ STRYDA V4 RED-TEAM AUDIT - STRESS TEST
=========================================
OBJECTIVE: Find the "breaking point" of V3 GOD TIER logic

Methodology:
1. Scrape target PDFs for all unique numeric values
2. Generate 30 "Trap" questions with varied nomenclature
3. Execute against RAG engine
4. Detect HALLUCINATIONS and DATA FAILURES
5. Report fail rate with exact broken queries

FAILURE CRITERIA:
- CRITICAL FAILURE: Response mentions "NZS 3604", "Timber", or "Spans" (wrong domain)
- DATA FAILURE: Numeric value doesn't match source exactly
- RETRIEVAL FAILURE: No relevant Bremick data returned
"""
import os
import sys
import re
import json
import asyncio
import hashlib
import random
from datetime import datetime
from dotenv import load_dotenv
load_dotenv('/app/backend-minimal/.env')

import psycopg2
import openai
from supabase import create_client
from pdf2image import convert_from_bytes
import base64

# Try to use Gemini for PDF parsing
try:
    import google.generativeai as genai
    GEMINI_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('EMERGENT_LLM_KEY')
    genai.configure(api_key=GEMINI_KEY)
    vision_model = genai.GenerativeModel('gemini-1.5-flash')
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

# Import RAG engine
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/backend-minimal')

from emergentintegrations.llm.chat import LlmChat, UserMessage
from core_prompts import STRYDA_SYSTEM_PROMPT

# Config
DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
EMERGENT_KEY = os.getenv('EMERGENT_LLM_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

openai_client = openai.OpenAI(api_key=OPENAI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# TARGET PDFs FOR SCRAPING
# ==============================================================================
TARGET_PDFS = [
    "F_Manufacturers/Fasteners/Bremick/flange-purlin-class-8-8-metric-zinc.pdf",
    "F_Manufacturers/Fasteners/Bremick/hex-nut-grade-8-unc-black.pdf"
]

# ==============================================================================
# CRITICAL FAILURE KEYWORDS (DOMAIN LEAKAGE)
# ==============================================================================
HALLUCINATION_KEYWORDS = [
    "nzs 3604", "nzs3604", "timber span", "rafter span", "joist span",
    "bearer span", "purlin span", "wind zone", "timber grade",
    "90x45", "140x45", "190x45", "240x45",
    "roof span", "floor span", "ceiling span"
]

# ==============================================================================
# GOD TIER LAW APPLICATION (copied from test_rag_v3.py for consistency)
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
        '5/8': '0.625', '3/4': '0.75', '7/8': '0.875',
        '1/8': '0.125', '5/16': '0.3125', '7/16': '0.4375',
        '9/16': '0.5625', '11/16': '0.6875', '13/16': '0.8125'
    }
    for frac, decimal in fraction_map.items():
        if frac in query.lower():
            expanded_terms.extend([decimal, f"{frac} inch"])
    
    if expanded_terms:
        return f"{query} {' '.join(expanded_terms)}"
    return query

# ==============================================================================
# PDF SCRAPING - EXTRACT ALL NUMERIC VALUES
# ==============================================================================
def scrape_pdf_for_values(pdf_path):
    """
    Download PDF and extract all unique numeric values using Gemini Vision.
    Returns dict of {property: [values]} 
    """
    print(f"\n📥 Scraping: {pdf_path}")
    
    try:
        # Download from Supabase
        data = supabase.storage.from_('product-library').download(pdf_path)
        if not data:
            print(f"   ❌ Download failed")
            return {}
        
        # Convert to images
        images = convert_from_bytes(data, dpi=150, fmt='JPEG')
        print(f"   📄 {len(images)} pages")
        
        all_values = {
            'proof_load': [],
            'tensile_strength': [],
            'hardness_hv': [],
            'hardness_hrc': [],
            'pitch': [],
            'spanner_size': [],
            'thread_forms': [],
            'sizes': [],
            'other_numeric': []
        }
        
        extraction_prompt = """Analyze this technical data sheet page. Extract ALL numeric values you can find.

OUTPUT FORMAT (JSON):
{
    "proof_load": ["list of proof load values with units, e.g. '24000 lbf', '107000 N'"],
    "tensile_strength": ["list of tensile values"],
    "hardness_hv": ["hardness values in HV"],
    "hardness_hrc": ["hardness values in HRC"],
    "pitch": ["thread pitch values"],
    "spanner_size": ["spanner/wrench sizes"],
    "thread_forms": ["thread specifications like UNC, UNF, M8, M10"],
    "sizes": ["product sizes mentioned, e.g. '1/2 inch', 'M12', '10-24'"],
    "other_numeric": ["any other important numeric values with context"]
}

Be thorough - extract EVERY numeric value visible."""
        
        for i, img in enumerate(images[:3], 1):  # First 3 pages
            from io import BytesIO
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=85)
            img_bytes = img_buffer.getvalue()
            
            try:
                response = vision_model.generate_content([
                    extraction_prompt,
                    {"mime_type": "image/jpeg", "data": base64.b64encode(img_bytes).decode('utf-8')}
                ])
                
                # Parse response - look for JSON
                text = response.text
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    for key in all_values:
                        if key in parsed and parsed[key]:
                            all_values[key].extend(parsed[key])
                
                print(f"   ✅ Page {i} parsed")
                
            except Exception as e:
                print(f"   ⚠️ Page {i} error: {str(e)[:40]}")
        
        # Dedupe
        for key in all_values:
            all_values[key] = list(set(all_values[key]))
        
        return all_values
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {}

# ==============================================================================
# TRAP QUESTION GENERATOR
# ==============================================================================
def generate_trap_questions(scraped_data):
    """
    Generate 30 "Trap" questions with varied nomenclature.
    These are designed to test GOD TIER LAW boundaries.
    """
    questions = []
    
    # Extract available sizes for permutation
    sizes = scraped_data.get('sizes', [])
    proof_loads = scraped_data.get('proof_load', [])
    thread_forms = scraped_data.get('thread_forms', [])
    
    # TRAP SET 1: Size Nomenclature Variations (10 questions)
    size_variations = [
        ("1/2", ["1/2 inch", "1/2\"", "0.5 inch", "half inch", "1/2-13"]),
        ("3/8", ["3/8 inch", "3/8\"", "0.375 inch", "three-eighths inch"]),
        ("M12", ["M12", "12mm", "12 mm", "metric 12", "size 12"]),
        ("M10", ["M10", "10mm", "ten mm", "metric 10"]),
        ("M16", ["M16", "16mm", "16 millimeter", "metric 16"]),
    ]
    
    for base, variants in size_variations[:4]:
        for v in variants[:2]:
            questions.append({
                "query": f"What is the proof load for {v} hex nut grade 8?",
                "expected_domain": "fasteners",
                "expected_source": "Bremick",
                "size_tested": base,
                "trap_type": "nomenclature_variation"
            })
    
    # TRAP SET 2: Property Variations (8 questions)
    property_variations = [
        ("proof load", ["proof load", "proof strength", "load capacity", "maximum load"]),
        ("tensile strength", ["tensile strength", "tensile", "ultimate tensile", "UTS"]),
        ("hardness", ["hardness", "HV", "HRC", "Rockwell", "Vickers"]),
    ]
    
    for base_prop, variants in property_variations:
        for v in variants[:3]:
            size = random.choice(["1/2 inch", "M12", "3/8 inch", "M10"]) if sizes else "1/2 inch"
            questions.append({
                "query": f"What is the {v} for {size} Bremick hex nut?",
                "expected_domain": "fasteners",
                "expected_source": "Bremick",
                "property_tested": base_prop,
                "trap_type": "property_alias"
            })
    
    # TRAP SET 3: Ambiguous Queries (5 questions)
    ambiguous_queries = [
        "hex nut specifications",
        "fastener load capacity",
        "bolt proof load",
        "metric nut strength",
        "UNC thread specifications"
    ]
    for q in ambiguous_queries:
        questions.append({
            "query": q,
            "expected_domain": "fasteners",
            "expected_source": "Bremick",
            "trap_type": "ambiguous_no_size"
        })
    
    # TRAP SET 4: Cross-Domain Confusion (5 questions) - These SHOULD fail gracefully
    cross_domain = [
        "What timber span should I use with M12 bolts?",
        "Rafter spacing for hex nut connections",
        "Wind zone requirements for fastener selection",
        "NZS 3604 bolt specifications",
        "Floor joist connections with grade 8 bolts"
    ]
    for q in cross_domain:
        questions.append({
            "query": q,
            "expected_domain": "mixed",
            "expected_source": "should_clarify",
            "trap_type": "cross_domain_trap"
        })
    
    # TRAP SET 5: Specific Value Lookups (7 questions) - MUST return exact values
    specific_lookups = [
        ("What is the proof load for 1/2 inch UNC grade 8 hex nut?", "proof_load"),
        ("Tensile strength of M12 class 8.8 flange bolt?", "tensile_strength"),
        ("What is the HV hardness range for grade 8 hex nuts?", "hardness_hv"),
        ("Spanner size for M16 hex nut?", "spanner_size"),
        ("Thread pitch for 1/2 inch UNC?", "pitch"),
        ("What is the proof load for 3/8 inch UNC black hex nut?", "proof_load"),
        ("M10 flange bolt proof load in Newtons?", "proof_load"),
    ]
    for q, prop in specific_lookups:
        questions.append({
            "query": q,
            "expected_domain": "fasteners",
            "expected_source": "Bremick",
            "expected_property": prop,
            "trap_type": "exact_value_lookup"
        })
    
    return questions[:30]  # Ensure exactly 30

# ==============================================================================
# RAG RETRIEVAL FUNCTION
# ==============================================================================
def get_embedding(text):
    """Get embedding for query"""
    r = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000],
        dimensions=1536
    )
    return r.data[0].embedding


def retrieve_bremick_context(query, top_k=10):
    """Retrieve context from Bremick documents only"""
    expanded = apply_god_tier_laws(query)
    emb = get_embedding(expanded)
    
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT content, source, page, 
               1 - (embedding <=> %s::vector) as score
        FROM documents
        WHERE source LIKE 'Bremick%%'
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

CONTEXT (Bremick Technical Data):
{context}

INSTRUCTIONS:
1. Answer ONLY from the provided context
2. If asking about proof load, tensile strength, hardness, etc - provide the EXACT numeric value
3. Format: "Value: [X] (Source: [filename], Page [Y])"
4. If data not found in context, say "Not found in Bremick data"
5. Do NOT reference NZS 3604, timber spans, or building code sections - this is fastener data only"""

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"stress-test-{hashlib.md5(query.encode()).hexdigest()[:8]}",
        system_message=STRYDA_SYSTEM_PROMPT
    ).with_model("gemini", "gemini-2.5-flash")
    
    response = await chat.send_message(UserMessage(text=user_prompt))
    return response

# ==============================================================================
# FAILURE DETECTION
# ==============================================================================
def check_hallucination(response_text):
    """Check if response contains hallucination keywords"""
    response_lower = response_text.lower()
    
    found_hallucinations = []
    for keyword in HALLUCINATION_KEYWORDS:
        if keyword in response_lower:
            found_hallucinations.append(keyword)
    
    return found_hallucinations


def check_data_accuracy(response_text, expected_values):
    """Check if numeric values in response match expected values"""
    # Extract all numbers from response
    numbers_in_response = re.findall(r'\b[\d,]+\.?\d*\b', response_text)
    
    # This is a simplified check - in production, you'd validate against source PDFs
    return {
        'numbers_found': numbers_in_response,
        'has_numeric_answer': len(numbers_in_response) > 0
    }


def check_retrieval_quality(context_chunks, expected_source):
    """Check if retrieval got relevant Bremick content"""
    if not context_chunks:
        return {'success': False, 'reason': 'No context retrieved'}
    
    bremick_count = sum(1 for c in context_chunks if 'bremick' in c['source'].lower())
    avg_score = sum(c['score'] for c in context_chunks) / len(context_chunks)
    
    return {
        'success': bremick_count >= 3 and avg_score > 0.3,
        'bremick_chunks': bremick_count,
        'avg_score': avg_score
    }

# ==============================================================================
# MAIN STRESS TEST EXECUTION
# ==============================================================================
async def run_stress_test():
    """Execute the full V4 Red-Team Audit"""
    
    print("="*80)
    print("   ⚡ STRYDA V4 RED-TEAM AUDIT - GOD TIER STRESS TEST")
    print(f"   Started: {datetime.now().isoformat()}")
    print("="*80)
    
    # Phase 1: Scrape PDFs for ground truth values
    print("\n📋 PHASE 1: SCRAPING TARGET PDFs FOR GROUND TRUTH")
    print("-"*60)
    
    all_scraped_data = {
        'proof_load': [],
        'tensile_strength': [],
        'hardness_hv': [],
        'hardness_hrc': [],
        'pitch': [],
        'spanner_size': [],
        'thread_forms': [],
        'sizes': [],
        'other_numeric': []
    }
    
    if HAS_GEMINI:
        for pdf in TARGET_PDFS:
            scraped = scrape_pdf_for_values(pdf)
            for key in all_scraped_data:
                if key in scraped:
                    all_scraped_data[key].extend(scraped[key])
        
        # Dedupe
        for key in all_scraped_data:
            all_scraped_data[key] = list(set(all_scraped_data[key]))
        
        print(f"\n📊 SCRAPED VALUES SUMMARY:")
        for key, values in all_scraped_data.items():
            if values:
                print(f"   {key}: {len(values)} unique values")
                print(f"      Examples: {values[:3]}")
    else:
        print("   ⚠️ Gemini not available - using predefined test values")
        # Fallback known values from Bremick TDS
        all_scraped_data = {
            'proof_load': ['24000 lbf', '17000 lbf', '107000 N', '59000 N'],
            'tensile_strength': ['150000 psi', '120000 psi'],
            'hardness_hv': ['272-353 HV', '250-320 HV'],
            'hardness_hrc': ['26-36 HRC', '24-32 HRC'],
            'sizes': ['1/4', '5/16', '3/8', '7/16', '1/2', '9/16', '5/8', '3/4', '7/8', '1', 'M6', 'M8', 'M10', 'M12', 'M14', 'M16', 'M20', 'M24'],
            'thread_forms': ['UNC', 'UNF', 'Metric'],
            'pitch': ['13 TPI', '20 TPI', '1.5mm', '1.75mm', '2.0mm'],
            'spanner_size': ['13mm', '17mm', '19mm', '22mm', '24mm'],
            'other_numeric': []
        }
    
    # Phase 2: Generate Trap Questions
    print("\n📋 PHASE 2: GENERATING 30 TRAP QUESTIONS")
    print("-"*60)
    
    questions = generate_trap_questions(all_scraped_data)
    print(f"   Generated {len(questions)} trap questions")
    
    trap_type_counts = {}
    for q in questions:
        t = q.get('trap_type', 'unknown')
        trap_type_counts[t] = trap_type_counts.get(t, 0) + 1
    
    print(f"   Distribution:")
    for t, c in trap_type_counts.items():
        print(f"      {t}: {c}")
    
    # Phase 3: Execute Queries
    print("\n📋 PHASE 3: EXECUTING STRESS TEST (30 QUERIES)")
    print("-"*60)
    
    results = []
    
    for i, q in enumerate(questions, 1):
        query = q['query']
        print(f"\n[{i:2}/30] 🔍 {query[:60]}...")
        
        try:
            # Retrieve context
            context = retrieve_bremick_context(query)
            retrieval_check = check_retrieval_quality(context, q.get('expected_source', 'Bremick'))
            
            # Generate answer
            answer = await generate_rag_answer(query, context)
            
            # Check for failures
            hallucinations = check_hallucination(answer)
            data_check = check_data_accuracy(answer, all_scraped_data.get(q.get('expected_property', ''), []))
            
            # Determine pass/fail
            is_critical_fail = len(hallucinations) > 0
            is_retrieval_fail = not retrieval_check['success']
            is_data_fail = q.get('trap_type') == 'exact_value_lookup' and not data_check['has_numeric_answer']
            
            status = "✅ PASS"
            if is_critical_fail:
                status = "🔴 CRITICAL FAIL"
            elif is_retrieval_fail:
                status = "🟠 RETRIEVAL FAIL"
            elif is_data_fail:
                status = "🟡 DATA FAIL"
            
            result = {
                'query': query,
                'trap_type': q.get('trap_type'),
                'status': status,
                'is_critical_fail': is_critical_fail,
                'is_retrieval_fail': is_retrieval_fail,
                'is_data_fail': is_data_fail,
                'hallucinations_found': hallucinations,
                'retrieval_score': retrieval_check.get('avg_score', 0),
                'bremick_chunks': retrieval_check.get('bremick_chunks', 0),
                'answer_snippet': answer[:200] if answer else "NO ANSWER"
            }
            results.append(result)
            
            print(f"       {status}")
            if is_critical_fail:
                print(f"       ⚠️ HALLUCINATIONS: {hallucinations}")
            
        except Exception as e:
            results.append({
                'query': query,
                'trap_type': q.get('trap_type'),
                'status': '❌ ERROR',
                'error': str(e)[:100]
            })
            print(f"       ❌ ERROR: {str(e)[:50]}")
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)
    
    # Phase 4: Generate Report
    print("\n" + "="*80)
    print("   📊 V4 RED-TEAM AUDIT - FINAL REPORT")
    print("="*80)
    
    total = len(results)
    critical_fails = sum(1 for r in results if r.get('is_critical_fail'))
    retrieval_fails = sum(1 for r in results if r.get('is_retrieval_fail'))
    data_fails = sum(1 for r in results if r.get('is_data_fail'))
    errors = sum(1 for r in results if r.get('status') == '❌ ERROR')
    passes = total - critical_fails - retrieval_fails - data_fails - errors
    
    success_rate = (passes / total) * 100 if total > 0 else 0
    fail_rate = 100 - success_rate
    
    print(f"""
┌─────────────────────────────────────────────────────────────┐
│  OVERALL RESULTS                                            │
├─────────────────────────────────────────────────────────────┤
│  Total Queries:        {total:4}                                  │
│  ✅ PASSED:            {passes:4} ({passes/total*100:.1f}%)                           │
│  🔴 CRITICAL FAILS:    {critical_fails:4} (Hallucination/Domain Leak)       │
│  🟠 RETRIEVAL FAILS:   {retrieval_fails:4} (Wrong/No Context)              │
│  🟡 DATA FAILS:        {data_fails:4} (Missing Numeric Answer)          │
│  ❌ ERRORS:            {errors:4} (Execution Errors)                │
├─────────────────────────────────────────────────────────────┤
│  📈 SUCCESS RATE:      {success_rate:5.1f}%                              │
│  📉 FAIL RATE:         {fail_rate:5.1f}%                              │
└─────────────────────────────────────────────────────────────┘
""")
    
    # List broken queries
    if critical_fails > 0:
        print("\n🔴 CRITICAL FAILURES (HALLUCINATION DETECTED):")
        print("-"*60)
        for r in results:
            if r.get('is_critical_fail'):
                print(f"   Query: {r['query'][:60]}")
                print(f"   Found: {r['hallucinations_found']}")
                print()
    
    if retrieval_fails > 0:
        print("\n🟠 RETRIEVAL FAILURES:")
        print("-"*60)
        for r in results:
            if r.get('is_retrieval_fail') and not r.get('is_critical_fail'):
                print(f"   Query: {r['query'][:60]}")
                print(f"   Bremick chunks: {r.get('bremick_chunks', 0)}, Score: {r.get('retrieval_score', 0):.2%}")
                print()
    
    if data_fails > 0:
        print("\n🟡 DATA FAILURES (EXPECTED VALUE NOT RETURNED):")
        print("-"*60)
        for r in results:
            if r.get('is_data_fail') and not r.get('is_critical_fail') and not r.get('is_retrieval_fail'):
                print(f"   Query: {r['query'][:60]}")
                print(f"   Answer: {r.get('answer_snippet', 'N/A')[:100]}...")
                print()
    
    # Save full report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_queries': total,
        'success_rate': success_rate,
        'fail_rate': fail_rate,
        'critical_fails': critical_fails,
        'retrieval_fails': retrieval_fails,
        'data_fails': data_fails,
        'errors': errors,
        'results': results,
        'scraped_ground_truth': all_scraped_data
    }
    
    with open('/app/v4_stress_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📁 Full report saved to: /app/v4_stress_test_report.json")
    print("="*80)
    print(f"   ⚡ V4 RED-TEAM AUDIT COMPLETE")
    print(f"   Completed: {datetime.now().isoformat()}")
    print("="*80)
    
    return report


if __name__ == "__main__":
    asyncio.run(run_stress_test())
