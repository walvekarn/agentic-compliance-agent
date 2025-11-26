# Architecture v2 - Agentic Compliance Assistant

**Version:** 2.0  
**Last Updated:** November 2025  
**Status:** Production Ready

---

## Overview

The Agentic Compliance Assistant follows a **unified schema architecture** with a single LLM gateway, comprehensive audit logging, and strict separation of concerns. All components follow Architecture v2 principles.

## Core Principles

1. **Unified Schemas** - Single source of truth for all data structures
2. **Single LLM Gateway** - All OpenAI calls through `backend/utils/llm_client.py`
3. **Complete Audit Trail** - Every decision logged to database
4. **No Demo Data** - Production-ready, real data only
5. **Error Handling** - Standardized, no swallowed exceptions
6. **Schema Compliance** - Frontend and backend use identical schemas

---

## System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        STREAMLIT[Streamlit Dashboard]
        PAGES[Pages: Home, Analyze Task, Audit Trail, Agentic Analysis, Test Suite]
        COMPONENTS[Components: Forms, Charts, Auth, API Client]
    end
    
    subgraph "API Gateway Layer"
        FASTAPI[FastAPI Backend :8000]
        
        subgraph "API Routes"
            DECISION[/api/v1/decision/*]
            ENTITY[/api/v1/entity/*]
            AUDIT[/api/v1/audit/*]
            FEEDBACK[/api/v1/feedback/*]
            AGENTIC[/api/v1/agentic/*]
        end
        
        AUTH[JWT Authentication]
        RATE[Rate Limiting]
        ERROR[Error Handlers]
    end
    
    subgraph "Business Logic Layer"
        DECISION_ENGINE[Decision Engine<br/>6-Factor Risk Model]
        LLM_GATEWAY[LLM Gateway<br/>backend/utils/llm_client.py]
        AUDIT_SVC[Audit Service<br/>Logging]
        ENTITY_ANALYZER[Entity Analyzer]
        JURISDICTION_ANALYZER[Jurisdiction Analyzer]
    end
    
    subgraph "Data Layer"
        SCHEMAS[Unified Schemas<br/>shared/schemas/]
        CONVERTERS[Schema Converters<br/>backend/utils/]
        DB[(Database<br/>SQLite/PostgreSQL)]
    end
    
    subgraph "External Services"
        OPENAI[OpenAI API<br/>gpt-4o-mini]
    end
    
    STREAMLIT --> FASTAPI
    FASTAPI --> AUTH
    FASTAPI --> DECISION
    FASTAPI --> ENTITY
    FASTAPI --> AUDIT
    FASTAPI --> FEEDBACK
    FASTAPI --> AGENTIC
    
    DECISION --> DECISION_ENGINE
    DECISION_ENGINE --> LLM_GATEWAY
    LLM_GATEWAY --> OPENAI
    
    DECISION_ENGINE --> AUDIT_SVC
    AUDIT_SVC --> DB
    
    DECISION --> CONVERTERS
    CONVERTERS --> SCHEMAS
    AUDIT --> CONVERTERS
    
    style LLM_GATEWAY fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style SCHEMAS fill:#2196F3,stroke:#1565C0,stroke-width:3px
    style DB fill:#9C27B0,stroke:#6A1B9A,stroke-width:3px
```

---

## Folder Structure

```
agentic-compliance-agent/
├── backend/
│   ├── agent/              # Core decision logic
│   │   ├── decision_engine.py      # Main decision engine
│   │   ├── entity_analyzer.py      # Entity risk analysis
│   │   ├── jurisdiction_analyzer.py # Jurisdiction analysis
│   │   ├── risk_models.py           # Risk models & enums
│   │   ├── audit_service.py         # Audit logging
│   │   └── proactive_suggestions.py # Proactive recommendations
│   │
│   ├── api/                 # API routes
│   │   ├── decision_routes.py       # /api/v1/decision/*
│   │   ├── audit_routes.py          # /api/v1/audit/*
│   │   ├── entity_analysis_routes.py # /api/v1/entity/*
│   │   ├── feedback_routes.py       # /api/v1/feedback/*
│   │   ├── agentic_routes.py        # /api/v1/agentic/*
│   │   ├── error_handlers.py        # Error handling
│   │   └── error_utils.py           # Error utilities
│   │
│   ├── db/                  # Database
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── base.py                  # Database base
│   │   └── init_db.py               # Database initialization
│   │
│   ├── utils/               # Utilities
│   │   ├── llm_client.py            # SINGLE LLM gateway
│   │   ├── schema_converter.py      # Convert to unified schemas
│   │   └── audit_converter.py       # Convert audit entries
│   │
│   ├── agentic_engine/      # Experimental agentic features
│   │   ├── orchestrator.py
│   │   ├── reasoning/
│   │   ├── tools/
│   │   └── testing/
│   │
│   ├── auth/                # Authentication
│   ├── config/              # Configuration
│   └── main.py              # FastAPI app entry point
│
├── frontend/
│   ├── pages/               # Streamlit pages
│   │   ├── Home.py
│   │   ├── 1_Analyze_Task.py
│   │   ├── 2_Compliance_Calendar.py
│   │   ├── 3_Audit_Trail.py
│   │   ├── 4_Agent_Insights.py
│   │   └── 7_Agentic_Test_Suite.py
│   │
│   └── components/          # Reusable components
│       ├── analyze_task/    # Task analysis components
│       ├── auth_utils.py
│       ├── api_client.py
│       └── constants.py
│
├── shared/
│   └── schemas/             # UNIFIED SCHEMAS
│       ├── analysis_result.py      # Analysis response schema
│       ├── audit_entry.py          # Audit entry schema
│       ├── jurisdictions.json      # Jurisdiction definitions
│       ├── task_categories.json    # Task category definitions
│       └── schema_loader.py        # Schema loading utilities
│
└── test_scenarios/          # Curated test scenarios
    ├── gdpr_article_30.json
    ├── multi_jurisdiction.json
    └── ...
```

---

## API Endpoints

### Decision Routes (`/api/v1/decision/*`)

**POST `/analyze`**
- Analyzes a compliance task
- Returns: `AnalysisResult` (unified schema)
- Saves to audit DB

**POST `/quick-check`**
- Fast risk assessment
- Returns: `AnalysisResult` (simple view)
- Saves to audit DB

**POST `/batch-analyze`**
- Analyzes multiple tasks
- Returns: List of `AnalysisResult`
- Saves all to audit DB

**POST `/what-if`**
- Scenario analysis
- Returns: Comparison results
- Saves to audit DB

**GET `/risk-levels`**
- Returns risk level definitions

### Audit Routes (`/api/v1/audit/*`)

**GET `/entries`**
- Retrieves audit entries with filters
- Returns: List of `AuditEntry` (unified schema)

**GET `/entries/{audit_id}`**
- Gets specific audit entry
- Returns: `AuditEntry` (unified schema)

**GET `/statistics`**
- Returns audit statistics

**GET `/export/json`**
- Exports audit trail as JSON

### Entity Routes (`/api/v1/entity/*`)

**POST `/entity/analyze`**
- Analyzes entity and generates calendar
- Returns: Compliance calendar

### Feedback Routes (`/api/v1/feedback/*`)

**POST `/feedback`**
- Submits decision feedback
- Returns: Feedback confirmation

**GET `/feedback`**
- Retrieves feedback entries

**GET `/feedback/stats`**
- Returns feedback statistics

### Agentic Routes (`/api/v1/agentic/*`)

**POST `/analyze`**
- Agentic AI analysis
- Returns: Agentic analysis results

**POST `/testSuite`**
- Runs curated test scenarios
- Returns: Test results with pass rate

**POST `/benchmarks`**
- Runs benchmark suite
- Returns: Benchmark results

**POST `/recovery`**
- Error recovery simulation
- Returns: Recovery results

**GET `/health/full`**
- Comprehensive health check
- Returns: Health check results

---

## Data Flow

### Decision Analysis Flow

```
1. User submits form (Frontend)
   ↓
2. API request to /api/v1/decision/analyze
   ↓
3. Request validation (Pydantic)
   ↓
4. Decision Engine analyzes:
   - Jurisdiction risk (15%)
   - Entity risk (15%)
   - Task risk (20%)
   - Data sensitivity (20%)
   - Regulatory risk (20%)
   - Impact risk (10%)
   ↓
5. Decision algorithm computes:
   - Overall risk score
   - Risk level (LOW/MEDIUM/HIGH)
   - Decision (AUTONOMOUS/REVIEW_REQUIRED/ESCALATE)
   - Confidence (0-1)
   ↓
6. Schema converter transforms to AnalysisResult
   ↓
7. Audit Service logs to database
   ↓
8. Response returned to frontend
   ↓
9. Frontend displays using unified schema
```

### LLM Call Flow

```
1. Any component needs LLM
   ↓
2. Calls backend/utils/llm_client.py
   ↓
3. LLM Gateway:
   - Validates API key
   - Applies JSON schema (if compliance task)
   - Sets timeout (45s)
   - Sets max_tokens (2048)
   - Retries (2 attempts)
   ↓
4. OpenAI API call (client.chat.completions.create)
   ↓
5. Response parsing:
   - Extract raw text
   - Parse JSON
   - Extract confidence
   ↓
6. Return LLMResponse:
   - parsed_json
   - raw_text
   - confidence
   - status
```

---

## User Isolation

### Authentication

- JWT-based authentication
- User sessions managed via Streamlit session state
- All API routes protected with `Depends(get_current_user)`

### Data Isolation

- Audit entries include user context
- Feedback linked to users
- Entity history scoped per user (future: multi-tenant)

---

## Error Handling

### Standardized Error Format

```python
{
    "error": {
        "type": "ErrorType",
        "message": "User-friendly message",
        "details": {...}
    }
}
```

### Error Types

- `ValidationError` - Request validation failed
- `AnalysisError` - Decision analysis failed
- `DatabaseError` - Database operation failed
- `LLMError` - LLM call failed
- `AuthenticationError` - Auth failed

### Error Recovery

- Automatic retries for LLM calls (2 attempts)
- Graceful degradation when LLM unavailable
- Database rollback on errors
- User-friendly error messages

---

## Database Schema

See `DB_DESIGN.md` for complete schema documentation.

### Key Tables

- `audit_trail` - All decisions logged
- `entity_history` - Entity compliance history
- `feedback_log` - Human feedback
- `compliance_queries` - Query history
- `users` - User accounts

---

## LLM Gateway

See `LLM_GATEWAY.md` for complete documentation.

### Key Features

- Single entry point: `backend/utils/llm_client.py`
- JSON schema enforcement
- Automatic retries (2 attempts)
- 45-second timeout
- 2048 max output tokens
- Confidence extraction

### Usage

```python
from backend.utils.llm_client import run_compliance_analysis

response = run_compliance_analysis(prompt, use_json_schema=True)
if response.status == "completed":
    analysis = response.parsed_json
    confidence = response.confidence
```

---

## Testing

### Test Suite

- Curated scenarios in `/test_scenarios/*.json`
- Each scenario has expected decision, risk level, confidence
- Compares actual vs expected
- Calculates pass rate, accuracy metrics

See `TEST_SUITE_DESIGN.md` for details.

---

## Deployment

### Development

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend
streamlit run frontend/Home.py --server.port 8501
```

### Production

- Use PostgreSQL instead of SQLite
- Enable JWT authentication
- Set up rate limiting
- Configure CORS properly
- Use environment variables for secrets

---

*Last Updated: November 2025*  
*Architecture Version: 2.0*

