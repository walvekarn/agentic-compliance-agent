# Testing Checklist
**AI Agentic Compliance Assistant - Verification Guide**

Use this checklist to verify the system is working correctly after setup or updates.

---

## 📋 Pre-Flight Checklist

### Environment Setup
- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows fastapi, streamlit, etc.)
- [ ] `.env` file exists with required secrets (`SECRET_KEY`, `JWT_SECRET`), optional `OPENAI_API_KEY` (mock mode when absent)
- [ ] Database file `compliance.db` will be created on first run (sqlite) or point `DATABASE_URL` to your DB

---

## 🔧 Backend Verification

### 1. Backend Startup
- [ ] **Backend starts without errors**
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port 8000
  ```
  - Expected: "Application startup complete"
  - No import errors
  - Database tables created/connected successfully

### 2. Health Endpoint
- [ ] **Health endpoint returns 200**
  ```bash
  curl http://localhost:8000/health
  ```
  - Expected: JSON with `status: healthy` (LLM may be `skipped` if no API key)
  - Status code: 200

### 3. Database Initialization
- [ ] **Database is initialized**
  - Triggered automatically on backend startup via `Base.metadata.create_all`
  - Tables should include: `audit_trail`, `entity_history`, `feedback_log`
  - For sqlite, file `compliance.db` should exist and have size > 0

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
  streamlit run frontend/Home.py
  ```
  - Expected: "You can now view your Streamlit app in your browser"
  - URL: http://localhost:8501
  - No import errors in console

### 6. Authentication
- [ ] **Authentication works**
  - Navigate to http://localhost:8501
  - See login page with password field
  - Demo credentials (default): `demo/demo123` (replace with real auth for production)
  - Click "Login"
  - Expected: Redirected to dashboard home; session persists on refresh

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

### 11. Chat Assistant
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
  6. Navigate to Agentic Analysis page
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

## 📊 Performance Testing

### Page Load Times
- [ ] **Login page loads in < 3 seconds**
  - Navigate to login page
  - Measure time from navigation to fully rendered
  - Expected: Complete render in < 3 seconds

- [ ] **Home page loads in < 3 seconds**
  - After login, navigate to Home page
  - Measure time from navigation to fully rendered
  - Expected: All cards and metrics visible in < 3 seconds

- [ ] **Analyze Task page loads in < 3 seconds**
  - Navigate to "Analyze Task" page
  - Measure time from navigation to form fully rendered
  - Expected: All form fields visible in < 3 seconds

- [ ] **Audit Trail page loads in < 5 seconds (with data)**
  - Navigate to "Audit Trail" page
  - Measure time from navigation to data displayed
  - Expected: Charts and table visible in < 5 seconds (may be longer with large datasets)

- [ ] **Agentic Analysis page loads in < 3 seconds**
  - Navigate to "Agentic Analysis" page
  - Measure time from navigation to form fully rendered
  - Expected: Form and tabs visible in < 3 seconds

### Agentic Operations
- [ ] **Agentic Analysis completes in < 120 seconds**
  - Submit a task for agentic analysis
  - Monitor progress indicators
  - Expected: Complete analysis within 120 seconds (AGENTIC_OPERATION_TIMEOUT)
  - No timeout errors for standard tasks

- [ ] **Test Suite completes all scenarios in < 180 seconds**
  - Run the Agentic Test Suite
  - Monitor execution time
  - Expected: All test scenarios complete within 180 seconds
  - Progress indicators show advancement

- [ ] **Timeout errors show user-friendly messages**
  - If timeout occurs, verify error message is displayed
  - Expected: Clear message like "Analysis timed out after 120 seconds"
  - Message includes troubleshooting guidance

### Response Times (Legacy)
- [ ] **System responds within acceptable time**
  - Health check: < 100ms
  - Task analysis: < 10 seconds
  - Chat response: < 15 seconds
  - Audit trail load: < 2 seconds
  - Dashboard page load: < 3 seconds

### Concurrent Requests
- [ ] **System handles multiple requests**
  - Open 2-3 browser tabs
  - Perform actions simultaneously
  - Expected: All complete successfully

---

## 🖥️ Display Validation

### Audit Trail Charts
- [ ] **"Decisions by Outcome" chart displays with data**
  - Navigate to Audit Trail page
  - Ensure audit data exists (submit a task analysis first)
  - Expected: Pie or bar chart showing AUTONOMOUS, REVIEW_REQUIRED, ESCALATE counts
  - Chart is interactive (hover shows values)

- [ ] **"Decisions by Risk Level" chart displays with data**
  - On Audit Trail page with data
  - Expected: Chart showing LOW, MEDIUM, HIGH risk level distribution
  - Chart renders correctly with proper labels

- [ ] **Charts show correct colors (green/yellow/red)**
  - Verify color coding:
    - Green: Low risk / AUTONOMOUS decisions
    - Yellow: Medium risk / REVIEW_REQUIRED decisions
    - Red: High risk / ESCALATE decisions
  - Expected: Colors match risk/decision semantics

- [ ] **Empty state shows helpful message**
  - Navigate to Audit Trail page with no data
  - Expected: Message like "No audit data available. Submit a task analysis first."
  - No broken chart placeholders

### Agentic Test Suite
- [ ] **Confidence Deviations chart renders**
  - Run Agentic Test Suite
  - Navigate to results section
  - Expected: Bar chart showing confidence deviations for each scenario
  - Chart shows positive (green) and negative (red) deviations

- [ ] **Deviation Data Table shows all columns**
  - In Test Suite results, check deviation table
  - Expected: Columns visible: scenario, expected_min, actual, deviation, adequate
  - All columns have data (no empty cells for valid scenarios)

- [ ] **Detailed Test Results table displays**
  - Check "Detailed Test Results" section
  - Expected: Table with columns: Scenario, Status, Decision Match, Risk Match, Confidence OK, Expected/Actual values
  - All test scenarios listed

- [ ] **Pass/Fail indicators are visible**
  - In Detailed Test Results table
  - Expected: ✅ for pass, ❌ for fail
  - Status column shows "✅ Pass" or "❌ Fail"
  - Match indicators (Decision Match, Risk Match, Confidence OK) show ✅ or ❌

## 📋 Data Integrity

- [ ] **All audit records show complete data (no empty fields)**
  - Navigate to Audit Trail page
  - Review several audit entries
  - Expected: All required fields populated:
    - entity_name (not "Unknown Entity" unless actually unknown)
    - task_description (not "No description")
    - decision_outcome (not empty)
    - risk_level (not empty)
    - confidence_score (not 0.5 default unless actually 0.5)
    - agent_type (not empty)
  - Check backend logs for validation warnings

- [ ] **Statistics match actual record counts**
  - On Audit Trail page, note statistics shown
  - Count actual entries in table/list
  - Expected: Statistics totals match visible entries
  - Decision outcome counts match actual distribution
  - Risk level counts match actual distribution

- [ ] **Test results match expected format**
  - Run Agentic Test Suite
  - Review test results structure
  - Expected: Each result contains:
    - scenario (with title)
    - expected (decision, risk_level, min_confidence)
    - actual (decision, risk_level, confidence)
    - passed (boolean)
    - decision_correct (boolean)
    - risk_level_correct (boolean)
    - confidence_adequate (boolean)
  - All boolean fields are properly set (not None)

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
  ls -la backend/agentic_engine/
  ```
  - Expected: orchestrator.py, agent_loop.py, reasoning/, tools/, scoring/, memory/
  
- [ ] **Files created successfully**
  ```bash
  find backend/agentic_engine -name "*.py" | wc -l
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
  python3 -c "from backend.agentic_engine.orchestrator import AgenticAIOrchestrator; print('✅ Imports OK')"
  ```
  - Expected: No import errors

- [ ] **API routes import**
  ```bash
  python3 -c "from backend.api.agentic_routes import router; print('✅ Routes OK')"
  ```
  - Expected: No import errors

### 5. Documentation Verification

- [ ] **README updated**
  - Check README.md contains agentic engine configuration section
  - Expected: Environment variables documented

- [ ] **ARCHITECTURE_v2.md updated**
  - Check docs/ARCHITECTURE_v2.md
  - Expected: Agentic engine section present
  - Note: Architecture documentation is consolidated in ARCHITECTURE_v2.md

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

**Total Items:** 28 major checkpoints + 19 performance/display/data items + 10 experimental (agentic)  
**Time to Complete:** 30-45 minutes (core) + 15 minutes (performance/display) + 10 minutes (experimental)  
**Required for:** Initial setup, after updates, before deployment

**New Sections Added:**
- Performance Testing: Page load times, agentic operation timeouts
- Display Validation: Chart rendering, test suite displays
- Data Integrity: Audit record completeness, statistics accuracy

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

**Last Updated:** December 10, 2025  
**Version:** 1.0.0  
**Status:** ✅ All items verified and working

