# Reasoning Engine Upgrade Proposal (Level 2 - Guided Autonomy)

## Current State Analysis

### Files to Modify:
1. `src/agentic_engine/reasoning/reasoning_engine.py`
   - `_safe_json_parse()` → Rename to `safe_parse_json()` for consistency
   - Enhance reflection to support multi-round tracking

2. `src/agentic_engine/orchestrator.py`
   - `run()` → Add multi-round reflection loop
   - Add `reasoning_trace` tracking
   - Enhance step retry logic based on reflection scores

3. `src/agentic_engine/agent_loop.py`
   - Enhance `execute_step()` to support reflection-based retries
   - Add reasoning trace support

## Proposed Workflow Changes

### Current Flow:
```
1. Generate Plan
2. For each step:
   a. Execute step
   b. Reflect on step
   c. If requires_retry → retry once
3. Generate final recommendation
```

### New Enhanced Flow:
```
1. Generate Initial Plan → Store in reasoning_trace
2. For each step:
   a. Execute step
   b. Reflect on step → Store in reasoning_trace.reflection_rounds
   c. If step fails OR reflection scores < 0.7:
      → Retry step with improved instructions (max 1 retry per step)
   d. Store execution result
3. After ALL steps complete:
   a. Evaluate overall completeness/correctness
   b. If completeness_score < 0.7 OR correctness_score < 0.7:
      → Regenerate plan (max 2 passes total)
      → Execute revised plan
      → Store in reasoning_trace.revised_plans
4. Generate final recommendation
5. Validate reasoning_trace (not empty, reflections include issues + fixes)
```

## Key Enhancements

### 1. Multi-Round Reflection
- After all steps complete, evaluate overall quality
- If scores < 0.7, regenerate plan and run second pass
- Maximum 2 passes (initial + 1 revision)
- Track all reflection rounds in `reasoning_trace`

### 2. Step Improvement Loop
- If step execution fails OR reflection scores < 0.7:
  - Retry once with modified instruction
  - Log retry in execution_results
  - Include previous error/reflection feedback in retry

### 3. Reasoning Trace Object
```python
reasoning_trace = {
    "initial_plan": [...],  # Original plan
    "reflection_rounds": [  # All reflections across all passes
        {
            "pass_number": 1,
            "step_index": 0,
            "reflection": {...},
            "triggered_retry": False
        },
        ...
    ],
    "revised_plans": [  # Plans generated after reflection
        {
            "pass_number": 2,
            "plan": [...],
            "trigger_reason": "completeness_score < 0.7"
        }
    ],
    "execution_results": [...]  # All step execution results
}
```

### 4. Output Validation
- Ensure `reasoning_trace` is not empty
- Ensure all reflections include `issues` and `suggestions` fields
- Validate scores are in valid range [0.0, 1.0]

## Safety Rules Compliance
✅ No database model changes
✅ No production code override (only enhancements)
✅ Backward compatible (existing code still works)

## Files to Modify

### 1. reasoning_engine.py
- Rename `_safe_json_parse` → `safe_parse_json` (public method)
- No other changes needed (already has good reflection logic)

### 2. orchestrator.py
- Enhance `run()` method with multi-round reflection
- Add `reasoning_trace` initialization and tracking
- Add plan regeneration logic
- Add validation at end

### 3. agent_loop.py
- Minor enhancement to support reflection-based retries
- Add reasoning trace metadata support

## Risk Assessment
- **Low Risk**: Changes are additive, existing functionality preserved
- **Backward Compatible**: All changes extend existing methods
- **Testable**: New logic can be tested independently

