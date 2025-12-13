#!/usr/bin/env python3
"""
Integration Test for Task 2D-4-3: Follow-Up Handling via /api/chat endpoint

This test verifies the full flow through the API:
1. Turn 1: Bootstrap conversation with intent classification
2. Turn 2: Follow-up returns placeholder response (bypasses old flow)
3. Verify intent_reclassified=false in logs
"""

import requests
import time
import os

# Backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

def test_api_follow_up_handling():
    """Test follow-up handling through /api/chat endpoint"""
    
    print("\n" + "="*80)
    print("🧪 INTEGRATION TEST: Task 2D-4-3 - Follow-Up via /api/chat")
    print("="*80 + "\n")
    
    # Test session ID
    test_session_id = f"test_api_2d_4_3_{int(time.time())}"
    
    # ===================================================================
    # TURN 1: Initial question (bootstrap)
    # ===================================================================
    print("📝 TURN 1: Initial question")
    print("-" * 80)
    
    turn1_payload = {
        "message": "What's the minimum bearing for a beam?",
        "session_id": test_session_id,
        "conversation_history": []
    }
    
    print(f"Request: POST {BACKEND_URL}/api/chat")
    print(f"Session: {test_session_id[:12]}...")
    print(f"Message: {turn1_payload['message']}")
    
    response1 = requests.post(
        f"{BACKEND_URL}/api/chat",
        json=turn1_payload,
        timeout=30
    )
    
    print(f"\nResponse status: {response1.status_code}")
    
    if response1.status_code != 200:
        print(f"❌ Turn 1 failed: {response1.text}")
        return False
    
    data1 = response1.json()
    print(f"✅ Turn 1 response received:")
    print(f"   Intent: {data1.get('intent')}")
    print(f"   Model: {data1.get('model')}")
    print(f"   Answer preview: {data1.get('answer', '')[:100]}...")
    print(f"   Notes: {data1.get('notes', [])}")
    
    # ===================================================================
    # TURN 2: Follow-up question (should use placeholder)
    # ===================================================================
    print("\n📝 TURN 2: Follow-up question")
    print("-" * 80)
    
    # Wait a moment to ensure conversation is stored
    time.sleep(0.5)
    
    turn2_payload = {
        "message": "What if it's a 90x45 beam?",
        "session_id": test_session_id,
        "conversation_history": [
            {"role": "user", "content": turn1_payload["message"]},
            {"role": "assistant", "content": data1.get("answer", "")}
        ]
    }
    
    print(f"Request: POST {BACKEND_URL}/api/chat")
    print(f"Session: {test_session_id[:12]}... (same session)")
    print(f"Message: {turn2_payload['message']}")
    
    response2 = requests.post(
        f"{BACKEND_URL}/api/chat",
        json=turn2_payload,
        timeout=30
    )
    
    print(f"\nResponse status: {response2.status_code}")
    
    if response2.status_code != 200:
        print(f"❌ Turn 2 failed: {response2.text}")
        return False
    
    data2 = response2.json()
    print(f"✅ Turn 2 response received:")
    print(f"   Intent: {data2.get('intent')} (should be same as Turn 1)")
    print(f"   Model: {data2.get('model')} (should be 'simple_session_placeholder')")
    print(f"   Answer: {data2.get('answer', '')}")
    print(f"   Notes: {data2.get('notes', [])}")
    
    # ===================================================================
    # Verify expectations
    # ===================================================================
    print("\n📊 VERIFICATION")
    print("-" * 80)
    
    checks_passed = []
    checks_failed = []
    
    # Check 1: Turn 2 should use placeholder model
    if data2.get('model') == 'simple_session_placeholder':
        checks_passed.append("✓ Turn 2 uses placeholder model")
    else:
        checks_failed.append(f"✗ Turn 2 model should be 'simple_session_placeholder', got '{data2.get('model')}'")
    
    # Check 2: Turn 2 should have follow_up_placeholder note
    if 'follow_up_placeholder' in data2.get('notes', []):
        checks_passed.append("✓ Turn 2 has 'follow_up_placeholder' note")
    else:
        checks_failed.append(f"✗ Turn 2 should have 'follow_up_placeholder' note, got {data2.get('notes', [])}")
    
    # Check 3: Turn 2 should have task_2d_4_3 note
    if 'task_2d_4_3' in data2.get('notes', []):
        checks_passed.append("✓ Turn 2 has 'task_2d_4_3' note")
    else:
        checks_failed.append(f"✗ Turn 2 should have 'task_2d_4_3' note")
    
    # Check 4: Intent should be locked (same as Turn 1)
    if data2.get('intent') == data1.get('intent'):
        checks_passed.append(f"✓ Intent locked: {data2.get('intent')}")
    else:
        checks_failed.append(f"✗ Intent should be locked to '{data1.get('intent')}', got '{data2.get('intent')}'")
    
    # Check 5: Answer should mention original question
    if "What's the minimum bearing for a beam?" in data2.get('answer', ''):
        checks_passed.append("✓ Answer references original question")
    else:
        checks_failed.append("✗ Answer should reference original question")
    
    # Check 6: No citations for placeholder
    if len(data2.get('citations', [])) == 0:
        checks_passed.append("✓ No citations for placeholder response")
    else:
        checks_failed.append(f"✗ Placeholder should have no citations, got {len(data2.get('citations', []))}")
    
    # Print results
    print("\nPassed checks:")
    for check in checks_passed:
        print(f"  {check}")
    
    if checks_failed:
        print("\nFailed checks:")
        for check in checks_failed:
            print(f"  {check}")
    
    # ===================================================================
    # Summary
    # ===================================================================
    print("\n" + "="*80)
    if len(checks_failed) == 0:
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("="*80)
        print("\nVerified:")
        print("  ✓ Turn 1: Bootstrap conversation")
        print("  ✓ Turn 2: Follow-up with placeholder response")
        print("  ✓ Intent locked across turns")
        print("  ✓ Old flow bypassed for follow-ups")
        print("  ✓ Proper notes and model tracking")
        print("\n⚠️  NOTE: Check backend logs for:")
        print("     [conversation_followup] ... intent_reclassified=false")
        return True
    else:
        print(f"❌ {len(checks_failed)} CHECKS FAILED")
        print("="*80)
        return False

if __name__ == "__main__":
    import sys
    
    # Check if SIMPLE_SESSION_MODE is enabled
    print("\n⚙️  Checking environment...")
    print(f"   BACKEND_URL: {BACKEND_URL}")
    
    # Try to get health check
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health.status_code == 200:
            print(f"   Backend: ✓ Online")
        else:
            print(f"   Backend: ✗ Unhealthy (status {health.status_code})")
            sys.exit(1)
    except Exception as e:
        print(f"   Backend: ✗ Unreachable ({e})")
        sys.exit(1)
    
    print("\n⚠️  IMPORTANT: This test requires SIMPLE_SESSION_MODE=true")
    print("   Set in .env or environment before running")
    
    success = test_api_follow_up_handling()
    sys.exit(0 if success else 1)
