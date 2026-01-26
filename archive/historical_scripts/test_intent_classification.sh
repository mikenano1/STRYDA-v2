#!/bin/bash

echo "Testing Intent Classification for Failing Queries"
echo "=================================================="

queries=(
  "H1 insulation R-values for Auckland climate zone"
  "NZS 3604 stud spacing requirements"
  "F4 means of escape for 2-storey building"
  "G5.3.2 hearth clearance requirements"
  "E2/AS1 minimum apron flashing cover"
)

for query in "${queries[@]}"; do
  echo ""
  echo "Query: $query"
  echo "---"
  response=$(curl -s -X POST "http://localhost:8001/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"$query\", \"session_id\": \"test_intent_$(date +%s)\"}")
  
  intent=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin).get('intent', 'unknown'))")
  citations=$(echo "$response" | python -c "import sys, json; print(len(json.load(sys.stdin).get('citations', [])))")
  tier1_hit=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin).get('tier1_hit', False))")
  
  echo "Intent: $intent"
  echo "Citations: $citations"
  echo "Tier1 Hit: $tier1_hit"
done
