# LLM Gateway - Unified LLM Client

**Version:** 2.0  
**Last Updated:** November 2025

---

## Overview

**SINGLE unified gateway** for all OpenAI calls. Located at `backend/utils/llm_client.py`. No endpoint or page may directly call OpenAI.

---

## Architecture

```
All LLM Calls
    ↓
backend/utils/llm_client.py
    ↓
OpenAI API (client.chat.completions.create)
    ↓
Response (parsed JSON, raw text, confidence)
```

---

## Configuration

### Compliance Tasks

- **Model:** `gpt-4o-mini`
- **Timeout:** 45 seconds
- **Max Output Tokens:** 2048
- **Temperature:** 0.7
- **Retries:** 2 attempts with exponential backoff
- **JSON Schema:** Enforced for compliance tasks

---

## Primary Method: `run_compliance_analysis()`

### Signature

```python
def run_compliance_analysis(
    prompt: str,
    use_json_schema: bool = True
) -> LLMResponse
```

### Returns

```python
class LLMResponse:
    parsed_json: Optional[Dict[str, Any]]  # Structured JSON data
    raw_text: Optional[str]                # Raw response text
    confidence: Optional[float]             # Extracted confidence (0-1)
    status: str                            # "completed", "error", "timeout"
    error: Optional[str]                    # Error message if failed
    timestamp: str                         # ISO timestamp
```

### Usage

```python
from backend.utils.llm_client import run_compliance_analysis

response = run_compliance_analysis(
    prompt="Analyze this compliance scenario...",
    use_json_schema=True
)

if response.status == "completed":
    analysis = response.parsed_json
    confidence = response.confidence
    raw_text = response.raw_text
else:
    error = response.error
```

---

## JSON Schema Enforcement

### Response Schema

When `use_json_schema=True`, responses are validated against:

```json
{
    "type": "object",
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["AUTONOMOUS", "REVIEW_REQUIRED", "ESCALATE"]
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "risk_level": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH"]
        },
        "risk_analysis": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "factor": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 1},
                    "weight": {"type": "number", "minimum": 0, "maximum": 1},
                    "explanation": {"type": "string"}
                }
            }
        },
        "why": {
            "type": "object",
            "properties": {
                "reasoning_steps": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    },
    "required": ["decision", "confidence", "risk_level", "risk_analysis", "why"]
}
```

### Request Format

```python
request_params = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "You are a compliance analysis assistant..."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7,
    "max_tokens": 2048,
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "compliance_analysis_response",
            "strict": True,
            "schema": response_schema
        }
    }
}
```

---

## Retry Logic

### Implementation

```python
for attempt in range(MAX_RETRIES + 1):  # 0, 1, 2
    try:
        response = client.chat.completions.create(**request_params)
        return LLMResponse(...)
    except Exception as e:
        if attempt == MAX_RETRIES:
            return LLMResponse(status="error", error=str(e))
        wait_time = 2 ** attempt  # Exponential backoff
        time.sleep(wait_time)
```

### Retry Behavior

- **Attempt 1:** Immediate
- **Attempt 2:** Wait 1 second
- **Attempt 3:** Wait 2 seconds
- **Final:** Return error if all fail

---

## Error Handling

### Error Types

**Timeout:**
```python
response.status == "timeout"
response.error == "Request timed out after 45 seconds"
```

**API Error:**
```python
response.status == "error"
response.error == "LLM request failed after 3 attempts: ..."
```

**Validation Error:**
```python
response.status == "error"
response.error == "Response is not valid JSON despite schema requirement"
```

### Handling

```python
response = run_compliance_analysis(prompt)

if response.status == "completed":
    # Success
    use_result(response.parsed_json)
elif response.status == "timeout":
    # Retry with longer timeout or simpler prompt
    handle_timeout()
elif response.status == "error":
    # Log error and show user-friendly message
    logger.error(response.error)
    show_error_to_user()
```

---

## Confidence Extraction

### Automatic Extraction

The gateway automatically extracts confidence from parsed JSON:

```python
# If parsed_json contains "confidence" field
confidence = parsed_json.get("confidence")
if confidence is not None:
    # Normalize to 0-1 range
    confidence = max(0.0, min(1.0, float(confidence)))
    response.confidence = confidence
```

### Usage

```python
response = run_compliance_analysis(prompt)

# Confidence is automatically extracted
if response.confidence is not None:
    print(f"Confidence: {response.confidence:.2f}")
else:
    print("Confidence not available")
```

---

## Async Support

### Async Method

```python
async def run_compliance_analysis_async(
    prompt: str,
    use_json_schema: bool = True
) -> LLMResponse
```

### Usage

```python
from backend.utils.llm_client import run_compliance_analysis_async

response = await run_compliance_analysis_async(prompt, use_json_schema=True)
```

---

## Migration from Direct Calls

### Before

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke(prompt)
```

### After

```python
from backend.utils.llm_client import run_compliance_analysis

response = run_compliance_analysis(prompt, use_json_schema=True)
if response.status == "completed":
    result = response.parsed_json
```

---

## Legacy Methods (Backward Compatibility)

### `call_llm_sync()` and `call_llm_async()`

These methods still work but are deprecated:

```python
# Legacy (still works)
from backend.utils.llm_client import call_llm_sync

response = call_llm_sync(prompt)
# Returns: {"status": "completed", "result": {...}, ...}

# Preferred (new)
from backend.utils.llm_client import run_compliance_analysis

response = run_compliance_analysis(prompt)
# Returns: LLMResponse with parsed_json, raw_text, confidence
```

---

## Implementation Details

### OpenAI Client

```python
from openai import OpenAI

client = OpenAI(
    api_key=api_key,
    timeout=45.0  # Set at client level
)
```

### Request Execution

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    temperature=0.7,
    max_tokens=2048,
    response_format={...}  # JSON schema if enabled
)
```

### Response Parsing

```python
# Extract content
raw_text = response.choices[0].message.content

# Parse JSON
parsed_json = json.loads(raw_text)

# Extract confidence
confidence = parsed_json.get("confidence")
```

---

## Testing

### Mock Mode

When API key is not configured:
```python
response = run_compliance_analysis(prompt)
# Returns: LLMResponse with status="error", error="LLM client not available"
```

### Test Scenarios

1. **Valid response** - JSON schema enforced
2. **Invalid JSON** - Error returned
3. **Timeout** - Retry logic tested
4. **API failure** - Retry and error handling

---

## Best Practices

1. **Always use `run_compliance_analysis()`** for compliance tasks
2. **Set `use_json_schema=True`** for structured responses
3. **Check `response.status`** before using data
4. **Handle `None` confidence** gracefully
5. **Log errors** for debugging
6. **Never call OpenAI directly** - always use gateway

---

*Last Updated: November 2025*  
*LLM Gateway Version: 2.0*

