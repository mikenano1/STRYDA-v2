# STRYDA-v2 Load & Concurrency Validation Report

**Date:** 2025-11-10 16:57:51 UTC  
**Test Type:** Concurrent load (5-10 users)  
**Total Queries:** 20

## Test Summary

- **Total Requests:** 20
- **Successful:** 20/20 (100.0%)
- **Failed:** 0
- **Average Latency:** 15973ms
- **P95 Latency:** 19679ms

## Cycle Results

### Cycle 1: 5 Concurrent Requests
- Avg Latency: 17854ms
- Success Rate: 100.0%
- Min/Max: 15354ms / 19679ms

### Cycle 2: 10 Concurrent Requests
- Avg Latency: 15733ms
- Success Rate: 100.0%
- Min/Max: 11973ms / 17847ms

### Cycle 3: 5 Concurrent Requests
- Avg Latency: 14573ms
- Success Rate: 100.0%
- Min/Max: 12469ms / 15807ms

## Performance Metrics

**Latency Distribution:**
- Min: 11973ms
- Max: 19679ms
- Median: 16519ms
- Mean: 15973ms
- P95: 19679ms
- P99: 19679ms

**Connection Pool:**
- Status: Active
- Min Connections: 2
- Max Connections: 10
- Pool Type: SimpleConnectionPool

**Caching Efficiency:**
- Embedding Cache Hit Rate: 5000.0%
- Embedding Cache Hits: 10
- Embedding Cache Misses: 10
- Response Cache Hit Rate: 0.0%

## Accuracy Validation

- Intent Classification: 1 different intents detected
- Citations Provided: 16/20 queries (80.0%)
- Avg Citations per Query: 2.1
- Avg Word Count: 151 words

## Issues Detected

No issues detected - all requests completed successfully.

## Production Readiness Verdict

✅ [Stability] All requests complete successfully
❌ [Performance] Avg latency <7s (actual: 16.0s)
❌ [Performance] P95 latency <10s (actual: 19.7s)
❌ [Caching] Cached queries <3s (actual: 14.6s)
✅ [Caching] Cache improvement: 18.4%
✅ [Caching] Cache hit rate ≥40% (actual: 50.0%)

⚠️ **CONDITIONAL** - Some criteria not met, review required
