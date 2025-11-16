# Atlas Revalidation Plan

## Overview

This document outlines the plan for revalidating the system using Atlas after Phase 2 fixes.

## Pre-Validation Checklist

### ✅ Completed Fixes

#### UX Fixes
- [x] Date picker always renders (never disabled)
- [x] Date picker keyboard accessible
- [x] Validation errors clear on successful submit
- [x] Multiselect has "Select All" option
- [x] Multiselect "No results" bug fixed
- [x] Tooltips added for all jargon terms
- [x] ARIA labels added to all interactive elements

#### Data Integrity Fixes
- [x] Task count mismatch clarified
- [x] Timestamps added to responses
- [x] AI Accuracy display fixed
- [x] Pagination total_count fixed

#### Regression Testing
- [x] Regression test page created
- [x] All endpoints tested
- [x] All UI components tested

### 🔍 Pre-Atlas Verification Steps

1. **Run Local Regression Tests**
   ```bash
   # Navigate to http://localhost:8501/debug/regression
   # Click "Run Endpoint Tests"
   # Verify all tests pass
   ```

2. **Manual Testing**
   - [ ] Test date picker with keyboard
   - [ ] Test multiselect "Select All"
   - [ ] Test validation error clearing
   - [ ] Test all tooltips
   - [ ] Verify task count explanations
   - [ ] Verify all agentic pages use `parseAgenticResponse()` and display timestamps on success

3. **Check Logs**
   ```bash
   # Check backend logs for errors
   tail -f backend.log
   
   # Check for any [ERROR] messages
   grep -i "error" backend.log
   ```

## Atlas Validation Steps

### 1. Initial Atlas Run

Run Atlas audit on the updated application:
```bash
# Run Atlas (follow your Atlas setup instructions)
atlas audit
```

### 2. Verify Fixed Issues

#### Date Picker (Atlas Issue A)
- **Expected**: Date picker always visible, never disabled
- **Verify**: Check that checkbox toggles date field requirement, but field remains accessible
- **Acceptance Criteria**: Date picker works with mouse and keyboard

#### Validation Errors (Atlas Issue B)
- **Expected**: Errors clear when form corrected and submitted
- **Verify**: Submit invalid form → see errors → correct form → submit → errors disappear
- **Acceptance Criteria**: No persistent error banners after successful submit

#### Multiselect (Atlas Issue C)
- **Expected**: "Select All" button, no "No results" message
- **Verify**: Open multiselect → see "Select All" button → click it → all items selected
- **Acceptance Criteria**: All items selectable, no "No results" message

#### Tooltips (Atlas Issue E)
- **Expected**: Tooltips for Agentic, Escalation Rate, High-Complex Risk, Risk Level
- **Verify**: Hover over terms with ℹ️ icon → tooltip appears
- **Acceptance Criteria**: All specified terms have tooltips

#### ARIA Labels (Atlas Issue F)
- **Expected**: All interactive elements have ARIA labels
- **Verify**: Use screen reader or dev tools → check ARIA attributes
- **Acceptance Criteria**: All buttons, dropdowns, checkboxes, inputs have labels

### 3. Data Integrity Verification

#### Task Count Mismatch (Atlas Issue 2A)
- **Expected**: Clear explanation of difference between Calendar and Home
- **Verify**: 
  - Calendar shows "high-priority" with explanation (days + risk)
  - Home shows "high-risk" with clarification (risk only)
  - Both include timestamps
- **Acceptance Criteria**: Difference clearly explained, no user confusion

#### AI Accuracy (Atlas Issue 2B)
- **Expected**: Shows "N/A" when no feedback, or accurate percentage with explanation
- **Verify**: Check Agent Insights page → see accuracy metric → hover for tooltip
- **Acceptance Criteria**: Formula explained, shows N/A when appropriate

### 4. Regression Testing

Run regression tests via UI:
1. Navigate to `/debug/regression`
2. Run all endpoint tests
3. Verify all pass
4. Test UI components
5. Verify pagination

### 5. Edge Cases

Test edge cases that Atlas might flag:
- [ ] Empty multiselect selection
- [ ] Very long task descriptions
- [ ] Deadline in the past (should be prevented by min_value)
- [ ] All locations selected vs none selected
- [ ] Form submission with network timeout
- [ ] Endpoint timeout (120s)

## Expected Atlas Results

### Should Pass ✅
- Date picker accessibility
- Validation error clearing
- Multiselect functionality
- Tooltip presence
- ARIA label presence
- Data consistency explanations
- AI Accuracy display

### Should Note ⚠️
- Task count difference (intentional, explained)
- Timeout handling (expected for long-running operations)
- OpenAI API dependency (external service)

### Should Not Find ❌
- Disabled date pickers
- Persistent validation errors
- "No results" in multiselects
- Missing tooltips
- Missing ARIA labels
- Data count mismatches without explanation
- AI Accuracy = 0% without explanation

## Post-Atlas Actions

### If All Issues Resolved ✅

1. **Document Results**
   - Update this file with Atlas results
   - Mark issues as resolved
   - Update PRODUCTION_READINESS.md

2. **Deploy to Production**
   - Follow deployment checklist
   - Monitor logs
   - Test critical paths

3. **Monitor**
   - Watch for user feedback
   - Monitor error logs
   - Track performance metrics

### If Issues Remain ❌

1. **Document Issues**
   - List remaining issues
   - Prioritize by severity
   - Assign fix estimates

2. **Fix Issues**
   - Create tickets for each issue
   - Implement fixes
   - Re-test locally

3. **Re-run Atlas**
   - Run Atlas again after fixes
   - Verify all issues resolved

## Acceptance Criteria

✅ **Atlas Passes** when:
- All Phase 2 fixes verified
- No critical UX issues found
- No data integrity issues found
- All accessibility improvements verified
- Regression tests pass

## Timeline

- **Pre-Atlas Verification**: 1 hour
- **Atlas Run**: 30 minutes
- **Issue Review**: 30 minutes
- **Fix Implementation** (if needed): Variable
- **Re-validation** (if needed): 30 minutes

## Success Metrics

- **Atlas Score**: Should be ≥ previous score + improvement
- **Critical Issues**: 0
- **Warnings**: ≤ 2 (acceptable: task count difference, timeout handling)
- **Regression Tests**: 100% pass rate
- **Manual Tests**: 100% pass rate

---

**Status**: Ready for Atlas Revalidation
**Last Updated**: 2024-01-XX
**Version**: 1.3.0-agentic-hardened
