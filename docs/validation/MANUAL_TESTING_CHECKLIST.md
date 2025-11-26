# Manual Testing Checklist

**Date:** November 2025  
**Purpose:** Verify all fixes are working correctly after syntax error corrections

---

## ✅ Step 1: Verify Backend Starts

### Check 1.1: Test Backend Import
```bash
python3 -c "from backend.api.agentic_routes import router; print('✅ Backend imports successfully!')"
```

**Expected:** `✅ Backend imports successfully!`  
**If Error:** Check import errors

---

### Check 1.2: Start Backend
```bash
make backend
```

**Expected:**
- ✅ No import errors
- ✅ Server starts on port 8000
- ✅ You see: `INFO:     Uvicorn running on http://0.0.0.0:8000`

**Wait for:** Backend to fully start (2-3 seconds)

---

### Check 1.3: Test Health Endpoint
Open a new terminal and run:
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status":"healthy","version":"2.0"}
```

**If Error:** Backend not running or port conflict

---

## ✅ Step 2: Verify Frontend Starts

### Check 2.1: Test Frontend Syntax
```bash
cd frontend/pages
python3 -m py_compile 3_Audit_Trail.py 4_Agent_Insights.py 7_Agentic_Test_Suite.py 8_Error_Recovery_Simulator.py 10_Deployment_Readiness.py
```

**Expected:** No errors (exit code 0)

**If Error:** Syntax error still exists

---

### Check 2.2: Start Frontend
```bash
make dashboard
```
(Or in separate terminal: `cd frontend && python3 -m streamlit run Home.py --server.port=8501`)

**Expected:**
- ✅ No syntax errors
- ✅ Streamlit starts
- ✅ You see: `You can now view your Streamlit app in your browser. Local URL: http://localhost:8501`

**Wait for:** Streamlit to fully load (5-10 seconds)

---

## ✅ Step 3: Manual UI Testing

### Test 3.1: Home Page ✅

**Navigate to:** http://localhost:8501

**Check:**
- [ yes] Page loads without errors
- [yes ] Login page appears
- [yes ] Can enter credentials (demo / demo123)
- [yes ] Can click "Login"
- [yes ] Home page displays after login
- [yes ] No error messages in console (F12)

**If Error:** Check browser console (F12) for JavaScript errors

---

### Test 3.2: Analyze Task Page ✅

**Navigate to:** Pages → Analyze Task (or http://localhost:8501/1_Analyze_Task)

**Check:**
- [yes ] Page loads without errors
- [yes ] Form displays correctly
- [ ] All fields visible and editable
- [ ] Can click "Load Example" button
- [ ] Form populates with example data
- [ ] Can submit form
- [ ] Results display after submission
- [ ] No syntax errors in terminal

**If Error:** Check Streamlit terminal for errors

---

### Test 3.3: Audit Trail Page ✅

**Navigate to:** Pages → Audit Trail (or http://localhost:8501/3_Audit_Trail)

**Check:**
- [ ] Page loads without errors
- [ ] No "SyntaxError" messages
- [ ] Filters display correctly
- [ ] Search box works
- [ ] Can select date range
- [ ] Can select risk levels
- [ ] Table displays (or empty state message)
- [ ] No errors in browser console (F12)

**Fixed:** Line 273 - Extra `else:` statement removed

---

### Test 3.4: Agent Insights Page ✅

**Navigate to:** Pages → Agent Insights (or http://localhost:8501/4_Agent_Insights)

**Check:**
- [ ] Page loads without errors
- [ ] No "SyntaxError: ':' expected" messages
- [ ] Charts display (if data exists)
- [ ] Empty state message shows if no data
- [ ] No errors in browser console

**Fixed:** Line 272 - Dictionary properly closed with `}`

---

### Test 3.5: Agentic Test Suite Page ✅

**Navigate to:** Pages → Agentic Test Suite (or http://localhost:8501/7_Agentic_Test_Suite)

**Check:**
- [ ] Page loads without errors
- [ ] No "IndentationError" messages
- [ ] "Run Test Suite" button visible
- [ ] Can click button
- [ ] Results display (or loading spinner)
- [ ] No errors in browser console

**Fixed:** Line 299 - Indentation corrected in expander blocks

---

### Test 3.6: Error Recovery Simulator Page ✅

**Navigate to:** Pages → Error Recovery Simulator (or http://localhost:8501/8_Error_Recovery_Simulator)

**Check:**
- [ ] Page loads without errors
- [ ] No "IndentationError: unexpected indent" messages
- [ ] Configuration section displays
- [ ] "Run Simulation" button visible
- [ ] Results section displays (if simulation run)
- [ ] No errors in browser console

**Fixed:** Line 246 - `render_section_header` properly indented

---

### Test 3.7: Deployment Readiness Page ✅

**Navigate to:** Pages → Deployment Readiness (or http://localhost:8501/10_Deployment_Readiness)

**Check:**
- [ ] Page loads without errors
- [ ] No "IndentationError: unexpected indent" messages
- [ ] Health check runs automatically
- [ ] Readiness score displays
- [ ] Component breakdown shows
- [ ] No errors in browser console

**Fixed:** Line 306 - `render_section_header` properly indented

---

### Test 3.8: All Other Pages ✅

**Navigate to each page and verify:**
- [ ] Compliance Calendar loads
- [ ] Agentic Analysis loads
- [ ] Agentic Benchmarks loads
- [ ] All pages accessible from sidebar
- [ ] No errors when switching pages

---

## ✅ Step 4: Functional Testing

### Test 4.1: Form Submission ✅

**On Analyze Task page:**
1. [ ] Fill out form with test data
2. [ ] Click "Get My Answer Now"
3. [ ] Loading spinner appears
4. [ ] Results display
5. [ ] No errors in console

---

### Test 4.2: Navigation ✅

**Test navigation flow:**
1. [ ] Start on Home page
2. [ ] Navigate to Analyze Task
3. [ ] Submit form
4. [ ] Navigate to Audit Trail
5. [ ] Verify entry appears in audit trail
6. [ ] Navigate back to Home
7. [ ] All navigation works smoothly

---

### Test 4.3: Error Handling ✅

**Test error cases:**
1. [ ] Stop backend (`Ctrl+C` in backend terminal)
2. [ ] Try to submit form on Analyze Task
3. [ ] Error message displays
4. [ ] Restart backend
5. [ ] Try again - should work

---

## ✅ Step 5: Console Error Check

### Check 5.1: Browser Console ✅

**In Browser (F12):**
- [ ] Open Developer Tools (F12)
- [ ] Go to Console tab
- [ ] Navigate through all pages
- [ ] Check for red errors
- [ ] Should see no critical errors

**Acceptable:** Warnings about missing data (normal)

---

### Check 5.2: Streamlit Terminal ✅

**In Terminal where Streamlit is running:**
- [ ] Check for Python exceptions
- [ ] Should see no SyntaxErrors
- [ ] Should see no IndentationErrors
- [ ] Should see no ImportErrors

**Acceptable:** API connection errors (if backend down)

---

### Check 5.3: Backend Terminal ✅

**In Terminal where Backend is running:**
- [ ] Check for import errors
- [ ] Should see no ImportError about STANDARD_MODEL
- [ ] Should see server running message
- [ ] Check logs when making API calls

---

## ✅ Step 6: Full System Test

### Test 6.1: Complete Workflow ✅

**End-to-end test:**
1. [ ] Start both services (`make start`)
2. [ ] Login to dashboard
3. [ ] Analyze a task
4. [ ] View results
5. [ ] Check audit trail for entry
6. [ ] View agent insights
7. [ ] All pages work correctly

---

### Test 6.2: Error Recovery ✅

**Test error recovery:**
1. [ ] Stop backend
2. [ ] Try to access pages
3. [ ] Should show error messages (not crash)
4. [ ] Restart backend
5. [ ] All pages work again

---

## ✅ Summary Checklist

### Backend ✅
- [ ] Backend starts without import errors
- [ ] Health endpoint responds
- [ ] No STANDARD_MODEL import errors
- [ ] API endpoints accessible

### Frontend ✅
- [ ] All pages load without syntax errors
- [ ] No IndentationErrors
- [ ] No SyntaxErrors
- [ ] No ImportErrors

### UI Functionality ✅
- [ ] All pages accessible
- [ ] Forms work correctly
- [ ] Navigation works
- [ ] Error messages display properly

---

## 🐛 If You Find Errors

### Backend Errors:
1. **ImportError:** Check if STANDARD_MODEL exists in `backend/utils/llm_client.py`
2. **SyntaxError:** Check file mentioned in error
3. **Connection Error:** Verify backend is running on port 8000

### Frontend Errors:
1. **SyntaxError:** File mentioned in error has syntax issue
2. **IndentationError:** Check indentation in file mentioned
3. **ImportError:** Missing import in frontend file

### UI Errors:
1. **Page won't load:** Check browser console (F12)
2. **Form won't submit:** Check backend is running
3. **Results not showing:** Check API responses in Network tab

---

## ✅ Quick Verification Commands

```bash
# Test backend imports
python3 -c "from backend.api.agentic_routes import router; print('✅ Backend OK')"

# Test frontend syntax
python3 -m py_compile frontend/pages/*.py

# Test backend health
curl http://localhost:8000/health

# Check if services are running
ps aux | grep uvicorn
ps aux | grep streamlit
```

---

**Report any issues you find!** 🎯

