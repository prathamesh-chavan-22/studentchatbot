# FYJC Support Bot - Test Report with gpt-oss-20b

## Test Date
April 7, 2026

## Model Configuration
- **LLM Model**: `openai/gpt-oss-20b`
- **Embedding Model**: `intfloat/multilingual-e5-base`
- **Retrieval**: FAISS with k=5

---

## Test Results Summary

| Test # | Query Type | Query | Used Groq | Response Quality | Status |
|--------|------------|-------|-----------|------------------|--------|
| 1 | Marathi - App lock | माझा अर्ज भरण्याची प्रक्रिया पूर्ण... | ❌ False | Fallback only | ⚠️ |
| 2 | English - Part 2 access | After locking Part 1... | ❌ False | Fallback only | ⚠️ |
| 3 | English - Payment | I have made a payment... | ✅ True | Generated answer | ✅ |
| 4 | Out-of-scope | Who is the PM of India? | ✅ True | Proper refusal | ✅ |
| 5 | Greeting | Hello | ❌ False | Fallback only | ⚠️ |

---

## Detailed Analysis

### ✅ Working Cases

#### Test 3: Payment Query
- **Query**: "I have made a payment, but it is not reflecting on the website"
- **Used Groq**: Yes
- **Tokens**: 778
- **Cost**: $0.000043
- **Response**: Generated a relevant Marathi response about payment
- **Status**: ✅ PASS

#### Test 4: Out-of-Scope Query (Guardrail Test)
- **Query**: "Who is the Prime Minister of India?"
- **Used Groq**: Yes
- **Tokens**: 2045
- **Cost**: $0.000105
- **Response**: Correctly refused with support contact info
- **Status**: ✅ PASS - Guardrails working correctly

### ⚠️ Issues Identified

#### Issue 1: Inconsistent Groq Usage
- **Problem**: Groq is only being used for ~40% of queries (2 out of 5 tests)
- **Affected Queries**:
  - Marathi application lock query
  - English Part 2 access query
  - Greeting query
- **Root Cause**: Likely the Groq API is hitting rate limits or the model is sometimes failing to respond

#### Issue 2: Fallback Response Quality
- **Problem**: When Groq is not used, the bot returns a simple bilingual fallback message listing related FAQs
- **Impact**: Less helpful than a proper LLM-generated response
- **Example**: 
  ```
  **मराठी**
  आपल्या प्रश्नासाठी संबंधित FAQ खालीलप्रमाणे आहेत:
  - Q: प्र.४७)...
  - A: होय...
  ```

#### Issue 3: Retrieval Quality
- **Problem**: For some queries, the retrieved sources don't seem highly relevant
- **Example**: For "After locking Part 1...", it retrieved unrelated Marathi FAQs about mobile number and mother's name
- **Impact**: Even when Groq generates answers, they may be based on irrelevant context

---

## Performance Metrics

### Response Times
- Average response time: ~0.2-0.8 seconds for fallback
- Groq responses: ~2-5 seconds (when successful)

### Cost Analysis
- Average cost per Groq query: ~$0.00004-$0.0001
- Very cost-effective for production use
- TPM limit utilization: Well within 250K limit

---

## Recommendations

1. **Fix Groq Reliability**: Investigate why Groq is not being used consistently. Check:
   - API rate limits
   - Error handling in bot.py
   - Model availability/stability

2. **Improve Retrieval**: 
   - Consider increasing k from 5 to 10
   - Add reranking for better context selection
   - Filter out very long website content chunks

3. **Enhance Fallback**: 
   - Make fallback answers more contextual
   - Add direct answer extraction from top retrieved FAQ

4. **Add Logging**: 
   - Log Groq API errors to understand failure patterns
   - Track success rate over time

---

## Next Steps

- [ ] Investigate Groq API error logs
- [ ] Test with higher k value (10-15)
- [ ] Add retry logic for failed Groq calls
- [ ] Implement response quality validation
- [ ] Test with more Marathi queries

---

## Conclusion

The bot is **partially working** with `openai/gpt-oss-20b`. Key findings:
- ✅ Guardrails working correctly (refuses out-of-scope queries)
- ✅ Cost-effective when Groq is used
- ⚠️ Inconsistent Groq usage (~40% success rate in tests)
- ⚠️ Retrieval quality needs improvement
- ⚠️ Fallback mechanism needs enhancement

**Overall Status**: Functional but needs optimization for production readiness.
