# GPT-5 / o1 Model Limitation (STRYDA-v2)

**Summary:** GPT-5 (gpt-5-2025-08-07) is an o1-style reasoning model that uses all tokens for internal reasoning and returns an empty content field.

## Observed Behavior

- `finish_reason: "length"`
- `message.content: ""` (empty string)
- Uses up to 4000 tokens with no user-visible output
- Token consumption occurs but `raw_len = 0 chars`

## Technical Details

### Response Structure
```python
{
  "model": "gpt-5-2025-08-07",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "",  # EMPTY - all tokens used for reasoning
      "refusal": None,
      "annotations": []
    },
    "finish_reason": "length"
  }],
  "usage": {
    "total_tokens": 1150,  # Tokens consumed
    "completion_tokens": 600  # But no output!
  }
}
```

### Test Results
| max_completion_tokens | Output Chars | finish_reason | Result |
|-----------------------|--------------|---------------|---------|
| 600 | 0 | length | ❌ Empty |
| 1500 | 0 | length | ❌ Empty |
| 2050 | 0 | length | ❌ Empty |
| 4000 | 0 | timeout | ❌ Timeout (>30s) |

## Impact

1. **JSON Response Workflows Incompatible**
   - Cannot use for structured JSON outputs
   - All reasoning tokens consumed, no content returned

2. **Performance Issues**
   - 0-char responses require fallback
   - Timeout risks with large token limits
   - Slower response times (>30s with 4000 tokens)

3. **User Experience**
   - Delays while model reasons without output
   - Requires fallback mechanism for reliability

## Workaround

### Primary Solution
Use `gpt-4o` or `gpt-4o-mini` for all JSON-structured calls:

```python
# .env
OPENAI_MODEL=gpt-4o-mini
OPENAI_MODEL_FALLBACK=gpt-4o-mini
```

### Fallback Logic
System automatically falls back to `gpt-4o-mini` when GPT-5 returns empty content:
1. Detect `raw_len == 0`
2. Retry with stricter instructions
3. If still empty, switch to fallback model
4. Log with `fallback_used=True`

## Testing Reference

**Test Query:** "minimum apron flashing cover per E2/AS1"

**GPT-5 Result:**
```
📥 Raw response: 0 chars, 1150 tokens (path: <none>)
DEBUG GPT5 choices[0].finish_reason: length
DEBUG GPT5 message.content: EMPTY STRING
```

**gpt-4o-mini Result:**
```
📥 Raw response: 851 chars, 188 tokens
✅ JSON parsed directly
📊 Final answer: 749 chars, 122 words, json_ok=True
```

## Status

**Documented and Mitigated** ✅

STRYDA-v2 now defaults to `gpt-4o-mini` for reliable, fast JSON responses. GPT-5/o1 models are not compatible with this use case.

## References

- **Date Identified:** 2025-11-02
- **Model Tested:** gpt-5-2025-08-07
- **Issue:** O1-style reasoning models exhaust all tokens on internal reasoning
- **Resolution:** Use gpt-4o-mini as primary model

---

**Note:** GPT-5/o1 are designed for complex reasoning tasks where thinking steps are more important than immediate output. For real-time JSON APIs, use standard GPT-4o models.
