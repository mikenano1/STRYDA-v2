#!/usr/bin/env python3
"""
STRYDA-v2 Backend Validation - 50 Real-World Questions
Tests intent classification, retrieval, and citation behavior
"""

import json
import requests
from datetime import datetime

QUESTIONS_FILE = "/app/backend-minimal/training/validation/stryda_v2_validation_questions.json"
RESULTS_FILE = "/app/backend-minimal/training/validation/stryda_v2_validation_results.json"
REPORT_FILE = "/app/backend-minimal/training/validation/stryda_v2_validation_report.md"
API_URL = "http://localhost:8001/api/chat"

print("="*80)
print("STRYDA-V2 BACKEND VALIDATION - 50 QUESTIONS")
print("="*80)

# Load questions
with open(QUESTIONS_FILE, 'r') as f:
    questions = json.load(f)

print(f"\n✅ Loaded {len(questions)} validation questions\n")

# Run validation
results = []
intent_counts = {}
citations_shown_count = 0
doc_type_top_counts = {}

for q in questions:
    if q['id'] % 10 == 0:
        print(f"Progress: {q['id']}/50")
    
    try:
        response = requests.post(
            API_URL,
            json={"message": q['question'], "session_id": f"val_{q['id']}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            intent = data.get('intent', 'unknown')
            citations = data.get('citations', [])
            citations_shown = len(citations) > 0
            
            if citations_shown:
                citations_shown_count += 1
            
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            # Extract top docs from citations (best we can do without internal access)
            top_docs = []
            for cite in citations[:3]:
                top_docs.append({
                    "source": cite.get('source', 'Unknown'),
                    "page": cite.get('page', 0)
                })
            
            result = {
                "question_id": q['id'],
                "trade_hint": q['trade_hint'],
                "question": q['question'],
                "intent": intent,
                "citations_shown": citations_shown,
                "citation_count": len(citations),
                "top_docs": top_docs
            }
            
            results.append(result)
        else:
            results.append({
                "question_id": q['id'],
                "error": f"HTTP {response.status_code}"
            })
    
    except Exception as e:
        results.append({
            "question_id": q['id'],
            "error": str(e)
        })

# Save JSON results
with open(RESULTS_FILE, 'w') as f:
    json.dump(results, f, indent=2)

# Generate markdown report
with open(REPORT_FILE, 'w') as f:
    f.write("# STRYDA-v2 Backend Validation Report\n\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Questions:** {len(results)}\n\n")
    
    f.write("## Overall Stats\n\n")
    f.write(f"- Total questions: {len(results)}\n")
    f.write(f"- Citations shown: {citations_shown_count}/{len(results)} ({citations_shown_count/len(results)*100:.1f}%)\n")
    f.write(f"- Citations hidden: {len(results) - citations_shown_count}/{len(results)}\n\n")
    
    f.write("## Intent Distribution\n\n")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        f.write(f"- **{intent}**: {count} questions\n")
    
    f.write("\n## Citations by Intent\n\n")
    for intent in sorted(intent_counts.keys()):
        intent_results = [r for r in results if r.get('intent') == intent]
        with_citations = sum(1 for r in intent_results if r.get('citations_shown', False))
        pct = (with_citations/len(intent_results)*100) if intent_results else 0
        f.write(f"- **{intent}**: {with_citations}/{len(intent_results)} ({pct:.1f}%) showed citations\n")
    
    f.write("\n## Sample Results (First 15)\n\n")
    for r in results[:15]:
        f.write(f"### Q{r['question_id']}: {r['trade_hint']}\n\n")
        f.write(f"**Question:** {r['question']}\n\n")
        f.write(f"- Intent: `{r.get('intent', 'N/A')}`\n")
        f.write(f"- Citations: {r.get('citation_count', 0)}\n")
        if r.get('top_docs'):
            f.write(f"- Top sources: {', '.join([d['source'] for d in r['top_docs']])}\n")
        f.write("\n")
    
    f.write("\n## Interesting Cases\n\n")
    
    # Product_info questions
    product_results = [r for r in results if r.get('intent') == 'product_info']
    if product_results:
        f.write("### Product_Info Questions (Should have 0 citations):\n\n")
        for r in product_results[:5]:
            f.write(f"- Q{r['question_id']}: {r['question'][:60]}...\n")
            f.write(f"  - Citations: {r['citation_count']}\n\n")
    
    # Legacy queries (looking for old building references)
    legacy_keywords = ['2005', '2007', '2010', '2014', '2017', 'older', 'before', 'pre-']
    legacy_candidates = [r for r in results if any(kw in r['question'].lower() for kw in legacy_keywords)]
    if legacy_candidates:
        f.write("### Legacy/Historical Queries:\n\n")
        for r in legacy_candidates[:5]:
            f.write(f"- Q{r['question_id']}: {r['question'][:60]}...\n")
            f.write(f"  - Intent: {r['intent']}\n")
            if r.get('top_docs'):
                f.write(f"  - Top source: {r['top_docs'][0]['source']}\n")
            f.write("\n")

print(f"\n✅ Results: {RESULTS_FILE}")
print(f"✅ Report: {REPORT_FILE}")

print(f"\n{'='*80}")
print("VALIDATION SUMMARY")
print(f"{'='*80}")
print(f"Total: {len(results)}")
print(f"Intents: {intent_counts}")
print(f"Citations shown: {citations_shown_count}/{len(results)} ({citations_shown_count/len(results)*100:.1f}%)")

