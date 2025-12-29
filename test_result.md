# Testing Protocol
- All backend testing must use `deep_testing_backend_v2` tool.
- Verify health check endpoint first.
- Test chat endpoint with hybrid questions (general) and strict questions (compliance).
- Test gate logic (threshold questions).
- Capture logs if failures occur.

# Test Results (Current Run)
- Date: 2025-06-15
- Phase: Gemini Migration & Regulation Update

## Backend Tests (Planned)
1. **Health Check**: Verify API is up.
2. **Gate Logic**:
   - Q: "What is the minimum pitch for corrugated iron?" -> Expect Gate Response.
   - A: "Corrugate, RU24, lap direction." -> Expect Resolved Answer.
3. **Regulation Check**:
   - Q: "Can I use schedule method for H1?" -> Expect warning/rejection of schedule method.
4. **Strict Compliance**:
   - Q: "What is the stud spacing for 2.4m wall?" -> Expect citations and strict model usage.
