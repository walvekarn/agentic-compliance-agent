# Known Issues
**AI Agentic Compliance Assistant**

This document tracks known bugs, workarounds, and planned fixes.

---

## 🚨 Critical Issues

### ❌ None Currently

All critical issues have been resolved as of version 1.0.0.

---

## ⚠️ Medium Priority Issues

### Issue #1: DateTime Timezone Handling in Proactive Suggestions

**Status:** 🐛 **IDENTIFIED - FIX PENDING**

**Component:** `src/agent/proactive_suggestions.py`

**Symptom:**
```python
TypeError: can't subtract offset-naive and offset-aware datetimes
```

**When It Occurs:**
- During task analysis when proactive suggestions are generated
- Specifically when calculating days until deadline
- In the dashboard after submitting a compliance analysis

**Root Cause:**
Mixing timezone-aware and timezone-naive datetime objects:
```python
# Line causing issue (approximate):
days_until = (deadline - datetime.now()).days
# If deadline is timezone-naive but datetime.now() returns timezone-aware
```

**Workaround:**
- Avoid using proactive suggestions feature temporarily
- Or ensure all datetime objects use the same timezone approach

**Proposed Fix:**
```python
# Option 1: Make both timezone-aware (RECOMMENDED)
from datetime import timezone
days_until = (deadline - datetime.now(timezone.utc)).days

# Option 2: Make both timezone-naive
days_until = (deadline - datetime.utcnow()).days
```

**Priority:** ⚠️ **MEDIUM**  
**Affects:** Proactive suggestions feature in dashboard  
**Blocking:** No - core functionality works without proactive suggestions  
**Fix ETA:** Next patch (v1.0.1)  
**Assigned:** Pending

---

## 🟡 Low Priority Issues

### Issue #2: CORS Configuration Warning

**Status:** ℹ️ **INFORMATIONAL - NOT A BUG**

**Component:** Streamlit server configuration

**Symptom:**
```
Warning: the config option 'server.enableCORS=false' is not compatible with
'server.enableXsrfProtection=true'.
As a result, 'server.enableCORS' is being overridden to 'true'.
```

**When It Occurs:**
- Every time Streamlit dashboard starts
- Visible in console output

**Root Cause:**
- Default Streamlit security settings conflict
- Streamlit automatically resolves by enabling CORS

**Impact:**
- ✅ **NO FUNCTIONAL IMPACT**
- Warning is informational only
- Both CORS and XSRF protection work correctly
- Security is not compromised

**Workaround:**
Create `.streamlit/config.toml`:
```toml
[server]
enableCORS = true
enableXsrfProtection = true
```

**Priority:** 🟢 **LOW**  
**Affects:** Developer experience (console clutter)  
**Blocking:** No  
**Fix ETA:** v1.1.0 (optional)

---

### Issue #3: API Endpoint Hardcoded to Localhost

**Status:** 🔧 **DESIGN LIMITATION**

**Component:** 
- `dashboard/components/chat_assistant.py`
- Multiple dashboard pages

**Symptom:**
```python
API_ENDPOINT = "http://localhost:8000/api/v1/query"
```

**When It Occurs:**
- When deploying to production/remote servers
- When backend is on different host/port

**Root Cause:**
- API endpoint hardcoded instead of using environment variables
- Designed for local development

**Workaround:**
Manually edit files to change endpoint:
```python
# dashboard/components/chat_assistant.py
API_ENDPOINT = os.getenv("BACKEND_URL", "http://localhost:8000") + "/api/v1/query"
```

**Proposed Fix:**
1. Add `BACKEND_URL` to `.env`
2. Update all dashboard pages to read from env
3. Add fallback to localhost for dev

**Priority:** 🟡 **LOW**  
**Affects:** Production deployment  
**Blocking:** No (acceptable for MVP/demo)  
**Fix ETA:** v1.1.0  
**Note:** This is by design for portfolio/demo purposes

---

## 🧪 Experimental Features Status

### Experimental #1: Agentic AI Engine

**Status:** ✅ **PHASE 2 COMPLETE - PHASE 3 PENDING**

**Component:** `src/agentic_engine/`

**Current State:**
- ✅ Directory structure created
- ✅ Orchestrator fully implemented
- ✅ Agent loop fully implemented
- ✅ Reasoning engine fully implemented
- ✅ Tools implemented (HTTPTool, CalendarTool, EntityTool, TaskTool)
- ✅ API endpoints return real results (`/api/v1/agentic/analyze`, `/api/v1/agentic/status`)
- ✅ Dashboard page functional (`5_Agentic_Analysis.py`)
- ✅ Transformation layer integrated
- ⏳ Memory systems pending (PHASE 3)
- ⏳ ScoreAssistant pending (PHASE 3)

**Known Limitations:**
1. **Tools Not Auto-Integrated:** Tools exist and work, but not automatically called during step execution
2. **Memory System Non-Functional:** Episodic and semantic memory systems are stubs (PHASE 3)
3. **No Cross-Session Learning:** Cannot learn or remember between sessions (PHASE 3)
4. **ScoreAssistant Not Used:** Class defined but not integrated (PHASE 3)

**What Works:**
- ✅ Orchestrator generates real plans with OpenAI (3-7 steps)
- ✅ Agent loop executes steps with reflection
- ✅ Reasoning engine provides LLM-powered reasoning
- ✅ Tools successfully fetch/update data
- ✅ API endpoints return real analysis results (not placeholders)
- ✅ Dashboard page displays real results
- ✅ Transformation layer maps orchestrator output correctly
- ✅ Error handling and retry mechanisms functional

**What's Pending:**
- ⏳ Memory persistence (PHASE 3)
- ⏳ Cross-session learning (PHASE 3)
- ⏳ Tool auto-integration into step execution
- ⏳ ScoreAssistant integration (PHASE 3)

**When You Should NOT Use:**
- ❌ Production environments
- ❌ Real compliance decisions
- ❌ Critical analysis
- ❌ Audit trail generation

**When You CAN Use:**
- ✅ Demo purposes (shows structure)
- ✅ Testing frontend integration
- ✅ API structure validation
- ✅ UI/UX feedback

**Configuration Requirements:**
```bash
# Required environment variables (for PHASE 2)
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
BACKEND_URL=http://localhost:8000
```

**Development Timeline:**
- **PHASE 1:** ✅ Complete (November 2024)
  - Structure, scaffolds, API, dashboard
  
- **PHASE 2:** ✅ Complete (January 2025)
  - Orchestrator logic implementation
  - Tool implementation
  - LLM reasoning integration
  - Execution loop with reflection
  - API integration with transformation layer
  
- **PHASE 3:** 📋 Planned (Target: Q2 2025)
  - Memory system implementation
  - Episodic memory recording
  - Semantic knowledge extraction
  - Cross-session learning
  - Pattern recognition

**Priority:** 🧪 **EXPERIMENTAL**  
**Stability:** Functional - Ready for Testing  
**Blocking:** No (isolated from main system)  
**Production Ready:** No (experimental, not recommended for production)

**How to Test:**
```bash
# Test structure
ls -la src/agentic_engine/

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/agentic/analyze \
  -H "Content-Type: application/json" \
  -d '{"entity": {"entity_name": "Test"}, "task": {"task_description": "Test"}}'

# Test dashboard
# Navigate to http://localhost:8501
# Click "Agentic Analysis" in sidebar
```

**Reporting Issues:**
- Label as `[EXPERIMENTAL]` in issue title
- Note which PHASE you're testing (PHASE 2 Complete, PHASE 3 Pending)
- Real analysis results are now returned (not placeholders)

---

## 🎯 Enhancement Requests

### Enhancement #1: Database Migration to PostgreSQL

**Status:** 📋 **PLANNED**

**Current:** SQLite (file-based)  
**Proposed:** PostgreSQL (production-ready)

**Reason:**
- SQLite is great for development/demos
- PostgreSQL needed for production scale
- Better concurrent access
- Advanced query capabilities

**Implementation:**
- Add PostgreSQL connection option
- Keep SQLite as default
- Environment variable to switch: `DATABASE_TYPE=postgresql`

**Priority:** 📋 **PLANNED**  
**ETA:** v1.1.0  
**Breaking Change:** No (backward compatible)

---

### Enhancement #2: Async Chat Responses

**Status:** 📋 **PLANNED**

**Current:** Synchronous API calls block UI  
**Proposed:** WebSocket or SSE for streaming responses

**Benefit:**
- Better user experience
- See response as it's generated
- Cancel long-running requests

**Priority:** 📋 **PLANNED**  
**ETA:** v1.2.0

---

### Enhancement #3: Export Formats

**Status:** 📋 **PLANNED**

**Current:** Limited export options  
**Proposed:** PDF, Excel, formatted reports

**Use Case:**
- Share with stakeholders
- Compliance documentation
- Audit preparation

**Priority:** 📋 **PLANNED**  
**ETA:** v1.1.0

---

## 🐛 Resolved Issues

### ✅ Issue: Import Errors in Dashboard Pages
**Resolved:** November 13, 2025  
**Version:** 1.0.0  
**Solution:** All dashboard pages validated, no import errors found

### ✅ Issue: Authentication Not Working
**Resolved:** November 13, 2025  
**Version:** 1.0.0  
**Solution:** Authentication system fully functional with demo password

### ✅ Issue: Backend Health Endpoint Missing
**Resolved:** November 12, 2025  
**Version:** 1.0.0  
**Solution:** Health endpoint implemented and tested

### ✅ Issue: Test Suite Failures
**Resolved:** November 13, 2025  
**Version:** 1.0.0  
**Solution:** All 84 tests passing with 84% coverage

---

## 📊 Issue Statistics

**Total Active Issues:** 3  
**Critical:** 0  
**Medium:** 1  
**Low:** 2  
**Experimental Features:** 1 (Agentic AI Engine - PHASE 2 Complete, PHASE 3 Pending)  
**Enhancements:** 3  
**Resolved:** 4+

---

## 🔍 How to Report New Issues

If you discover a new issue:

1. **Check if it's already listed above**
2. **Gather information:**
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Error messages
   - Environment (OS, Python version, etc.)

3. **Report via:**
   - GitHub Issues
   - Email: walvekarn@gmail.com
   - Include "[BUG]" in subject line

4. **Provide:**
   - Screenshots if applicable
   - Log files (backend.log)
   - Browser console output (F12)

---

## 🛠️ Workaround Guide

### General Troubleshooting Steps

1. **Clear browser cache and reload**
   ```bash
   # Chrome/Edge: Ctrl+Shift+R
   # Safari: Cmd+Shift+R
   ```

2. **Restart backend and dashboard**
   ```bash
   # Stop both (Ctrl+C)
   # Restart backend
   uvicorn main:app --port 8000
   # Restart dashboard
   streamlit run dashboard/Home.py
   ```

3. **Reinitialize database**
   ```bash
   rm compliance.db
   python scripts/setup_database.py
   ```

4. **Check logs**
   ```bash
   tail -f backend.log
   ```

5. **Verify environment**
   ```bash
   python3 scripts/verify_setup.py
   ```

---

## 📅 Fix Schedule

### Version 1.0.1 (Patch) - Target: December 2025
- [ ] Fix DateTime timezone issue (#1)
- [ ] Add .streamlit/config.toml (#2)
- [ ] Minor bug fixes

### Version 1.1.0 (Minor) - Target: Q1 2025
- [ ] Environment variable for API endpoint (#3)
- [ ] PostgreSQL support (Enhancement #1)
- [ ] Export formats (Enhancement #3)
- [ ] Performance optimizations

### Version 1.2.0 (Minor) - Target: Q2 2025
- [ ] Async chat responses (Enhancement #2)
- [ ] Advanced analytics
- [ ] Multi-language support

---

## 🔐 Security Issues

**Reporting Security Issues:**

If you discover a security vulnerability, please **DO NOT** open a public issue.

**Instead:**
1. Email: walvekarn@gmail.com with "[SECURITY]" in subject
2. Include detailed description
3. Allow 48 hours for response
4. Coordinate responsible disclosure

**Known Security Considerations:**
- Demo password (`demo123`) is intentionally weak for portfolio purposes
- API key in `.env` must be protected (add to `.gitignore`)
- SQLite database is not encrypted
- No rate limiting implemented (v1.0.0)

**Production Hardening Required:**
- Change default password
- Implement JWT authentication
- Add rate limiting
- Use HTTPS
- Encrypt database
- Add input sanitization
- Implement RBAC

---

## 📝 Issue Template

When reporting issues, use this template:

```markdown
### Issue Title
Brief description of the problem

**Component:** Which file/module
**Severity:** Critical | Medium | Low
**Status:** New

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Error Messages:**
```
Paste error messages here
```

**Environment:**
- OS: macOS 13.x / Windows 11 / Ubuntu 22.04
- Python: 3.11.7
- Browser: Chrome 120.x
- Backend running: Yes/No

**Screenshots:**
[Attach if helpful]

**Additional Context:**
Any other relevant information
```

---

## 🎯 Testing Before Reporting

Before reporting an issue, please:

1. Run through TESTING_CHECKLIST.md
2. Check this file for known issues
3. Try the workarounds listed
4. Verify it's reproducible
5. Gather all diagnostic information

This helps us fix issues faster! 🚀

---

**Last Updated:** November 13, 2025  
**Version:** 1.0.0  
**Maintainer:** Nikita Walvekar  
**Status:** Actively Maintained

