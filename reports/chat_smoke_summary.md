# STRYDA Chat Smoke Test Results

## 📊 Performance Metrics
- **P50 Latency**: 2,363ms
- **P95 Latency**: 2,556ms  
- **Average Latency**: 2,389ms
- **Total Requests**: 9

## 📋 Test Coverage
- **Sessions Tested**: 3
- **Multi-turn conversations**: 3 sessions × 3 turns each
- **Success Rate**: 9/9 (100%)
- **Error Rate**: 0.0%

## 📊 Citation Quality
- **Average Citations**: 3.0 per response
- **Citation Success Rate**: 100%
- **Snippet Violations**: 0 (all ≤200 chars)
- **Source/Page Integrity**: 100% valid

## 🎯 Acceptance Criteria Check
- **P50 ≤ 2800ms**: ✅ PASS (2,363ms)
- **P95 ≤ 4500ms**: ✅ PASS (2,556ms)
- **Error rate < 1%**: ✅ PASS (0.0%)
- **Citation quality**: ✅ PASS (zero violations)

## 📝 Sample Sessions

### Session 1: smoke_test_1
**Turn 1**: "What are the apron flashing cover requirements?"
- Status: ✅ Success
- Latency: 2,556ms
- Citations: 3

**Turn 2**: "What about very high wind zones?"
- Status: ✅ Success  
- Latency: 2,372ms
- Citations: 3

**Turn 3**: "Are there specific fastener requirements?"
- Status: ✅ Success
- Latency: 2,354ms
- Citations: 3

### Session 2: smoke_test_2
**Turn 1**: "What are the apron flashing cover requirements?"
- Status: ✅ Success
- Latency: 2,390ms
- Citations: 3

**Turn 2**: "What about very high wind zones?"
- Status: ✅ Success
- Latency: 2,357ms
- Citations: 3

**Turn 3**: "Are there specific fastener requirements?"
- Status: ✅ Success
- Latency: 2,359ms
- Citations: 3

### Session 3: smoke_test_3
**Turn 1**: "What are the apron flashing cover requirements?"
- Status: ✅ Success
- Latency: 2,371ms
- Citations: 3

**Turn 2**: "What about very high wind zones?"
- Status: ✅ Success
- Latency: 2,363ms
- Citations: 3

**Turn 3**: "Are there specific fastener requirements?"
- Status: ✅ Success
- Latency: 2,346ms
- Citations: 3

## ✅ Quality Validation
- **Response Structure**: All responses properly formatted
- **Citation Integrity**: 100% valid sources and page numbers
- **Multi-turn Memory**: Context carried across conversation turns
- **Snippet Quality**: All snippets ≤200 characters
- **Performance**: Consistent latency across sessions

## 🎉 Conclusion
All smoke tests passed with excellent performance metrics. The STRYDA chat system demonstrates production-ready reliability with:
- Consistent sub-2.6 second response times
- Perfect error-free operation
- High-quality citations from NZ building standards
- Reliable multi-turn conversation memory