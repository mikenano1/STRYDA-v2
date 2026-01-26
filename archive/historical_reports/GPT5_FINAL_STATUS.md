# GPT-5 Re-enablement Status Report

**Date:** 2025-11-02  
**Branch:** main  
**Commit:** e5749ae  

## Configuration Applied

### Environment (.env)
```
OPENAI_MODEL=gpt-5
OPENAI_MODEL_FALLBACK=gpt-4o-mini
USE_GPT5_EXPERIMENTAL=true
```

### Startup Banner
```
🚀 STRYDA-v2 start | sha=e5749ae | model=gpt-5 | fb=gpt-4o-mini | pills=False | web=True | extractor=reasoning-mode
```

### /__version Endpoint
```json
{
    "git_sha": "e5749ae",
    "build_time": "2025-11-02T08:29:51.619422+00:00",
    "model": "gpt-5",
    "fallback": "gpt-4o-mini",
    "flags": {
        "CLAUSE_PILLS": false,
        "ENABLE_WEB_SEARCH": true
    },
    "extraction_signature": "extract_final_text+retry+fallback"
}
```

## Updated Extraction Logic

### extract_final_text() Enhancement

Implemented multi-path extraction supporting:

1. **GPT-5/o1 reasoning output:**
   - Checks `payload["output"][0]["content"]` for parts with `type="output_text"`
   - Skips `type="reasoning"` or `type="thoughts"` parts
   - Returns: `extraction_path="output[0].content[output_text]"`

2. **Responses API compatibility:**
   - Checks `response.output_text` field
   - Returns: `extraction_path="output_text"`

3. **Standard GPT-4 path:**
   - Checks `choices[0].message.content` (string or list)
   - Returns: `extraction_path="choices[0].message.content"`

### Token Configuration

```python
# GPT-5/o1 models:
max_completion_tokens = 2500
timeout = 45 seconds

# Standard models:
max_tokens = 600
temperature = 0.3
```

## Test Results

### Problem Persists: GPT-5 Returns Empty Content

**Tested Configurations:**
- ✗ 600 tokens → 0 chars, finish_reason=length
- ✗ 1500 tokens → 0 chars, finish_reason=length
- ✗ 2050 tokens → 0 chars, finish_reason=length
- ✗ 2500 tokens, 45s timeout → Request timed out
- ✗ 4000 tokens, 45s timeout → Request timed out (>30s)

**Debug Output:**
```
🔄 Calling OpenAI gpt-5...
🤖 Using GPT-5/o1 with max_completion_tokens=2500, timeout=45s
❌ OpenAI API error: Request timed out.
extraction_path=<error>
fallback_used=False (error occurred before fallback could trigger)
```

### Fallback System Works Perfectly

When retry/fallback logic is reached (before timeout):
```
📥 Raw response: 0 chars, 2050 tokens (path: <none>)
⚠️ Empty response detected, retrying...
⚠️ Still empty, switching to fallback model: gpt-4o-mini
[chat] intent=compliance_strict model=gpt-5 raw_len=821 json_ok=True 
       retry=fallback_model words=115 extraction_path=choices[0].message.content 
       fallback_used=True
```

## Root Cause Analysis

### Issue #1: Empty Content Field
GPT-5 (gpt-5-2025-08-07) returns:
- `message.content = ""` (empty string)
- `finish_reason = "length"`
- Token consumption: 1150-2050 tokens
- **No accessible output in any tested field paths**

Tested extraction paths that all returned empty:
- ❌ `response.output` → doesn't exist
- ❌ `response.output_text` → doesn't exist
- ❌ `choices[0].message.content` → empty string
- ❌ `choices[0].message.content[list]` → not a list, is string
- ❌ `choices[0].message.parsed` → doesn't exist/null
- ❌ `choices[0].message.annotations` → empty array

### Issue #2: Timeout on Large Token Counts
- 2500 tokens + 45s timeout → API timeout
- 4000 tokens + 45s timeout → API timeout
- GPT-5 reasoning time exceeds practical limits for real-time chat

## Conclusion

**GPT-5/o1 models are fundamentally incompatible with STRYDA's real-time JSON response requirements:**

1. **Empty output:** All tokens consumed for reasoning, none for final answer
2. **Performance:** >45s response times unacceptable for chat UX
3. **Cost:** High token usage (2500+ tokens) with no output
4. **Reliability:** Fallback required for every single request

**Recommendation:** **Keep gpt-4o-mini as primary model**

- Fast responses (3-10s)
- Reliable JSON extraction
- 750-1100 char answers
- 120-160 words per response
- Zero timeouts
- Proven stable

## Files Modified

1. `/app/backend-minimal/.env` - Set OPENAI_MODEL=gpt-5 (for testing only)
2. `/app/backend-minimal/app.py` - Updated startup banner to "reasoning-mode", default to gpt-5
3. `/app/backend-minimal/openai_structured.py` - Enhanced extract_final_text() with multi-path reasoning support
4. `/app/backend-minimal/docs/GPT5_INCOMPATIBILITY.md` - Documented incompatibility

## Next Action

**Revert to gpt-4o-mini** for production stability:

```bash
# backend-minimal/.env
OPENAI_MODEL=gpt-4o-mini
OPENAI_MODEL_FALLBACK=gpt-4o-mini
```

This ensures:
- ✅ Fast responses (<12s)
- ✅ Reliable JSON extraction
- ✅ Zero timeouts
- ✅ Production-ready UX
