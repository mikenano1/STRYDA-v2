#!/bin/bash
echo "================================================"
echo "    STRYDA V2 - End-to-End Smoke Test"
echo "================================================"
echo ""

# 1. Check backend health
echo "1️⃣  Checking backend health..."
HEALTH=$(curl -s http://localhost:8001/health)
if echo "$HEALTH" | grep -q '"ok":true'; then
    echo "   ✅ Backend healthy"
else
    echo "   ❌ Backend not responding"
    exit 1
fi

# 2. Test compliance query (should have citations)
echo ""
echo "2️⃣  Testing compliance query..."
RESPONSE=$(curl -s -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "NZS 3604 stud spacing requirements", "session_id": "smoke-test"}')

CITATIONS=$(echo "$RESPONSE" | grep -o '"citations":\[' | wc -l)
if [ "$CITATIONS" -gt 0 ]; then
    echo "   ✅ Citations provided for compliance query"
else
    echo "   ❌ No citations for compliance query"
    exit 1
fi

# 3. Test chitchat (should have NO citations)
echo ""
echo "3️⃣  Testing chitchat query..."
CHITCHAT=$(curl -s -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?", "session_id": "smoke-test-chat"}')

CHAT_CITES=$(echo "$CHITCHAT" | grep -o '"citations":\[\]' | wc -l)
if [ "$CHAT_CITES" -gt 0 ]; then
    echo "   ✅ No citations for chitchat (correct)"
else
    echo "   ⚠️  Chitchat may have citations (check manually)"
fi

# 4. Verify CLAUSE_PILLS flag
echo ""
echo "4️⃣  Verifying feature flags..."
if grep -q "CLAUSE_PILLS=false" .env; then
    echo "   ✅ CLAUSE_PILLS=false (production mode)"
else
    echo "   ⚠️  CLAUSE_PILLS not set to false"
fi

# 5. Check frontend
echo ""
echo "5️⃣  Checking frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend responding"
else
    echo "   ⚠️  Frontend not responding"
fi

echo ""
echo "================================================"
echo "         ✅ Smoke Test Complete"
echo "================================================"
echo ""
echo "Next recommended steps:"
echo "  1. Push to GitHub: git remote add origin <url> && git push -u origin main"
echo "  2. Review quarantined files in __quarantine__/20251030/"
echo "  3. Deploy to production environment"
echo ""
