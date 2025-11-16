# Testing Checklist
**AI Agentic Compliance Assistant - Verification Guide**

Use this checklist to verify the system is working correctly after setup or updates.

---

## 📋 Pre-Flight Checklist

### Environment Setup
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows fastapi, streamlit, etc.)
- [ ] `.env` file exists with valid `OPENAI_API_KEY`
- [ ] Database file `compliance.db` exists

---

## 🔧 Backend Verification

### 1. Backend Startup
- [ ] **Backend starts without errors**
  ```bash
  uvicorn main:app --port 8000
  ```
  - Expected: "Application startup complete"
  - No import errors
  - No database connection errors

### 2. Health Endpoint
- [ ] **Health endpoint returns 200**
  ```bash
  curl http://localhost:8000/health
  ```
  - Expected: `{"status": "healthy", "version": "1.0.0"}`
  - Status code: 200

### 3. Database Initialization
- [ ] **Database is initialized**
  ```bash
  python scripts/setup_database.py
  ```
  - Expected: "✅ Database tables created successfully"
  - Tables created: `audit_trail`, `entity_history`, `feedback_log`
  - File `compliance.db` exists and has size > 0

### 4. API Endpoints Respond Correctly

#### Decision Analysis Endpoint
- [ ] **POST /api/v1/decision/analyze**
  ```bash
  curl -X POST http://localhost:8000/api/v1/decision/analyze \
    -H "Content-Type: application/json" \
    -d '{
      "entity": {
        "name": "Test Corp",
        "entity_type": "PRIVATE_COMPANY",
        "industry": "TECHNOLOGY",
        "jurisdictions": ["US_FEDERAL"],
        "employee_count": 50,
        "annual_revenue": 5000000.0,
        "has_personal_data": true,
        "is_regulated": false,
        "previous_violations": 0
      },
      "task": {
        "description": "Review privacy policy",
        "category": "POLICY_REVIEW",
        "affects_personal_data": false,
        "affects_financial_data": false,
        "involves_cross_border": false
      }
    }'
  ```
  - Expected: JSON response with `risk_level`, `decision`, `recommendations`
  - Status code: 200

#### Audit Trail Endpoint
- [ ] **GET /api/v1/audit/entries**
  ```bash
  curl http://localhost:8000/api/v1/audit/entries
  ```
  - Expected: JSON array (may be empty initially)
  - Status code: 200

#### Query Endpoint (Chat)
- [ ] **POST /api/v1/query**
  ```bash
  curl -X POST http://localhost:8000/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is GDPR?"}'
  ```
  - Expected: JSON with `response` field containing text
  - Status code: 200

#### Feedback Endpoint
- [ ] **POST /api/v1/feedback**
  ```bash
  curl -X POST http://localhost:8000/api/v1/feedback \
    -H "Content-Type: application/json" \
    -d '{
      "audit_id": 1,
      "feedback_type": "OVERRIDE",
      "original_decision": "AUTONOMOUS",
      "corrected_decision": "REVIEW_REQUIRED",
      "reason": "Testing feedback system"
    }'
  ```
  - Expected: JSON confirmation
  - Status code: 200 or 201

#### Entity Analysis Endpoint
- [ ] **POST /api/v1/entity/analyze**
  ```bash
  curl -X POST http://localhost:8000/api/v1/entity/analyze \
    -H "Content-Type: application/json" \
    -d '{
      "entity_name": "Test Company",
      "entity_type": "PRIVATE_COMPANY",
      "locations": ["United States"],
      "employee_count": 100,
      "annual_revenue": 10000000.0,
      "data_types": ["PII"],
      "current_obligations": ["GDPR Compliance"]
    }'
  ```
  - Expected: JSON with compliance calendar
  - Status code: 200

---

## 🎨 Frontend Verification

### 5. Dashboard Startup
- [ ] **Dashboard loads without errors**
  ```bash
  streamlit run dashboard/Home.py
  ```
  - Expected: "You can now view your Streamlit app in your browser"
  - URL: http://localhost:8501
  - No import errors in console

### 6. Authentication
- [ ] **Authentication works**
  - Navigate to http://localhost:8501
  - See login page with password field
  - Enter password: `demo123`
  - Click "Login"
  - Expected: Redirected to dashboard home
  - Session persists on page refresh

### 7. Home Page
- [ ] **Home page renders correctly**
  - See "AI Agentic Compliance Assistant" title
  - Four action cards visible:
    - ✅ Check One Task
    - 📅 Plan All Tasks
    - 📊 Review History
    - 🤖 Agent Insights
  - System status shown
  - Chat assistant visible in sidebar

### 8. Task Analysis
- [ ] **Task analysis completes successfully**
  - Click "Check One Task" or navigate to "Analyze Task" page
  - Fill out entity form:
    - Name: "Test Corp"
    - Type: "Private Company"
    - Industry: "Technology"
    - Location: "United States"
    - Employee count: 50
    - Annual revenue: 5000000
    - Check "Has personal data"
  - Fill out task form:
    - Description: "Update employee handbook with remote work policy"
    - Category: "Policy Review"
  - Click "Analyze Task"
  - Expected:
    - Progress indicators show
    - Results appear within 10 seconds
    - No error messages

### 9. Results Display
- [ ] **Results display correctly**
  - See decision card with:
    - Risk level badge (Low/Medium/High)
    - Decision type (AUTONOMOUS/REVIEW/ESCALATE)
    - Confidence score (0-100%)
  - Risk factors shown with scores:
    - Jurisdiction Risk
    - Entity Risk
    - Task Complexity
    - Data Sensitivity
    - Regulatory Risk
    - Impact Risk
  - Reasoning chain displayed
  - Recommendations listed
  - Visualizations render (charts, gauges)

### 10. Audit Trail
- [ ] **Audit trail shows decisions**
  - Navigate to "Audit Trail" page
  - See table/list of decisions
  - Previous analysis appears in list
  - Can filter by:
    - Date range
    - Decision type
    - Risk level
  - Can export data
  - Clicking entry shows details

### 11. Agent Insights
- [ ] **Agent Insights renders charts**
  - Navigate to "Agent Insights" page
  - See dashboard with metrics:
    - Total decisions
    - Decision distribution pie chart
    - Risk score histogram
    - Timeline chart
  - Charts render without errors
  - Data matches audit trail

### 12. Chat Assistant
- [ ] **Chat assistant responds**
  - Open chat panel (sidebar or main area)
  - Type message: "What is GDPR?"
  - Click "Send"
  - Expected:
    - Message appears in chat
    - "AI is thinking..." indicator shows
    - Response appears within 10 seconds
    - Response is relevant to query
  - Try context-aware question after analysis:
    - "Why was this decision autonomous?"
    - Should reference recent analysis

### 13. Compliance Calendar
- [ ] **Compliance calendar generates**
  - Navigate to "Compliance Calendar" page
  - Fill out entity information
  - Click "Generate Calendar"
  - Expected:
    - Calendar displays
    - Shows upcoming obligations
    - Deadlines highlighted
    - Can download as CSV/PDF

---

## 🧪 Automated Tests

### 14. Test Suite
- [ ] **All tests pass**
  ```bash
  pytest -v
  ```
  - Expected: "84 passed"
  - No failures
  - Execution time: < 5 seconds

### 15. Coverage Report
- [ ] **Coverage meets threshold**
  ```bash
  pytest --cov=src --cov-report=term-missing
  ```
  - Expected: Total coverage ≥ 84%
  - Core modules ≥ 90%:
    - decision_engine.py: ≥ 96%
    - risk_models.py: ≥ 99%
    - entity_analyzer.py: ≥ 98%

### 16. Dashboard Component Tests
- [ ] **Dashboard tests pass**
  ```bash
  python3 tests/test_auth_module.py
  python3 tests/test_chat_assistant.py
  python3 tests/test_dashboard_pages.py
  ```
  - Expected: All tests pass
  - No import errors
  - No runtime errors

---

## 🔍 Integration Tests

### 17. End-to-End Flow
- [ ] **Complete user workflow works**
  1. Login to dashboard
  2. Analyze a task
  3. View result
  4. Check audit trail (result appears)
  5. Ask chat question about result
  6. Navigate to Agent Insights (metrics updated)
  7. Generate compliance calendar
  - All steps complete without errors

### 18. Data Persistence
- [ ] **Data persists across sessions**
  1. Analyze a task
  2. Note the task details
  3. Close browser
  4. Restart dashboard (keep backend running)
  5. Login again
  6. Check audit trail
  - Expected: Previous task still visible

### 19. Backend-Frontend Communication
- [ ] **API calls succeed from dashboard**
  - Open browser dev tools (F12)
  - Navigate to Network tab
  - Perform task analysis
  - Check network requests:
    - POST to /api/v1/decision/analyze: Status 200
    - POST to /api/v1/query: Status 200
    - No CORS errors
    - No 500 errors

---

## 🚨 Error Handling

### 20. Backend Offline Handling
- [ ] **Dashboard handles backend offline gracefully**
  1. Stop backend server
  2. Try to analyze task in dashboard
  - Expected:
    - Error message: "Cannot connect to backend"
    - No crash
    - Can retry after backend restart

### 21. Invalid Input Handling
- [ ] **Validation works correctly**
  1. Try to submit task with empty fields
  - Expected: Validation errors shown
  2. Try negative employee count
  - Expected: Validation error
  3. Try invalid data in API
  - Expected: 422 status with error details

### 22. Database Errors
- [ ] **Database issues handled**
  1. Delete `compliance.db` while backend running
  2. Try to analyze task
  - Expected: Error logged, user sees message
  3. Restart backend
  4. Run `python scripts/setup_database.py`
  - Expected: Database recreated, system works

---

## 📊 Performance Checks

### 23. Response Times
- [ ] **System responds within acceptable time**
  - Health check: < 100ms
  - Task analysis: < 10 seconds
  - Chat response: < 15 seconds
  - Audit trail load: < 2 seconds
  - Dashboard page load: < 3 seconds

### 24. Concurrent Requests
- [ ] **System handles multiple requests**
  - Open 2-3 browser tabs
  - Perform actions simultaneously
  - Expected: All complete successfully

---

## 🔐 Security Checks

### 25. Authentication Protection
- [ ] **Protected pages require auth**
  1. Clear browser storage/cookies
  2. Navigate directly to http://localhost:8501/?page=Audit_Trail
  - Expected: Redirected to login or see warning

### 26. API Security
- [ ] **API key required**
  1. Remove OPENAI_API_KEY from .env
  2. Restart backend
  3. Try to analyze task
  - Expected: Error about missing API key

---

## ✅ Final Verification

### 27. Documentation Accuracy
- [ ] README Quick Start works as written
- [ ] All documented endpoints exist
- [ ] Screenshots match current UI (if provided)

### 28. Clean Shutdown
- [ ] **Services stop cleanly**
  ```bash
  # Stop backend: Ctrl+C
  # Stop dashboard: Ctrl+C
  ```
  - Expected: No hanging processes
  - No errors on shutdown

---

## 🧪 Experimental: Agentic AI Engine Testing

### 1. Structure Verification (PHASE 1)

- [ ] **Directory structure exists**
  ```bash
  ls -la src/agentic_engine/
  ```
  - Expected: orchestrator.py, agent_loop.py, reasoning/, tools/, scoring/, memory/
  
- [ ] **Files created successfully**
  ```bash
  find src/agentic_engine -name "*.py" | wc -l
  ```
  - Expected: 17+ Python files

### 2. API Endpoint Testing

#### Agentic Analysis Endpoint
- [ ] **POST /api/v1/agentic/analyze**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agentic/analyze \
    -H "Content-Type: application/json" \
    -d '{
      "entity": {
        "entity_name": "Test Corp",
        "locations": ["US"],
        "industry": "TECHNOLOGY"
      },
      "task": {
        "task_description": "Test task",
        "task_category": "DATA_PROTECTION"
      }
    }'
  ```
  - Expected: Status code 200
  - Response contains: plan, step_outputs, reflections, final_recommendation
  - Returns real orchestrator results (PHASE 2 Complete)

#### Status Endpoint
- [ ] **GET /api/v1/agentic/status**
  ```bash
  curl http://localhost:8000/api/v1/agentic/status
  ```
  - Expected: Status code 200
  - Response contains: status: "experimental", phase: "PHASE 2 - Implementation Complete", orchestrator_implemented: true

### 3. Dashboard Integration

- [ ] **Agentic Analysis page loads**
  - Navigate to http://localhost:8501
  - Click "🤖 Agentic Analysis" in sidebar
  - Expected: Page loads without errors

- [ ] **Form validation works**
  - Try submitting empty form
  - Expected: Validation errors shown

- [ ] **Example data loads**
  - Click "⚡ Load Example"
  - Expected: Form fields populate with sample data

- [ ] **Analysis submission works**
  - Fill form with valid data
  - Click "Run Agentic Analysis"
  - Expected: Real analysis results appear in tabs

- [ ] **Results tabs functional**
  - Check "Plan", "Step Outputs", "Reflections", "Recommendation", "Memory & Metrics" tabs
  - Expected: All tabs clickable and display content

### 4. Import Testing

- [ ] **Python imports work**
  ```bash
  python3 -c "from src.agentic_engine.orchestrator import AgenticAIOrchestrator; print('✅ Imports OK')"
  ```
  - Expected: No import errors

- [ ] **API routes import**
  ```bash
  python3 -c "from src.api.agentic_routes import router; print('✅ Routes OK')"
  ```
  - Expected: No import errors

### 5. Documentation Verification

- [ ] **README updated**
  - Check README.md contains agentic engine configuration section
  - Expected: Environment variables documented

- [ ] **ARCHITECTURE.md updated**
  - Check docs/production_engine/ARCHITECTURE.md
  - Expected: Agentic engine section present

- [ ] **FEATURE_INVENTORY.md updated**
  - Check docs/production_engine/FEATURE_INVENTORY.md
  - Expected: Feature #6 describes agentic engine

### Status Notes

**Current Phase:** PHASE 2 Complete (Implementation + Integration)  
**Next Phase:** PHASE 3 (Memory + Scoring Extensions)  
**Stability:** Experimental - Fully Functional - Ready for Testing  
**Test Coverage:** Structure tests exist, integration validated

**Known Limitations:**
- Tools not auto-integrated into step execution (available but not auto-called)
- Memory system not functional (PHASE 3)
- ScoreAssistant not integrated (PHASE 3)
- Real LLM integration working, returns actual analysis results

---

## 📝 Checklist Summary

**Total Items:** 28 major checkpoints + 10 experimental (agentic)  
**Time to Complete:** 30-45 minutes (core) + 10 minutes (experimental)  
**Required for:** Initial setup, after updates, before deployment

---

## 🎯 Quick Smoke Test (5 minutes)

For a quick verification, test these critical items:

- [ ] Backend starts (Item 1)
- [ ] Health endpoint works (Item 2)
- [ ] Dashboard loads (Item 5)
- [ ] Login works (Item 6)
- [ ] Task analysis completes (Items 8-9)
- [ ] All automated tests pass (Item 14)

If all 6 pass, system is likely working correctly. Run full checklist for comprehensive verification.

---

## 🐛 If Tests Fail

1. **Check Prerequisites:**
   - Python version correct?
   - Dependencies installed?
   - API key configured?

2. **Check Logs:**
   - Backend console output
   - Browser console (F12)
   - `backend.log` file

3. **Try Clean Restart:**
   ```bash
   # Stop all services
   # Delete compliance.db
   python scripts/setup_database.py
   # Restart backend
   # Restart dashboard
   ```

4. **Consult Documentation:**
   - KNOWN_ISSUES.md
   - README.md Troubleshooting section
   - GitHub Issues

---

**Last Updated:** November 13, 2025  
**Version:** 1.0.0  
**Status:** ✅ All items verified and working

