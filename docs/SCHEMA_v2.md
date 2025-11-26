# Schema v2 - Unified Data Schemas

**Version:** 2.0  
**Last Updated:** November 2025

---

## Overview

All data structures follow **unified schemas** located in `/shared/schemas/`. Frontend and backend must use these schemas exclusively. No duplicate definitions allowed.

---

## Core Schemas

### 1. AnalysisResult (`shared/schemas/analysis_result.py`)

**Purpose:** Standardized response for all compliance analysis requests.

**Structure:**
```python
{
    "decision": "AUTONOMOUS" | "REVIEW_REQUIRED" | "ESCALATE",
    "confidence": float (0-1),  # None if not available, NEVER 0.0 default
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "risk_analysis": [
        {
            "factor": "jurisdiction_risk",
            "score": float (0-1),
            "weight": float (0-1),
            "explanation": "string"
        },
        ...
    ],
    "why": {
        "reasoning_steps": ["step1", "step2", ...]
    },
    # Optional fields
    "recommendations": ["rec1", "rec2", ...],
    "escalation_reason": "string",
    "similar_cases": [...],
    "pattern_analysis": "string",
    "proactive_suggestions": [...],
    "timestamp": "ISO datetime"
}
```

**Methods:**
- `to_simple_dict()` - Simple view (summary only)
- `to_detailed_dict()` - Detailed view (full analysis)

**Usage:**
```python
from shared.schemas.analysis_result import AnalysisResult

# Backend converts DecisionAnalysis to AnalysisResult
result = convert_decision_analysis_to_analysis_result(analysis)

# Frontend parses using AnalysisResult
analysis = AnalysisResult(**response_data)
```

---

### 2. AuditEntry (`shared/schemas/audit_entry.py`)

**Purpose:** Standardized format for all audit trail entries.

**Structure:**
```python
{
    "audit_id": int,
    "timestamp": "ISO datetime",
    "agent_type": "string",
    "task_description": "string",
    "task_category": "string",
    "entity_name": "string",
    "entity_type": "string",
    "decision_outcome": "AUTONOMOUS" | "REVIEW_REQUIRED" | "ESCALATE",
    "confidence_score": float (0-1),
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "risk_score": float (0-1),
    "reasoning_chain": ["step1", "step2", ...],
    "risk_factors": {...},
    "recommendations": ["rec1", ...],
    "escalation_reason": "string",
    "entity_context": {...},
    "task_context": {...},
    "metadata": {...}
}
```

**Usage:**
```python
from shared.schemas.audit_entry import AuditEntry

# Backend converts AuditTrail to AuditEntry
entry = convert_audit_trail_to_audit_entry(audit_trail)

# Frontend parses using AuditEntry
entry = AuditEntry(**entry_data)
```

---

### 3. Jurisdictions (`shared/schemas/jurisdictions.json`)

**Purpose:** Centralized jurisdiction definitions.

**Structure:**
```json
[
    {
        "code": "US_FEDERAL",
        "name": "United States (Federal)",
        "regulations": ["SOX", "HIPAA", "CCPA"],
        "description": "..."
    },
    {
        "code": "EU",
        "name": "European Union",
        "regulations": ["GDPR"],
        "description": "..."
    },
    ...
]
```

**Usage:**
```python
from shared.schemas.schema_loader import load_jurisdictions

jurisdictions = load_jurisdictions()
# Use exact names from schema: "European Union", not "EU countries"
```

---

### 4. Task Categories (`shared/schemas/task_categories.json`)

**Purpose:** Centralized task category definitions.

**Structure:**
```json
[
    {
        "code": "DATA_PRIVACY",
        "name": "Data Privacy",
        "description": "...",
        "complexity": "MEDIUM",
        "typical_risk": "MEDIUM"
    },
    ...
]
```

---

## Schema Conversion

### Backend → Unified Schema

**Decision Analysis:**
```python
from backend.utils.schema_converter import convert_decision_analysis_to_analysis_result

# Convert DecisionAnalysis to AnalysisResult
result = convert_decision_analysis_to_analysis_result(analysis, detailed=True)
```

**Audit Trail:**
```python
from backend.utils.audit_converter import convert_audit_trail_to_audit_entry

# Convert AuditTrail to AuditEntry
entry = convert_audit_trail_to_audit_entry(audit_trail)
```

### Frontend → Unified Schema

**Loading Options:**
```python
from shared.schemas.schema_loader import load_jurisdictions, load_task_categories

jurisdictions = load_jurisdictions()
task_categories = load_task_categories()
```

**Parsing Responses:**
```python
from shared.schemas.analysis_result import AnalysisResult

# Parse API response
analysis = AnalysisResult(**response_data)
decision = analysis.decision
confidence = analysis.confidence  # May be None
risk_analysis = analysis.risk_analysis
reasoning = analysis.why.reasoning_steps
```

---

## Field Requirements

### Required Fields

**AnalysisResult:**
- `decision` - Always present
- `confidence` - Present or None (never defaults to 0.0)
- `risk_level` - Always present
- `risk_analysis` - Always present (may be empty list)
- `why.reasoning_steps` - Always present (may be empty list)

**AuditEntry:**
- `timestamp` - Always present
- `agent_type` - Always present
- `task_description` - Always present
- `decision_outcome` - Always present
- `confidence_score` - Always present (may be None)
- `reasoning_chain` - Always present (may be empty list)

### Optional Fields

Only include if they have values:
- `recommendations` - Only if recommendations exist
- `escalation_reason` - Only if escalation occurred
- `similar_cases` - Only if similar cases found
- `pattern_analysis` - Only if patterns identified
- `proactive_suggestions` - Only if suggestions generated

---

## Schema Validation

### Backend Validation

```python
from shared.schemas.analysis_result import AnalysisResult

# Validate response matches schema
try:
    result = AnalysisResult(**response_data)
except ValidationError as e:
    # Handle validation error
```

### Frontend Validation

```python
# Check required fields exist
required = ["decision", "risk_level", "confidence", "risk_analysis", "why"]
missing = [f for f in required if f not in response_data]
if missing:
    # Handle missing fields
```

---

## Migration Guide

### Removing Duplicate Definitions

**Before:**
```python
# Frontend
LOCATION_OPTIONS = ["United States", "European Union countries", ...]

# Backend
JURISDICTIONS = ["US_FEDERAL", "EU", ...]
```

**After:**
```python
# Both use unified schema
from shared.schemas.schema_loader import load_jurisdictions
jurisdictions = load_jurisdictions()
LOCATION_OPTIONS = [j["name"] for j in jurisdictions]
```

---

## Confidence Handling

### Rules

1. **Never default to 0.0** - Use `None` when confidence is not available
2. **Normalize range** - Always 0-1 (not 0-100)
3. **Extract from response** - Use `response.confidence` from LLMResponse
4. **Display gracefully** - Show "N/A" when confidence is None

### Examples

**Backend:**
```python
# Correct
confidence = analysis.confidence if analysis.confidence is not None else None

# Wrong
confidence = analysis.confidence or 0.0  # NEVER do this
```

**Frontend:**
```python
# Correct
if confidence is not None and confidence > 0:
    st.metric("Confidence", f"{confidence*100:.0f}%")
else:
    st.metric("Confidence", "N/A")

# Wrong
st.metric("Confidence", f"{confidence*100:.0f}%")  # May show 0% incorrectly
```

---

## Risk Analysis Structure

### Unified Format

```python
risk_analysis = [
    {
        "factor": "jurisdiction_risk",
        "score": 0.7,
        "weight": 0.15,
        "explanation": "Jurisdiction complexity risk: 0.70"
    },
    {
        "factor": "entity_risk",
        "score": 0.5,
        "weight": 0.15,
        "explanation": "Entity risk profile: 0.50"
    },
    # ... 4 more factors
]
```

### Conversion

**From RiskFactors (backend):**
```python
risk_factors = RiskFactors(
    jurisdiction_risk=0.7,
    entity_risk=0.5,
    ...
)

# Converted to risk_analysis list in schema_converter.py
```

**To RiskFactors (for display):**
```python
# Frontend can convert back if needed
risk_factors = {}
for item in risk_analysis:
    risk_factors[item["factor"]] = item["score"]
```

---

## Reasoning Chain Structure

### Unified Format

```python
why = {
    "reasoning_steps": [
        "Step 1: Analyzed jurisdiction requirements",
        "Step 2: Assessed entity risk profile",
        "Step 3: Evaluated task complexity",
        ...
    ]
}
```

### Legacy Support

Frontend supports both formats:
```python
# Unified schema (preferred)
reasoning = analysis.why.reasoning_steps

# Legacy format (fallback)
reasoning = analysis.get("reasoning_chain", [])
```

---

## Schema Files

### Location

All schemas in `/shared/schemas/`:

- `analysis_result.py` - AnalysisResult Pydantic model
- `audit_entry.py` - AuditEntry Pydantic model
- `jurisdictions.json` - Jurisdiction definitions
- `task_categories.json` - Task category definitions
- `schema_loader.py` - Loading utilities

### Import Paths

**Backend:**
```python
from shared.schemas.analysis_result import AnalysisResult
from shared.schemas.audit_entry import AuditEntry
```

**Frontend:**
```python
# Add shared to path first
import sys
from pathlib import Path
shared_dir = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from schemas.schema_loader import load_jurisdictions
```

---

*Last Updated: November 2025*  
*Schema Version: 2.0*

