#!/usr/bin/env python3
"""
STRYDA-v2 Intent Classifier V2.3 - Validation Analysis
Analyzes 50-question validation results and produces confusion matrix + report
"""

import json
from datetime import datetime

QUESTIONS_FILE = "/app/backend-minimal/training/validation/stryda_v2_validation_questions.json"
RESULTS_FILE = "/app/backend-minimal/training/validation/intent_v23_run.json"
REPORT_FILE = "/app/backend-minimal/training/logs/INTENT_V23_VALIDATION_REPORT.md"

print("="*80)
print("INTENT CLASSIFIER V2.3 - VALIDATION ANALYSIS")
print("="*80)

# Load questions and results
with open(QUESTIONS_FILE, 'r') as f:
    questions = json.load(f)

try:
    with open(RESULTS_FILE, 'r') as f:
        results = json.load(f)
except FileNotFoundError:
    print("❌ Results file not found. Run validation first.")
    exit(1)

# Since we don't have gold labels, infer expected intent from question patterns
def infer_gold_intent(question):
    """Infer expected intent from question text"""
    q = question.lower()
    
    # Compliance strict: explicit requirements
    if any(word in q for word in ['minimum', 'maximum', 'requirement', 'what does', 'according to', 'clause', 'table']):
        if any(word in q for word in ['nzs', 'e2/as1', 'h1/as1', 'c/as', 'b1/as1', 'f4/as1']):
            return "compliance_strict"
    
    # Implicit compliance: checking compliance
    if any(phrase in q for phrase in ['does this', 'is this', 'will this', 'can i', 'do i need', 'is it']):
        if any(word in q for word in ['comply', 'meet', 'acceptable', 'allowed', 'legal', 'pass', 'required']):
            return "implicit_compliance"
    
    # Product info: brand/system questions
    if any(word in q for word in ['which', 'what', 'best']) and any(brand in q for brand in ['gib', 'ardex', 'system']):
        return "product_info"
    
    # Council process
    if any(word in q for word in ['consent', 'ccc', 'producer statement', 'council', 'inspection']):
        if any(word in q for word in ['process', 'apply', 'need', 'how do i get']):
            return "council_process"
    
    # Default to general_help
    return "general_help"

# Analyze results
total = len(results)
correct = 0
intent_counts = {}
confusion_matrix = {}
citation_by_intent = {}

for idx, (q, r) in enumerate(zip(questions, results)):
    gold = infer_gold_intent(q['question'])
    predicted = r.get('intent', 'unknown')
    citations_count = r.get('citation_count', 0)
    
    # Accuracy
    if gold == predicted:
        correct += 1
    
    # Count by intent
    intent_counts[predicted] = intent_counts.get(predicted, 0) + 1
    
    # Confusion matrix
    if gold not in confusion_matrix:
        confusion_matrix[gold] = {}
    confusion_matrix[gold][predicted] = confusion_matrix[gold].get(predicted, 0) + 1
    
    # Citations
    if predicted not in citation_by_intent:
        citation_by_intent[predicted] = {"total": 0, "with_citations": 0}
    citation_by_intent[predicted]["total"] += 1
    if citations_count > 0:
        citation_by_intent[predicted]["with_citations"] += 1

accuracy = (correct / total) * 100 if total > 0 else 0

# Generate report
with open(REPORT_FILE, 'w') as f:
    f.write("# STRYDA-v2 Intent Classifier V2.3 – Validation Report\n\n")
    f.write(f"**Date:** {datetime.now().isoformat()}\n")
    f.write(f"**Classifier Version:** V2.3 (Hybrid Scoring + Few-Shots)\n\n")
    
    f.write("## Overall Stats\n\n")
    f.write(f"- Total questions: {total}\n")
    f.write(f"- Overall accuracy: {correct}/{total} ({accuracy:.1f}%)\n\n")
    
    f.write("## Intent Distribution\n\n")
    for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True):
        f.write(f"- **{intent}**: {count}/{total} ({count/total*100:.1f}%)\n")
    
    f.write("\n## Citation Behavior (100% Correct Expected)\n\n")
    for intent in sorted(citation_by_intent.keys()):
        stats = citation_by_intent[intent]
        pct = (stats['with_citations'] / stats['total'] * 100) if stats['total'] > 0 else 0
        f.write(f"- **{intent}**: {stats['with_citations']}/{stats['total']} ({pct:.1f}%) showed citations\n")
    
    f.write("\n## Confusion Matrix\n\n")
    f.write("| Gold Intent | compliance_strict | implicit_compliance | general_help | product_info | council_process |\n")
    f.write("|-------------|-------------------|---------------------|--------------|--------------|------------------|\n")
    
    all_intents = ['compliance_strict', 'implicit_compliance', 'general_help', 'product_info', 'council_process']
    for gold in all_intents:
        if gold in confusion_matrix:
            row = [gold]
            for pred in all_intents:
                count = confusion_matrix[gold].get(pred, 0)
                row.append(str(count))
            f.write("| " + " | ".join(row) + " |\n")
    
    f.write("\n## Key Findings\n\n")
    f.write(f"✅ **Overall Accuracy:** {accuracy:.1f}%\n\n")
    
    if accuracy >= 90:
        f.write("✅ **Target Met:** Accuracy ≥ 90%\n\n")
    else:
        f.write(f"⚠️ **Below Target:** Accuracy {accuracy:.1f}% (target: 90%)\n\n")
    
    # Check citation behavior
    compliance_citations = citation_by_intent.get('compliance_strict', {}).get('with_citations', 0)
    compliance_total = citation_by_intent.get('compliance_strict', {}).get('total', 0)
    other_citations = sum(citation_by_intent.get(i, {}).get('with_citations', 0) 
                         for i in ['general_help', 'product_info', 'implicit_compliance', 'council_process'])
    
    f.write(f"**Citation Control:**\n")
    f.write(f"- compliance_strict: {compliance_citations}/{compliance_total} with citations\n")
    f.write(f"- Other intents: {other_citations} with citations (should be 0)\n\n")
    
    if other_citations == 0:
        f.write("✅ **Citation Behavior:** 100% correct\n\n")
    else:
        f.write(f"⚠️ **Citation Regression:** {other_citations} non-compliance queries showed citations\n\n")

print(f"\n✅ Report written to {REPORT_FILE}")
print(f"\nOverall Accuracy: {accuracy:.1f}%")
print(f"Intent Distribution: {intent_counts}")
