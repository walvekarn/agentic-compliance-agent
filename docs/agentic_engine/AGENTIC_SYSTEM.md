# 🧪 Experimental Agentic AI Engine

**Version:** 0.2.0 (PHASE 2 Complete)  
**Status:** Experimental - Fully Functional - Ready for Testing  
**Last Updated:** November 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Development Phases](#development-phases)
5. [API Documentation](#api-documentation)
6. [Dashboard Integration](#dashboard-integration)
7. [Configuration](#configuration)
8. [Development Guide](#development-guide)
9. [Testing](#testing)
10. [Roadmap](#roadmap)

---

## Overview

### What is the Agentic AI Engine?

The **Agentic AI Engine** is an experimental next-generation reasoning system that implements advanced **plan-execute-reflect** cycles for deep compliance analysis. Unlike traditional rule-based systems, it provides transparent, step-by-step reasoning with tool augmentation and iterative refinement.

### Key Innovation

**This engine doesn't just make a decision—it shows its work** through explicit planning, execution, and self-reflection phases, providing unprecedented transparency in AI reasoning.

### Comparison with Existing System

| Aspect | Existing Decision Engine | Agentic AI Engine |
|--------|-------------------------|-------------------|
| **Approach** | Rule-based risk scoring (6 factors) | Plan-execute-reflect reasoning |
| **Speed** | Fast (<1s) | Slower (10-30s) |
| **Transparency** | Risk factors + final decision | Complete reasoning chain |
| **Adaptability** | Fixed model | Dynamic tool usage |
| **Memory** | Entity history only | Episodic + semantic learning |
| **Tools** | None | HTTP, calendar, entity, task tools |
| **Best For** | Fast, routine decisions | Complex, novel scenarios |
| **Production Ready** | ✅ Yes | ❌ No (experimental) |

### When to Use

**✅ Use Agentic Engine For:**
- Complex, multi-step compliance analyses
- Novel scenarios requiring research
- Tasks needing external data sources
- Situations requiring transparent reasoning
- High-stakes decisions needing complete audit trails
- Learning and improvement over time

**❌ Use Traditional Engine For:**
- Simple yes/no decisions
- Time-critical real-time responses
- Routine, repetitive tasks
- Low-complexity inquiries
- Production environments (currently)

---

## Architecture

### System Overview

```mermaid
graph TB
    USER[User/API Client]
    
    subgraph "API Layer"
        ENDPOINT["/api/v1/agentic/analyze"]
    end
    
    subgraph "Agentic AI Engine"
        ORCH[AgenticAIOrchestrator<br/>Main Coordinator]
        
        subgraph "Agent Loop"
            PLAN[Planning Phase<br/>3-7 Strategic Steps]
            EXEC[Execution Phase<br/>Tool-Augmented Actions]
            REFLECT[Reflection Phase<br/>Quality Assessment]
        end
        
        subgraph "Reasoning System"
            RE[Reasoning Engine<br/>LLM-Powered]
            PROMPTS[Prompts:<br/>Planner | Executor | Reflector]
        end
        
        subgraph "Tools"
            T1[HTTP Tool]
            T2[Calendar Tool]
            T3[Entity Tool]
            T4[Task Tool]
        end
        
        subgraph "Support Systems"
            SCORE[Score Assistant<br/>Quality Metrics]
            MEM[Memory Store<br/>Episodic + Semantic]
        end
    end
    
    USER --> ENDPOINT
    ENDPOINT --> ORCH
    
    ORCH --> PLAN
    PLAN --> EXEC
    EXEC --> REFLECT
    REFLECT -.Iterate.-> PLAN
    
    PLAN --> RE
    EXEC --> RE
    REFLECT --> RE
    RE --> PROMPTS
    
    EXEC --> T1 & T2 & T3 & T4
    REFLECT --> SCORE
    ORCH -.PHASE 3.-> MEM
    
    style ORCH fill:#667eea,stroke:#764ba2,stroke-width:3px
    style PLAN fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style EXEC fill:#FF9800,stroke:#E65100,stroke-width:2px
    style REFLECT fill:#2196F3,stroke:#1565C0,stroke-width:2px
```

### Execution Flow

```
1. USER SUBMITS TASK
   ↓
2. ORCHESTRATOR RECEIVES REQUEST
   ↓
3. PLANNING PHASE
   - Analyze task and entity context
   - Generate 3-7 strategic steps
   - Identify tool requirements
   - Establish success criteria
   ↓
4. EXECUTION LOOP (for each step)
   │
   ├─→ EXECUTE STEP
   │   - Invoke required tools
   │   - Gather data and facts
   │   - Perform analysis
   │   - Document findings
   │   ↓
   ├─→ REFLECT ON STEP
   │   - Assess correctness
   │   - Check completeness
   │   - Identify issues
   │   - Score quality
   │   ↓
   └─→ DECISION POINT
       - Quality acceptable? → Next step
       - Issues found? → Re-execute step
       - Missing info? → Request data
   ↓
5. SYNTHESIS
   - Combine all step results
   - Generate final recommendation
   - Calculate confidence score
   ↓
6. RETURN RESULTS
   - Complete reasoning chain
   - All step outputs
   - Quality reflections
   - Final recommendation
```

---

## Components

### 1. Orchestrator (`orchestrator.py`)

**Purpose:** Master coordinator for the entire agentic workflow.

**Class:** `AgenticAIOrchestrator`

**Key Methods:**
- `plan(task, context)` → Generates strategic execution plan
- `execute_step(step, plan_context)` → Runs individual step with tools
- `reflect(step, execution_result)` → Evaluates execution quality
- `run(task, context, max_iterations)` → Orchestrates complete workflow

**Responsibilities:**
- Coordinate plan-execute-reflect cycles
- Manage iteration limits
- Handle errors and retries
- Aggregate results

**Current Status:** ✅ **Fully Implemented** - Orchestrator.run() functional, returns real analysis results

---

### 2. Agent Loop (`agent_loop.py`)

**Purpose:** Manages the iterative execution loop.

**Class:** `AgentLoop`

**Key Methods:**
- `generate_plan(task, context, planner_fn)` → Creates execution plan
- `run_steps(plan, executor_fn, context)` → Executes plan sequentially
- `evaluate_reflection(step, result, reflector_fn)` → Assesses quality
- `update_memory(step, result, reflection, memory_store)` → Stores learnings
- `execute(task, ...)` → Main entry point for complete cycle

**Configuration:**
- `max_steps`: Maximum execution steps (default: 10)
- `enable_reflection`: Toggle reflection phase (default: True)
- `enable_memory`: Toggle memory updates (default: True)

**Current Status:** ✅ **Fully Implemented** - Orchestrator.run() functional, returns real analysis results

---

### 3. Reasoning Engine (`reasoning/reasoning_engine.py`)

**Purpose:** Provides LLM-powered reasoning capabilities.

**Class:** `ReasoningEngine`

**Prompts:**

#### `planner_prompt.txt`
```
You are an AI planner. Break the user's compliance task into 3–7 steps, 
each representing a meaningful reasoning or action stage. Plan the path 
that an expert compliance analyst would follow.
```

#### `executor_prompt.txt`
```
You are an AI executor. Perform the step given. Use the available tools 
to gather facts, analyze risks, and fill in missing context. Respond 
only with the step output.
```

#### `reflection_prompt.txt`
```
You are an AI critic. Evaluate the previous step for correctness, 
completeness, compliance risk, hallucination, and missing data. 
Suggest improvements or corrections.
```

**Current Status:** ✅ **Fully Implemented** - Reasoning engine functional, JSON parsing robust, prompts loaded correctly

---

### 4. Tools (`tools/`)

**Purpose:** Enable agent to interact with external systems and data.

#### HTTP Tool (`http_tool.py`)
- **Purpose:** Make HTTP requests to external APIs
- **Methods:** `get()`, `post()`
- **Use Cases:** Fetch regulatory data, API lookups, external validation

#### Calendar Tool (`calendar_tool.py`)
- **Purpose:** Manage compliance deadlines and schedules
- **Methods:** `get_deadlines()`, `add_deadline()`
- **Use Cases:** Deadline tracking, schedule compliance activities

#### Entity Tool (`entity_tool.py`)
- **Purpose:** Analyze entities and retrieve entity information
- **Methods:** `analyze_entity()`, `get_entity_history()`
- **Use Cases:** Entity profiling, historical analysis, risk assessment

#### Task Tool (`task_tool.py`)
- **Purpose:** Manage and analyze compliance tasks
- **Methods:** `analyze_task()`, `get_task_status()`
- **Use Cases:** Task categorization, status tracking, dependency mapping

**Current Status:** ✅ **Fully Implemented** - All tools functional (HTTPTool, CalendarTool, EntityTool, TaskTool), available for use

---

### 5. Scoring Assistant (`scoring/score_assistant.py`)

**Purpose:** Evaluate quality of agent outputs and decisions.

**Class:** `ScoreAssistant`

**Metrics:**
- **Quality Score:** Overall rating (0.0 - 1.0)
- **Correctness:** Factual accuracy validation
- **Completeness:** Requirement coverage check
- **Confidence:** Reliability of the output
- **Risk Assessment:** Compliance risk evaluation

**Current Status:** ⏳ **PHASE 3** - Scaffold complete, scoring logic pending (reflection provides quality scores currently)

---

### 6. Memory System (`memory/` - PHASE 3)

**Purpose:** Enable learning and pattern recognition across sessions.

#### Memory Store (`memory_store.py`)
- Central storage interface
- Methods: `store()`, `retrieve()`, `search()`
- Backend: TBD (SQLite, PostgreSQL, or Vector DB)

#### Episodic Memory (`episodic_memory.py`)
- Stores specific analysis events
- Chronological record of actions and outcomes
- Enables "remembering" past decisions

#### Semantic Memory (`semantic_memory.py`)
- Stores learned knowledge and patterns
- Abstracts concepts from specific episodes
- Enables generalization and transfer learning

**Current Status:** ✅ Scaffolds complete, ⏳ Implementation planned (PHASE 3)

---

## Development Phases

### ✅ PHASE 1: Structure (Complete)

**Timeline:** November 2024  
**Status:** ✅ **COMPLETE**

**Deliverables:**
- [x] Directory structure created (`src/agentic_engine/`)
- [x] Class scaffolds implemented (orchestrator, agent_loop, etc.)
- [x] API endpoints defined (`/api/v1/agentic/*`)
- [x] Dashboard page created (`5_Agentic_Analysis.py`)
- [x] Prompts written (planner, executor, reflector)
- [x] Documentation created (this file + updates)
- [x] README updated with configuration

**What Works:**
- ✅ API endpoints respond with valid structure
- ✅ Dashboard page loads and renders
- ✅ Form validation works
- ✅ All imports successful
- ✅ Placeholder responses demonstrate structure

**What Doesn't:**
- ❌ No actual LLM reasoning
- ❌ No tool execution
- ❌ No quality scoring
- ❌ No memory storage

---

### ✅ PHASE 2: Logic Implementation + Integration (Complete)

**Timeline:** November 2025  
**Status:** ✅ **COMPLETE**

**Deliverables:**
- [x] Implement orchestrator logic with LLM calls
- [x] Connect tools to real backend services
- [x] Implement execution loop with error handling
- [x] Add reflection evaluation logic
- [x] Add retry and recovery mechanisms
- [x] Add comprehensive error handling
- [x] Integration layer (transformation function)
- [x] API endpoint returns real results (not placeholders)
- [x] UI displays real analysis results
- [x] Status endpoint shows correct implementation flags

**What Works:**
- ✅ Orchestrator generates real plans with OpenAI (3-7 steps)
- ✅ Tools successfully fetch/update data (HTTPTool, EntityTool, TaskTool, CalendarTool)
- ✅ Reflection provides meaningful quality assessment
- ✅ End-to-end workflow completes successfully
- ✅ Response time 10-30 seconds for typical tasks
- ✅ Transformation layer maps orchestrator output to API response
- ✅ UI displays complete reasoning chain

**What's Pending:**
- ⏳ Real-time progress streaming (future enhancement)
- ⏳ Unit tests for all components (structure tests exist)
- ⏳ Performance optimization (acceptable currently)
- ⏳ Tool integration into step execution (tools available but not auto-called)

---

### 📋 PHASE 3: Memory & Learning (Planned)

**Timeline:** Q1 2026 (Target)  
**Status:** 📋 **PLANNED**

**Goals:**
- [ ] Implement memory store backend (choose: SQLite, PostgreSQL, Vector DB)
- [ ] Add episodic memory recording (store each analysis)
- [ ] Build semantic knowledge extraction (learn patterns)
- [ ] Enable cross-session learning (improve over time)
- [ ] Implement pattern recognition (identify similar cases)
- [ ] Add memory-augmented reasoning (use past experience)
- [ ] Create memory management UI
- [ ] Implement memory pruning/archival
- [ ] Add privacy controls for memory

**Success Criteria:**
- Agent remembers past analyses
- Quality improves with experience
- Similar cases handled more efficiently
- Patterns identified and reused
- Memory doesn't degrade performance

---

## API Documentation

### Endpoint: POST `/api/v1/agentic/analyze`

**Description:** Perform deep compliance analysis using agentic reasoning.

**Request:**
```json
{
  "entity": {
    "entity_name": "string",
    "entity_type": "string",
    "locations": ["string"],
    "industry": "string",
    "employee_count": integer,
    "has_personal_data": boolean,
    "is_regulated": boolean,
    "previous_violations": integer
  },
  "task": {
    "task_description": "string",
    "task_category": "string",
    "priority": "string",
    "deadline": "string (ISO format)"
  },
  "max_iterations": integer
}
```

**Response:**
```json
{
  "status": "string",
  "plan": [
    {
      "step_id": "string",
      "description": "string",
      "rationale": "string",
      "expected_tools": ["string"],
      "dependencies": ["string"]
    }
  ],
  "step_outputs": [
    {
      "step_id": "string",
      "status": "string",
      "output": "string",
      "tools_used": ["string"],
      "metrics": {}
    }
  ],
  "reflections": [
    {
      "step_id": "string",
      "quality_score": number,
      "correctness": boolean,
      "completeness": boolean,
      "confidence": number,
      "issues": ["string"],
      "suggestions": ["string"]
    }
  ],
  "final_recommendation": "string",
  "confidence_score": number,
  "execution_metrics": {}
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/agentic/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "entity": {
      "entity_name": "TechCorp Inc",
      "locations": ["US", "EU"],
      "industry": "TECHNOLOGY",
      "employee_count": 150
    },
    "task": {
      "task_description": "Implement GDPR Article 30 records",
      "task_category": "DATA_PROTECTION",
      "priority": "HIGH"
    },
    "max_iterations": 10
  }'
```

---

### Endpoint: GET `/api/v1/agentic/status`

**Description:** Get status information about the agentic AI engine.

**Response:**
```json
{
  "status": "experimental",
  "version": "0.1.0",
  "phase": "PHASE 2 - Implementation Complete, Integration Pending",
  "orchestrator_implemented": true,
  "agent_loop_implemented": true,
  "reasoning_engine_implemented": true,
  "tools_implemented": true,
  "memory_implemented": false,
  "integration_complete": false,
  "next_steps": ["string"]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/agentic/status
```

---

## Dashboard Integration

### Page: `5_Agentic_Analysis.py`

**Location:** `dashboard/pages/5_Agentic_Analysis.py`

**Access:** http://localhost:8501 → "🤖 Agentic Analysis" in sidebar

**Features:**

#### Input Form
- **Entity Information**
  - Entity name, type, industry
  - Employee count, locations
  - Personal data handling, regulatory status
  - Previous violations

- **Task Information**
  - Task description (text area)
  - Category, priority, deadline
  - Additional context

- **Advanced Options**
  - Max iterations slider (3-20)

#### Results Display (5 Tabs)

**1. 📋 Plan Tab**
- Shows execution plan steps
- Displays rationale for each step
- Lists expected tools and dependencies

**2. ⚙️ Step Outputs Tab**
- Execution results for each step
- Status indicators (✅/⏳/❌)
- Tools used and execution metrics

**3. 🔍 Reflections Tab**
- Quality scores with color coding
- Correctness/Completeness/Confidence metrics
- Issues identified and suggestions

**4. 💡 Recommendation Tab**
- Final recommendation in styled box
- Overall confidence score
- Download full report as JSON

**5. 🧠 Memory & Metrics Tab**
- Execution metrics (steps, duration, status, success rates)
- Real-time metrics from agent loop
- Raw metrics viewer
- PHASE 3 memory features pending

**Quick Actions:**
- ⚡ Load Example - Populate form with sample data
- 🔄 Reset Form - Clear all fields

---

## Configuration

### Environment Variables

```bash
# Required for Agentic Engine (PHASE 2 Complete - Now Required)
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini
BACKEND_URL=http://localhost:8000
```

### Setup

1. **Add to `.env` file:**
```bash
echo "OPENAI_API_KEY=your-key-here" >> .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
echo "BACKEND_URL=http://localhost:8000" >> .env
```

2. **Verify configuration:**
```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

3. **Test imports:**
```bash
python3 -c "from backend.agentic_engine.orchestrator import AgenticAIOrchestrator; print('✅ Ready')"
```

---

## Development Guide

### Getting Started

1. **Understand the architecture** (see diagrams above)
2. **Review scaffolds** in `src/agentic_engine/`
3. **Check prompts** in `reasoning/prompts/`
4. **Test API endpoints** with curl
5. **Explore dashboard** at http://localhost:8501

### Adding New Features

#### Example: Implementing a New Tool

1. **Create tool file:** `src/agentic_engine/tools/my_tool.py`

```python
class MyTool:
    """Description of what this tool does."""
    
    def __init__(self):
        pass
    
    def my_method(self, param: str) -> dict:
        """Method description."""
        # Implementation
        return {"result": "data"}
```

2. **Register in `__init__.py`:**
```python
from .my_tool import MyTool
__all__ = [..., "MyTool"]
```

3. **Use in orchestrator/agent loop:**
```python
tool = MyTool()
result = tool.my_method("param")
```

### Code Style

- **Type hints:** Use for all function parameters and returns
- **Docstrings:** Required for all classes and public methods
- **Error handling:** Use try-except with specific exceptions
- **Logging:** Use Python logging module (not print)
- **Testing:** Write tests alongside implementation

---

## Testing

### Current Tests (PHASE 1)

**Structure Tests:**
```bash
# Verify directory structure
ls -la src/agentic_engine/

# Count Python files
find src/agentic_engine -name "*.py" | wc -l

# Test imports
python3 -c "from backend.agentic_engine.orchestrator import AgenticAIOrchestrator"
```

**API Tests:**
```bash
# Test analyze endpoint
curl -X POST http://localhost:8000/api/v1/agentic/analyze \
  -H "Content-Type: application/json" \
  -d '{"entity": {"entity_name": "Test"}, "task": {"task_description": "Test"}}'

# Test status endpoint
curl http://localhost:8000/api/v1/agentic/status
```

**Dashboard Tests:**
1. Navigate to http://localhost:8501
2. Click "🤖 Agentic Analysis"
3. Click "⚡ Load Example"
4. Click "Run Agentic Analysis"
5. Verify all 5 tabs display content

### Future Tests (PHASE 2)

**Unit Tests:**
- [ ] Orchestrator methods
- [ ] Agent loop functions
- [ ] Tool integrations
- [ ] Scoring calculations
- [ ] Memory operations

**Integration Tests:**
- [ ] End-to-end workflow
- [ ] API endpoint responses
- [ ] Dashboard functionality
- [ ] Error scenarios
- [ ] Performance benchmarks

**Test Coverage Target:** 90%+

---

## Roadmap

### ✅ Completed (November 2025) - PHASE 2

- [x] **PHASE 2:** Implementation + Integration complete
- [x] Orchestrator fully implemented
- [x] Agent loop functional
- [x] Reasoning engine integrated
- [x] Tools implemented (HTTPTool, CalendarTool, EntityTool, TaskTool)
- [x] API integration complete
- [x] UI integration functional
- [x] **Architecture Hardening (v1.3.0):** Service/Repository layers, Dependency Injection

### Near Term (Q1 2025) - PHASE 3 Planning

- [ ] **Tool Auto-Integration:** Integrate tools into step execution automatically
- [ ] **Memory System Design:** Design database schema for episodic/semantic memory
- [ ] **Performance Optimization:** Reduce execution time (target: <20s)
- [ ] **Enhanced Error Handling:** Better retry strategies

### Medium Term (Q2 2025) - PHASE 3 Implementation

- [ ] **PHASE 3: Memory Systems** - Implement EpisodicMemory and SemanticMemory
- [ ] **PHASE 3: ScoreAssistant** - Integrate quality scoring system
- [ ] **Database Persistence** - Store memory across sessions
- [ ] **Cross-Session Learning** - Learn from previous analyses
- [ ] **Pattern Recognition** - Identify compliance patterns

### Long Term (Q3-Q4 2025)

- [ ] Production hardening
- [ ] Security audit
- [ ] Performance at scale
- [ ] Advanced reasoning patterns
- [ ] Multi-agent collaboration

---

## Limitations & Considerations

### Current Limitations (PHASE 2)

- ⚠️ **Tools Not Auto-Integrated:** Tools exist and work, but not automatically called during step execution
- ⚠️ **No Memory Persistence:** Memory systems are stubs (PHASE 3)
- ⚠️ **No Cross-Session Learning:** Cannot learn or remember between sessions (PHASE 3)
- ⚠️ **No Real-Time Progress:** Results returned after completion (future enhancement)
- ⚠️ **Limited Unit Tests:** Structure tests exist, full unit tests pending

### Design Trade-offs

**Slower than Traditional Engine:**
- Traditional: <1s
- Agentic: 10-30s (expected)
- Reason: Multiple LLM calls, tool usage, reflection

**Higher Cost:**
- More API calls to OpenAI
- Larger context windows
- Multiple reasoning steps
- Trade-off: Depth vs. speed/cost

**Increased Complexity:**
- More components to maintain
- More potential failure points
- More debugging required
- Trade-off: Capability vs. simplicity

---

## Support & Feedback

### Reporting Issues

**Label:** `[EXPERIMENTAL]` in issue title  
**Include:**
- Phase you're testing (PHASE 1/2/3)
- Expected vs. actual behavior
- Environment details
- Note that placeholder responses are expected in PHASE 1

### Contributing

Contributions welcome for PHASE 2+!

**Areas for Contribution:**
- Tool implementation
- Prompt engineering
- Memory system design
- Performance optimization
- Test coverage

### Contact

**Project Lead:** Nikita Walvekar  
**Email:** walvekarn@gmail.com  
**Label:** [AGENTIC ENGINE] in subject

---

## References

### Internal Documentation
- [ARCHITECTURE.md](../production_engine/ARCHITECTURE.md) - System architecture
- [FEATURE_INVENTORY.md](../production_engine/FEATURE_INVENTORY.md) - Feature #6 details
- [VERSION.md](../VERSION.md) - Version status
- [TESTING_CHECKLIST.md](../TESTING_CHECKLIST.md) - Testing procedures
- [KNOWN_ISSUES.md](../issues/KNOWN_ISSUES.md) - Known limitations

### External Resources
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [LangChain Documentation](https://python.langchain.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**Document Version:** 1.0  
**Last Updated:** November 15, 2025  
**Status:** Living Document (Updated with each phase)  
**Maintainer:** AI Compliance Agent Team

---

*This is an experimental feature. Not recommended for production use. Use at your own risk.*

