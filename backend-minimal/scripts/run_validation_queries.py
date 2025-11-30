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

print(f"\n✅ Loaded {len(questions)} validation questions")

# Run validation
results = []
intent_counts = {}
citations_shown_count = 0

for q in questions:
    print(f"\n[{q['id']}/50] Testing: {q['question'][:60]}...")
    
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
            
            result = {
                "question_id": q['id'],
                "trade_hint": q['trade_hint'],
                "question": q['question'],
                "intent": intent,
                "citations_shown": citations_shown,
                "citation_count": len(citations),
                "citation_sources": [c.get('source') for c in citations[:3]]
            }
            
            results.append(result)
            print(f"   Intent: {intent} | Citations: {len(citations)}")
        else:
            print(f"   ❌ HTTP {response.status_code}")
            results.append({
                "question_id": q['id'],
                "error": f"HTTP {response.status_code}"
            })
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results.append({
            "question_id": q['id'],
            "error": str(e)
        })

# Save JSON results
with open(RESULTS_FILE, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Results saved to {RESULTS_FILE}")

# Generate markdown report
with open(REPORT_FILE, 'w') as f:
    f.write("# STRYDA-v2 Backend Validation Report\n\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Questions:** 50\n\n")
    
    f.write("## Summary\n\n")
    f.write(f"- Total questions: {len(results)}\n")
    f.write(f"- Citations shown: {citations_shown_count}/{len(results)} ({citations_shown_count/len(results)*100:.1f}%)\n")
    f.write(f"- Citations hidden: {len(results) - citations_shown_count}/{len(results)}\n\n")
    
    f.write("## Intent Distribution\n\n")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        f.write(f"- {intent}: {count}\n")
    
    f.write("\n## Citations by Intent\n\n")
    for intent in intent_counts.keys():
        intent_results = [r for r in results if r.get('intent') == intent]
        with_citations = sum(1 for r in intent_results if r.get('citations_shown', False))
        f.write(f"- {intent}: {with_citations}/{len(intent_results)} showed citations\n")
    
    f.write("\n## Sample Results\n\n")
    for r in results[:10]:
        f.write(f"**Q{r['question_id']}:** {r['question']}\n")
        f.write(f"- Intent: {r.get('intent', 'N/A')}\n")
        f.write(f"- Citations: {r.get('citation_count', 0)}\n")
        if r.get('citation_sources'):
            f.write(f"- Sources: {', '.join(r['citation_sources'])}\n")
        f.write("\n")

print(f"✅ Report saved to {REPORT_FILE}")

print(f"\n{'='*80}")
print("VALIDATION COMPLETE")
print(f"{'='*80}")
print(f"Total: {len(results)}")
print(f"Intents: {intent_counts}")
print(f"Citations shown: {citations_shown_count}/{len(results)}")
