# Agentic Engine Tools Implementation

Complete implementation of four production-ready tools for the agentic compliance system.

## Overview

The tools module provides specialized capabilities for the agentic orchestrator to interact with production systems, external APIs, and perform compliance-specific calculations.

```
src/agentic_engine/tools/
├── __init__.py          # Tool exports
├── entity_tool.py       # Entity analysis & audit log queries
├── task_tool.py         # Task risk analysis
├── calendar_tool.py     # Deadline & urgency calculations
└── http_tool.py         # Safe HTTP wrapper
```

## 1. EntityTool

**Purpose:** Fetch entity details from production engine and similar tasks from audit log.

### Features

- ✅ Connects to `EntityAnalyzer` from production engine
- ✅ Fetches entity capability assessments
- ✅ Queries `ComplianceQuery` audit log for similar tasks
- ✅ Lazy-loads dependencies to avoid circular imports
- ✅ Graceful fallback when components unavailable

### Methods

#### `fetch_entity_details(entity_name, entity_type, industry, **kwargs)`

Fetch entity details from production engine.

**Parameters:**
- `entity_name` (str): Name of the entity
- `entity_type` (str): Type (PUBLIC_COMPANY, PRIVATE_COMPANY, etc.)
- `industry` (str): Industry category
- `**kwargs`: Additional attributes (employee_count, annual_revenue, etc.)

**Returns:**
```python
{
    "name": "Acme Corp",
    "type": "PRIVATE_COMPANY",
    "industry": "TECHNOLOGY",
    "capability": "Moderate - Standard compliance capability",
    "confidence": 0.7,
    "details": {
        "employee_count": 150,
        "annual_revenue": 5000000,
        "has_personal_data": True,
        "is_regulated": False,
        "previous_violations": 0
    }
}
```

#### `fetch_similar_tasks(query, entity_name=None, limit=5)`

Fetch similar tasks from audit log.

**Parameters:**
- `query` (str): Search query or task description
- `entity_name` (Optional[str]): Filter by entity name
- `limit` (int): Maximum results (default: 5)

**Returns:**
```python
[
    {
        "id": 123,
        "query": "Assess GDPR compliance for data processing...",
        "response_preview": "Based on analysis of your data...",
        "model": "gpt-4o-mini",
        "status": "success",
        "created_at": "2024-11-15T10:30:00",
        "metadata": {...}
    }
]
```

### Usage Example

```python
from backend.agentic_engine.tools import EntityTool
from backend.db.base import get_db

# With database session
db = next(get_db())
tool = EntityTool(db_session=db)

# Fetch entity details
entity_info = tool.fetch_entity_details(
    entity_name="Healthcare Inc",
    entity_type="HEALTHCARE",
    industry="HEALTHCARE",
    employee_count=500,
    has_personal_data=True
)

# Find similar past tasks
similar = tool.fetch_similar_tasks(
    query="HIPAA compliance",
    entity_name="Healthcare Inc"
)
```

---

## 2. TaskTool

**Purpose:** Run task risk analyzer from production decision engine.

### Features

- ✅ Connects to `DecisionEngine` from production engine
- ✅ Calculates risk scores using production risk models
- ✅ Classifies tasks into risk levels (LOW/MEDIUM/HIGH)
- ✅ Provides actionable recommendations
- ✅ Auto-classifies task categories from descriptions

### Methods

#### `run_task_risk_analyzer(task_description, task_category, affects_personal_data, **kwargs)`

Run task risk analyzer from production engine.

**Parameters:**
- `task_description` (str): Description of the compliance task
- `task_category` (str): Category (GENERAL_INQUIRY, REGULATORY_FILING, etc.)
- `affects_personal_data` (bool): Whether task affects personal data
- `**kwargs`: Additional context (deadline, requires_filing, etc.)

**Returns:**
```python
{
    "task_description": "File annual compliance report with SEC",
    "category": "REGULATORY_FILING",
    "risk_score": 0.85,
    "risk_level": "HIGH",
    "recommendation": "Escalate to expert - high-risk task",
    "reasoning": [
        "Task category: REGULATORY_FILING - High base risk",
        "Requires regulatory filing - high compliance scrutiny"
    ],
    "analysis": {
        "affects_personal_data": False,
        "requires_filing": True,
        "has_deadline": True,
        "base_category_risk": 0.9
    }
}
```

#### `classify_task_category(task_description)`

Classify task into appropriate category based on keywords.

**Parameters:**
- `task_description` (str): Task description

**Returns:** str - Predicted category

**Categories:**
- `DATA_PRIVACY` - GDPR, privacy, PII keywords
- `REGULATORY_FILING` - File, filing, submit keywords
- `CONTRACT_REVIEW` - Contract, agreement keywords
- `SECURITY_AUDIT` - Security, breach keywords
- `FINANCIAL_REPORTING` - Financial, audit, SOX keywords
- `RISK_ASSESSMENT` - Risk, assess keywords
- `POLICY_REVIEW` - Policy, procedure keywords
- `GENERAL_INQUIRY` - Default

### Usage Example

```python
from backend.agentic_engine.tools import TaskTool

tool = TaskTool()

# Analyze task risk
result = tool.run_task_risk_analyzer(
    task_description="Submit quarterly financial report to SEC",
    task_category="REGULATORY_FILING",
    affects_personal_data=False,
    requires_filing=True,
    deadline="2024-12-31"
)

print(f"Risk Level: {result['risk_level']}")
print(f"Recommendation: {result['recommendation']}")

# Auto-classify task
category = tool.classify_task_category("Review GDPR privacy policy")
# Returns: "DATA_PRIVACY"
```

---

## 3. CalendarTool

**Purpose:** Calculate deadlines, urgency scores, and compliance timing.

### Features

- ✅ Flexible deadline calculation (days ahead, text parsing, direct dates)
- ✅ Natural language parsing ("30 days", "2 weeks", "1 month")
- ✅ Urgency scoring based on time remaining and task category
- ✅ Actionable recommendations based on urgency level
- ✅ Support for past due detection

### Methods

#### `calculate_deadline(base_date=None, days_ahead=None, deadline_text=None)`

Calculate deadline from various input formats.

**Parameters:**
- `base_date` (Optional[str]): Base date in ISO format
- `days_ahead` (Optional[int]): Days ahead from base_date
- `deadline_text` (Optional[str]): Natural language deadline

**Returns:**
```python
{
    "deadline": "2024-12-15T10:30:00",
    "deadline_date": "2024-12-15",
    "days_remaining": 30,
    "calculation_method": "Parsed '30 days' as 30 days",
    "is_past_due": False,
    "urgency": 0.55
}
```

#### `calculate_urgency_score(deadline, task_category="GENERAL_INQUIRY")`

Calculate urgency score based on deadline and task category.

**Parameters:**
- `deadline` (str): Deadline in ISO format or natural language
- `task_category` (str): Task category for risk weighting

**Returns:**
```python
{
    "urgency_score": 0.91,
    "urgency_level": "CRITICAL",
    "days_remaining": 3,
    "deadline": "2024-11-18T10:30:00",
    "task_category": "REGULATORY_FILING",
    "is_overdue": False,
    "recommendations": [
        "Immediate action required",
        "Escalate to compliance team",
        "Review all requirements today",
        "Prepare emergency response if overdue"
    ]
}
```

### Urgency Calculation

**Base Urgency (by days remaining):**
- < 0 days: 1.0 (Overdue - Critical)
- ≤ 3 days: 0.95 (Critical)
- ≤ 7 days: 0.85 (High)
- ≤ 14 days: 0.70 (High)
- ≤ 30 days: 0.55 (Medium)
- ≤ 60 days: 0.35 (Medium-Low)
- > 60 days: 0.20 (Low)

**Category Multipliers:**
- `REGULATORY_FILING`: 1.3x
- `INCIDENT_RESPONSE`: 1.4x
- `FINANCIAL_REPORTING`: 1.2x
- `DATA_PRIVACY`: 1.1x
- `GENERAL_INQUIRY`: 0.8x

**Urgency Levels:**
- `CRITICAL`: ≥ 0.8
- `HIGH`: ≥ 0.6
- `MEDIUM`: ≥ 0.4
- `LOW`: < 0.4

### Usage Example

```python
from backend.agentic_engine.tools import CalendarTool

tool = CalendarTool()

# Calculate deadline from text
deadline_info = tool.calculate_deadline(deadline_text="30 days")
print(f"Deadline: {deadline_info['deadline_date']}")
print(f"Urgency: {deadline_info['urgency']}")

# Calculate urgency with category weighting
urgency_info = tool.calculate_urgency_score(
    deadline="7 days",
    task_category="REGULATORY_FILING"
)
print(f"Urgency Level: {urgency_info['urgency_level']}")
for rec in urgency_info['recommendations']:
    print(f"  • {rec}")
```

---

## 4. HTTPTool

**Purpose:** Safe GET/POST wrapper with timeouts, retries, and error handling.

### Features

- ✅ Configurable timeouts and retries
- ✅ Automatic exponential backoff
- ✅ Safe JSON/text response parsing
- ✅ SSL verification control
- ✅ Both async and sync methods
- ✅ Comprehensive error handling
- ✅ Request/response metadata

### Methods

#### `async get(url, params=None, headers=None, **kwargs)`

Make async HTTP GET request.

**Parameters:**
- `url` (str): Target URL
- `params` (Optional[Dict]): Query parameters
- `headers` (Optional[Dict]): HTTP headers
- `**kwargs`: Additional httpx parameters

**Returns:**
```python
{
    "success": True,
    "status_code": 200,
    "data": {...},  # Parsed JSON or text
    "headers": {...},
    "url": "https://api.example.com/data",
    "method": "GET",
    "attempts": 1
}
```

#### `async post(url, data=None, json=None, headers=None, **kwargs)`

Make async HTTP POST request.

**Parameters:**
- `url` (str): Target URL
- `data` (Optional[Dict]): Form data
- `json` (Optional[Dict]): JSON data
- `headers` (Optional[Dict]): HTTP headers
- `**kwargs`: Additional httpx parameters

**Returns:** Same as `get()`

#### `get_sync(url, params=None, headers=None, **kwargs)`

Synchronous version of GET request.

#### `post_sync(url, data=None, json=None, headers=None, **kwargs)`

Synchronous version of POST request.

### Error Handling

**Automatic Retries:**
- Timeout exceptions → Retry with exponential backoff
- HTTP errors → Retry with exponential backoff
- Max retries: Configurable (default: 3)

**Backoff Strategy:**
- Attempt 1: Immediate
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds

**Error Response:**
```python
{
    "success": False,
    "status_code": None,
    "data": None,
    "error": "Request timeout after 30.0s: ...",
    "url": "https://api.example.com/data",
    "method": "GET",
    "attempts": 3
}
```

### Usage Example

```python
from backend.agentic_engine.tools import HTTPTool

# Initialize with custom settings
tool = HTTPTool(
    timeout=30.0,      # 30 second timeout
    max_retries=3,     # 3 retry attempts
    verify_ssl=True    # Verify SSL certificates
)

# Synchronous GET
result = tool.get_sync(
    "https://api.example.com/compliance/data",
    params={"entity": "Acme Corp"},
    headers={"Authorization": "Bearer token"}
)

if result["success"]:
    print(f"Status: {result['status_code']}")
    print(f"Data: {result['data']}")
else:
    print(f"Error: {result['error']}")

# Synchronous POST
result = tool.post_sync(
    "https://api.example.com/compliance/submit",
    json={
        "task": "GDPR compliance check",
        "entity": "Acme Corp"
    }
)

# Async usage
import asyncio

async def fetch_data():
    result = await tool.get(
        "https://api.example.com/data"
    )
    return result

data = asyncio.run(fetch_data())

# Clean up
asyncio.run(tool.close())
```

---

## Integration with Orchestrator

The tools are designed to be imported lazily inside the orchestrator to avoid circular dependencies and minimize import overhead.

### Recommended Pattern

```python
# src/agentic_engine/orchestrator.py

class AgenticAIOrchestrator:
    def __init__(self):
        # ... existing initialization ...
        self._tools = None
    
    def _get_tools(self, db_session=None):
        """Lazy load tools when needed."""
        if self._tools is None:
            from backend.agentic_engine.tools import (
                EntityTool,
                TaskTool,
                CalendarTool,
                HTTPTool
            )
            
            self._tools = {
                'entity': EntityTool(db_session),
                'task': TaskTool(),
                'calendar': CalendarTool(),
                'http': HTTPTool()
            }
        
        return self._tools
    
    def run(self, task, context, max_iterations=10):
        """Main orchestration with tool access."""
        tools = self._get_tools(context.get('db_session'))
        
        # Use tools in execution
        entity_info = tools['entity'].fetch_entity_details(
            entity_name=context.get('entity_name', 'Unknown'),
            entity_type=context.get('entity_type', 'PRIVATE_COMPANY')
        )
        
        task_risk = tools['task'].run_task_risk_analyzer(
            task_description=task,
            task_category=context.get('task_category', 'GENERAL_INQUIRY')
        )
        
        if context.get('deadline'):
            urgency = tools['calendar'].calculate_urgency_score(
                deadline=context['deadline'],
                task_category=context.get('task_category', 'GENERAL_INQUIRY')
            )
        
        # ... continue with plan-execute-reflect cycle ...
```

### Benefits of Lazy Loading

1. **No Circular Imports:** Tools import production modules only when instantiated
2. **Faster Startup:** Import overhead only when tools are actually used
3. **Optional Dependencies:** Orchestrator works even if some production modules unavailable
4. **Flexibility:** Can mock tools for testing without affecting orchestrator

---

## Testing

### Unit Tests

Each tool includes comprehensive error handling and fallbacks:

```python
# Test EntityTool without database
tool = EntityTool()  # No db_session
result = tool.fetch_entity_details("Acme Corp", "PRIVATE_COMPANY")
assert "capability" in result  # Still works with fallback

# Test TaskTool with invalid category
tool = TaskTool()
result = tool.run_task_risk_analyzer(
    "Some task",
    task_category="INVALID_CATEGORY"  # Falls back to GENERAL_INQUIRY
)
assert result["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

# Test CalendarTool with unparseable text
tool = CalendarTool()
result = tool.calculate_deadline(deadline_text="unknown format")
# Defaults to 30 days ahead
assert result["days_remaining"] is not None

# Test HTTPTool timeout
tool = HTTPTool(timeout=0.001, max_retries=1)
result = tool.get_sync("https://slow-endpoint.com")
assert result["success"] == False
assert "timeout" in result["error"].lower()
```

### Integration Tests

Run `test_tools_implementation.py` to verify all tools:

```bash
python3 test_tools_implementation.py
```

---

## Requirements

### Dependencies

All dependencies are already in `requirements.txt`:

```
sqlalchemy>=2.0.0     # For EntityTool database queries
httpx==0.25.2         # For HTTPTool
python-dateutil       # For CalendarTool date parsing (optional)
```

### Production Module Access

Tools connect to these production modules:

- `src.agent.entity_analyzer.EntityAnalyzer`
- `src.agent.decision_engine.DecisionEngine`
- `src.agent.risk_models` (EntityContext, TaskContext, etc.)
- `backend.db.models.ComplianceQuery`

All connections use lazy loading and include fallbacks if modules are unavailable.

---

## Summary

| Tool | Primary Function | Production Integration | Key Methods |
|------|-----------------|----------------------|-------------|
| **EntityTool** | Entity analysis & history | EntityAnalyzer, ComplianceQuery | fetch_entity_details, fetch_similar_tasks |
| **TaskTool** | Risk analysis | DecisionEngine | run_task_risk_analyzer, classify_task_category |
| **CalendarTool** | Deadline & urgency | Standalone | calculate_deadline, calculate_urgency_score |
| **HTTPTool** | External APIs | Standalone (httpx) | get, post, get_sync, post_sync |

**Lines of Code:** ~800 lines across 4 production-ready tools

**Status:** ✅ Fully implemented, tested, and production-ready

**Next Steps:**
1. Import tools lazily in orchestrator when needed
2. Use tools in step execution for enhanced context
3. Log tool usage in agent loop metrics
4. Extend tools with additional methods as needed

---

**Implementation Date:** November 15, 2024  
**Implementation Status:** COMPLETE ✅

