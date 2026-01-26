#!/usr/bin/env python3
"""
STRYDA Intent Router V2 - Self-Check Validation
Tests classifier accuracy against training_questions_v2
"""

import sys
sys.path.insert(0, '/app/backend-minimal')

import psycopg2
import json
from intent_classifier_v2 import classify_intent
from datetime import datetime

DATABASE_URL = "postgresql://postgres.qxqisgjhbjwvoxsjibes:8skmVOJbMyaQHyQl@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

print("="*80)
print("INTENT ROUTER V2 - SELF-CHECK VALIDATION")
print("="*80)
print(f"Start time: {datetime.now().isoformat()}\n")

# Load test sample (100 random entries from each intent)
conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cur = conn.cursor()

print("1. Loading test sample (100 per intent, 500 total)")
test_entries = []

for intent in ['compliance_strict', 'implicit_compliance', 'general_help', 'product_info', 'council_process']:
    cur.execute("""
        SELECT id, intent, trade, question
        FROM training_questions_v2
        WHERE intent = %s
        ORDER BY RANDOM()
        LIMIT 100;
    """, (intent,))
    
    for row in cur.fetchall():
        test_entries.append({
            "id": row[0],
            "expected_intent": row[1],
            "expected_trade": row[2],
            "question": row[3]
        })

print(f"   ✅ Loaded {len(test_entries)} test entries\n")

# Classify each
print("2. Running classifications...")
results = []
correct_intent = 0
correct_trade = 0

for i, entry in enumerate(test_entries):
    if i % 50 == 0:
        print(f"   Progress: {i}/{len(test_entries)}")
    
    predicted = classify_intent(entry["question"])
    
    is_intent_correct = predicted["intent"] == entry["expected_intent"]
    is_trade_correct = predicted["trade"] == entry["expected_trade"]
    
    if is_intent_correct:
        correct_intent += 1
    if is_trade_correct:
        correct_trade += 1
    
    results.append({
        "id": entry["id"],
        "question": entry["question"][:80],
        "expected_intent": entry["expected_intent"],
        "predicted_intent": predicted["intent"],
        "expected_trade": entry["expected_trade"],
        "predicted_trade": predicted["trade"],
        "confidence": predicted["confidence"],
        "method": predicted["method"],
        "intent_correct": is_intent_correct,
        "trade_correct": is_trade_correct
    })

cur.close()
conn.close()

# Calculate metrics
intent_accuracy = (correct_intent / len(test_entries)) * 100
trade_accuracy = (correct_trade / len(test_entries)) * 100

print(f"\n{'='*80}")
print("VALIDATION RESULTS")
print(f"{'='*80}\n")

print(f"Intent Accuracy: {correct_intent}/{len(test_entries)} ({intent_accuracy:.1f}%)")
print(f"Trade Accuracy: {correct_trade}/{len(test_entries)} ({trade_accuracy:.1f}%)")
print(f"Status: {'✅ PASS' if intent_accuracy >= 90 else '⚠️ BELOW TARGET'} (Target: ≥90%)")

# Breakdown by intent
print(f"\n{'='*80}")
print("ACCURACY BY INTENT")
print(f"{'='*80}\n")

for intent in ['compliance_strict', 'implicit_compliance', 'general_help', 'product_info', 'council_process']:
    intent_results = [r for r in results if r["expected_intent"] == intent]
    correct = sum(1 for r in intent_results if r["intent_correct"])
    accuracy = (correct / len(intent_results)) * 100 if intent_results else 0
    
    print(f"{intent:25}: {correct}/{len(intent_results):3} ({accuracy:5.1f}%)")

# Show common misclassifications
print(f"\n{'='*80}")
print("COMMON MISCLASSIFICATIONS (First 10)")
print(f"{'='*80}\n")

misclassified = [r for r in results if not r["intent_correct"]][:10]
for r in misclassified:
    print(f"ID: {r['id']}")
    print(f"   Q: {r['question']}...")
    print(f"   Expected: {r['expected_intent']} | Predicted: {r['predicted_intent']}")
    print()

# Save full report
report_path = "/app/backend-minimal/training/logs/INTENT_V2_VALIDATION_REPORT.json"
with open(report_path, 'w') as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tested": len(test_entries),
            "intent_accuracy": intent_accuracy,
            "trade_accuracy": trade_accuracy,
            "correct_intent": correct_intent,
            "correct_trade": correct_trade
        },
        "results": results[:100]  # Save first 100 for review
    }, f, indent=2)

print(f"✅ Full report saved to {report_path}")

print(f"\n{'='*80}")
print(f"VALIDATION {'✅ COMPLETE' if intent_accuracy >= 90 else '⚠️ NEEDS IMPROVEMENT'}")
print(f"{'='*80}")
