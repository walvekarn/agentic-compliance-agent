# 🚀 Agentic Engine Upgrade Plan
## Guided Mode - Level 2 Autonomy

**Date:** November 2025  
**Goal:** Reach 9/10 system completeness for Agentic Engine  
**Mode:** Guided (ask before major changes)

---

## 📊 CURRENT STATE ANALYSIS

### Flow Mapping
```
User Request → API (/api/v1/agentic/analyze)
    ↓
AgenticAIOrchestrator.run()
    ↓
1. plan() → LLM call (minimal prompt)
    ↓
2. execute_step() → LLM call (minimal prompt, NO TOOLS CALLED)
    ↓
3. reflect() → LLM call (minimal prompt)
    ↓
4. transform_orchestrator_result() → API response
    ↓
UI (5_Agentic_Analysis.py) → Display results
```

### Critical Issues Identified

#### 🔴 CRITICAL-1: Tools Never Called
- **Location:** `orchestrator.py:293` - `"tools_used": []` hardcoded
- **Impact:** Tools defined but 0% integration
- **Files:** All 4 tools exist but unused

#### 🔴 CRITICAL-2: Prompts Are 1-Line Templates
- **Location:** `reasoning/prompts/*.txt` - Only 1 line each
- **Impact:** LLM must infer everything, inconsistent quality
- **Files:** planner_prompt.txt, executor_prompt.txt, reflection_prompt.txt

#### 🔴 CRITICAL-3: No Reflection → Retry Loop
- **Location:** `orchestrator.py:486-508` - Reflection computed but `requires_retry` ignored
- **Impact:** Quality feedback not acted upon

#### 🔴 CRITICAL-4: No Error Recovery
- **Location:** `orchestrator.py:300-310` - Errors return failure, no retry
- **Impact:** Failures stop execution

#### 🟠 HIGH-1: API → UI Data Mismatches
- **Location:** `agentic_routes.py:235` vs `5_Agentic_Analysis.py:422`
- **Impact:** Reflection scores converted to boolean, losing granularity
- **Missing:** Findings and risks not displayed in UI

#### 🟠 HIGH-2: Step Output Structure Inconsistent
- **Location:** `orchestrator.py:289` - Sometimes dict, sometimes string
- **Impact:** Transformation and UI display issues

---

## 🎯 UPGRADE PLAN

### PHASE 1: Tool Integration (P0 - Critical)

#### File: `src/agentic_engine/orchestrator.py`

**Changes:**
1. **Initialize tools in `__init__`** (lines 25-63)
   ```python
   # Add after line 51 (after memory_store initialization)
   from backend.agentic_engine.tools.entity_tool import EntityTool
   from backend.agentic_engine.tools.calendar_tool import CalendarTool
   from backend.agentic_engine.tools.http_tool import HTTPTool
   from backend.agentic_engine.tools.task_tool import TaskTool
   
   # Initialize tools
   self.tools = {
       "entity_tool": EntityTool(db_session=db_session) if db_session else None,
       "calendar_tool": CalendarTool(),
       "http_tool": HTTPTool(),
       "task_tool": TaskTool()
   }
   ```

2. **Add tool identification method** (after `_load_prompts`, before `plan`)
   ```python
   def _identify_required_tools(self, step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[str]:
       """Identify which tools this step might need"""
       tools = []
       desc_lower = step.get("description", "").lower()
       
       # Check step description for tool keywords
       if any(word in desc_lower for word in ["entity", "organization", "company", "organization"]):
           tools.append("entity_tool")
       if any(word in desc_lower for word in ["deadline", "calendar", "date", "time", "urgency"]):
           tools.append("calendar_tool")
       if any(word in desc_lower for word in ["task", "risk", "compliance", "regulation"]):
           tools.append("task_tool")
       if any(word in desc_lower for word in ["http", "api", "external", "fetch", "retrieve"]):
           tools.append("http_tool")
       
       # Also check if step explicitly mentions tools
       if "tools" in step:
           tools.extend(step.get("tools", []))
       
       return list(set(tools))  # Remove duplicates
   ```

3. **Add tool execution method** (after `_identify_required_tools`)
   ```python
   def _execute_tools(self, tool_names: List[str], step: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
       """Execute tools and gather results"""
       tool_results = {}
       tools_used = []
       
       for tool_name in tool_names:
           tool = self.tools.get(tool_name)
           if not tool:
               continue
           
           try:
               # Extract relevant context for each tool
               entity_data = context.get("entity", {}) if context else {}
               task_data = context.get("task", {}) if context else {}
               
               if tool_name == "entity_tool" and entity_data:
                   result = tool.fetch_entity_details(
                       entity_name=entity_data.get("entity_name", ""),
                       entity_type=entity_data.get("entity_type", "PRIVATE_COMPANY"),
                       industry=entity_data.get("industry", "TECHNOLOGY"),
                       employee_count=entity_data.get("employee_count"),
                       annual_revenue=entity_data.get("annual_revenue"),
                       has_personal_data=entity_data.get("has_personal_data", False),
                       is_regulated=entity_data.get("is_regulated", False),
                       previous_violations=entity_data.get("previous_violations", 0),
                       jurisdictions=entity_data.get("locations", [])
                   )
                   tool_results["entity"] = result
                   tools_used.append(tool_name)
               
               elif tool_name == "calendar_tool" and task_data.get("deadline"):
                   result = tool.calculate_deadline(deadline_text=task_data["deadline"])
                   tool_results["calendar"] = result
                   tools_used.append(tool_name)
               
               elif tool_name == "task_tool" and task_data:
                   result = tool.analyze_task_risk(
                       task_description=task_data.get("task_description", ""),
                       task_category=task_data.get("task_category", "DATA_PROTECTION"),
                       priority=task_data.get("priority", "MEDIUM")
                   )
                   tool_results["task"] = result
                   tools_used.append(tool_name)
               
               elif tool_name == "http_tool":
                   # HTTP tool requires explicit URL, skip for now
                   # Could be enhanced to extract URLs from step description
                   pass
           
           except Exception as e:
               print(f"Warning: Tool {tool_name} failed: {e}")
               tool_results[f"{tool_name}_error"] = str(e)
       
       return {
           "tool_results": tool_results,
           "tools_used": tools_used
       }
   ```

4. **Update `execute_step` to use tools** (lines 212-310)
   - Replace hardcoded `"tools_used": []` with actual tool execution
   - Add tool results to executor prompt
   - Include tool context in LLM call

**Impact:** 
- ✅ Tools actually called during execution
- ✅ Tool results available to LLM
- ✅ `tools_used` populated correctly

**Estimated Lines Changed:** ~150 lines

---

### PHASE 2: Prompt Rewrites (P0 - Critical)

#### File: `src/agentic_engine/reasoning/prompts/planner_prompt.txt`

**Replace entire content with:**
```txt
You are an expert compliance analyst creating a strategic execution plan.

TASK: Break down the compliance task into 3-7 actionable steps that follow the path an expert compliance analyst would take.

AVAILABLE TOOLS:
- entity_tool: Analyze entity characteristics, risk profile, capability assessment, historical violations
- task_tool: Assess task-specific risks, categorize compliance requirements, evaluate regulatory filings
- calendar_tool: Calculate deadlines, urgency scores, time-sensitive compliance windows
- http_tool: Fetch external regulatory information, official guidance, API data

PLANNING GUIDELINES:
1. START: Requirements Analysis (What regulations apply? What are the constraints?)
2. GATHER: Context Collection (Entity profile, historical data, similar cases)
3. ANALYZE: Risk Assessment (Regulatory risks, compliance gaps, impact analysis)
4. EVALUATE: Resource & Timing (Deadline urgency, required capabilities)
5. RECOMMEND: Action Planning (Specific recommendations, implementation steps)

DOMAIN EXPERTISE:
- Compliance frameworks: GDPR, HIPAA, SOX, CCPA, PIPEDA, etc.
- Risk factors: Jurisdiction complexity, data sensitivity, regulatory oversight, impact severity
- Task types: Data privacy, regulatory filing, security audit, incident response, policy review

OUTPUT FORMAT (JSON array):
[
  {
    "step_id": "step_1",
    "description": "Clear, specific action (e.g., 'Identify GDPR Article 30 requirements for EU operations')",
    "rationale": "Why this step is critical for compliance",
    "expected_outcome": "What concrete result should emerge",
    "tools": ["entity_tool", "task_tool"]  // Optional: which tools might help
  },
  ...
]

QUALITY STANDARDS:
- Steps should be specific, not generic
- Each step should have clear regulatory or compliance focus
- Steps should build on each other logically
- Tools should be appropriately suggested
- Expected outcomes should be measurable

EXAMPLE GOOD PLAN:
Entity: TechCorp (EU operations, handles PII)
Task: Implement GDPR Article 30 records

Step 1: Identify GDPR Article 30 requirements → Use entity_tool + task_tool
Step 2: Assess entity's current data processing activities → Use entity_tool for history
Step 3: Map data flows and identify gaps → Use task_tool for risk analysis
Step 4: Calculate deadline urgency if deadline exists → Use calendar_tool
Step 5: Generate compliance recommendations → Synthesize findings

Respond ONLY with valid JSON array. No explanations.
```

**Impact:** 
- ✅ LLM has compliance domain context
- ✅ Tool awareness in planning
- ✅ Structured output guidance

**Estimated Lines Changed:** 1 → ~80 lines

---

#### File: `src/agentic_engine/reasoning/prompts/executor_prompt.txt`

**Replace entire content with:**
```txt
You are an expert compliance analyst executing a specific compliance analysis step.

YOUR TASK: Perform the step using compliance expertise and available tool results.

AVAILABLE TOOL RESULTS (if provided in context):
- entity: Entity risk profile, capability assessment, historical data
- calendar: Deadline calculations, urgency scores, time-sensitive information
- task: Task-specific risk analysis, categorization, regulatory requirements
- http: External regulatory information, official guidance

EXECUTION APPROACH:
1. Review step description and identify what compliance analysis is needed
2. USE TOOL RESULTS if provided (don't ignore them!)
3. Apply compliance expertise (GDPR, HIPAA, SOX, etc.)
4. Be specific and cite regulations when relevant
5. Identify risks, gaps, and recommendations

COMPLIANCE FOCUS:
- Cite specific regulations (e.g., "GDPR Article 30(1) requires...")
- Assess risks accurately (LOW/MEDIUM/HIGH with reasoning)
- Provide actionable recommendations
- Consider jurisdictional differences
- Identify compliance gaps

OUTPUT FORMAT (JSON):
{
  "output": "Detailed analysis result (2-5 sentences explaining findings)",
  "findings": ["Finding 1: specific insight", "Finding 2: specific insight"],
  "risks": ["Risk 1: specific concern with regulatory reference", "Risk 2: ..."],
  "confidence": 0.85  // 0.0-1.0 based on data quality and certainty
}

QUALITY STANDARDS:
- Output should be specific, not generic
- Findings should be actionable insights
- Risks should cite regulations or standards
- Confidence should reflect uncertainty honestly

EXAMPLE GOOD EXECUTION:
Input: Step to identify GDPR Article 30 requirements
Tool Results: entity_tool shows EU operations, handles PII

Output:
{
  "output": "GDPR Article 30(1) requires maintaining records of processing activities for organizations with 250+ employees or those processing high-risk data. Based on entity_tool results, this entity operates in EU and handles PII, triggering Article 30 requirements.",
  "findings": [
    "Article 30 applies because entity handles personal data in EU jurisdiction",
    "Records must include: processing purposes, data categories, recipients, retention periods"
  ],
  "risks": [
    "Non-compliance risk: Missing Article 30 records could result in €20M or 4% revenue fine",
    "Data subject rights risk: Inability to demonstrate compliance upon request"
  ],
  "confidence": 0.9
}

Respond ONLY with valid JSON. No explanations.
```

**Impact:** 
- ✅ Tool results actually used
- ✅ Compliance expertise guidance
- ✅ Structured output with findings/risks

**Estimated Lines Changed:** 1 → ~70 lines

---

#### File: `src/agentic_engine/reasoning/prompts/reflection_prompt.txt`

**Replace entire content with:**
```txt
You are an expert compliance analyst critically evaluating an AI execution step.

YOUR ROLE: Assess quality, identify issues, suggest improvements, determine if retry is needed.

EVALUATION CRITERIA:

1. CORRECTNESS (0.0-1.0):
   ✓ Factual accuracy of regulatory citations (GDPR Article 30, HIPAA, etc.)
   ✓ Logical soundness of reasoning
   ✓ Accuracy of risk assessments
   ✗ Check for: Factual errors, incorrect regulations, logical flaws

2. COMPLETENESS (0.0-1.0):
   ✓ Does it fully address step requirements?
   ✓ Are all regulatory aspects covered?
   ✓ Is critical information missing?
   ✗ Check for: Partial coverage, missed regulations, incomplete analysis

3. COMPLIANCE RISK AWARENESS (0.0-1.0):
   ✓ Are compliance risks properly identified?
   ✓ Are regulatory requirements correctly interpreted?
   ✓ Are potential violations highlighted?
   ✗ Check for: Missed compliance issues, underestimated risks

4. HALLUCINATION RISK (0.0-1.0):
   ✓ Are regulatory citations verifiable?
   ✓ Is information plausible and consistent?
   ✓ No fabricated regulations or impossible scenarios?
   ✗ Check for: Made-up regulations, inconsistent data, implausible claims

5. ACTIONABILITY (0.0-1.0):
   ✓ Recommendations are specific and implementable?
   ✓ Next steps are clearly defined?
   ✓ Entity can actually execute suggestions?
   ✗ Check for: Vague guidance, unrealistic suggestions

OUTPUT FORMAT (JSON):
{
  "correctness_score": 0.85,  // 0.0-1.0
  "completeness_score": 0.80,  // 0.0-1.0
  "overall_quality": 0.82,  // Weighted average: (correctness * 0.4 + completeness * 0.3 + risk_awareness * 0.2 + actionability * 0.1)
  "confidence_score": 0.88,  // Your confidence in this evaluation (0.0-1.0)
  "issues": [
    "Issue 1: Specific problem identified",
    "Issue 2: Another specific issue"
  ],
  "suggestions": [
    "Suggestion 1: Specific improvement",
    "Suggestion 2: Another improvement"
  ],
  "requires_retry": false,  // true if overall_quality < 0.60 or critical issues found
  "missing_data": [
    "Missing item 1: What information is needed",
    "Missing item 2: Another gap"
  ]
}

QUALITY THRESHOLDS:
- overall_quality >= 0.85: ✅ Excellent, no retry needed
- overall_quality >= 0.70: ✅ Good, minor improvements suggested
- overall_quality >= 0.50: ⚠️ Fair, consider retry with improvements
- overall_quality < 0.50: ❌ Poor, requires_retry = true

BE SPECIFIC:
- ❌ Bad: "Output is incomplete"
- ✅ Good: "Output lacks Article 30 retention period requirements (Article 30(1)(f))"

- ❌ Bad: "Some risks missing"
- ✅ Good: "Missing risk: Article 30 violations can trigger GDPR Article 83 fines up to €20M"

Respond ONLY with valid JSON. No explanations.
```

**Impact:** 
- ✅ Structured evaluation criteria
- ✅ Compliance-specific considerations
- ✅ Clear retry thresholds

**Estimated Lines Changed:** 1 → ~90 lines

---

### PHASE 3: Reflection → Retry Loop (P0 - Critical)

#### File: `src/agentic_engine/orchestrator.py`

**Update `run` method** (lines 422-546)

**Add after line 487 (after reflection is computed):**
```python
# Check if retry is needed based on reflection
if reflection.get("requires_retry", False) and iteration < max_iterations:
    print(f"Step {step_idx + 1} requires retry based on reflection (quality: {reflection.get('overall_quality', 0.0):.2f})")
    
    # Improve step based on reflection suggestions
    improved_step = self._improve_step_from_reflection(step, reflection)
    
    # Re-execute with improved step
    execution_result = self.execute_step(improved_step, context)
    self.execution_state["step_outputs"][-1] = execution_result  # Replace previous result
    
    # Re-reflect on improved execution
    reflection = self.reflect(improved_step, execution_result)
    self.execution_state["reflections"][-1] = reflection  # Replace previous reflection
    
    print(f"Step {step_idx + 1} retry completed. New quality: {reflection.get('overall_quality', 0.0):.2f}")
```

**Add new method `_improve_step_from_reflection`** (after `reflect` method):
```python
def _improve_step_from_reflection(
    self, 
    step: Dict[str, Any], 
    reflection: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Improve a step based on reflection feedback.
    
    Args:
        step: Original step
        reflection: Reflection containing suggestions and issues
        
    Returns:
        Improved step with enhanced description
    """
    improved_step = step.copy()
    
    # Add suggestions to step description
    suggestions = reflection.get("suggestions", [])
    issues = reflection.get("issues", [])
    missing_data = reflection.get("missing_data", [])
    
    if suggestions or issues or missing_data:
        improvement_note = "\n\nIMPROVEMENTS NEEDED:\n"
        if issues:
            improvement_note += f"Issues to address: {', '.join(issues[:3])}\n"
        if suggestions:
            improvement_note += f"Suggestions: {', '.join(suggestions[:3])}\n"
        if missing_data:
            improvement_note += f"Missing data: {', '.join(missing_data[:3])}\n"
        
        improved_step["description"] = step.get("description", "") + improvement_note
        improved_step["retry_count"] = step.get("retry_count", 0) + 1
    
    return improved_step
```

**Impact:** 
- ✅ Reflection feedback actually used
- ✅ Steps improved and re-executed when needed
- ✅ Quality improvement loop

**Estimated Lines Changed:** ~50 lines

---

### PHASE 4: Error Recovery & Retries (P0 - Critical)

#### File: `src/agentic_engine/orchestrator.py`

**Update `execute_step` method** (lines 212-310)

**Replace error handling** (lines 300-310):
```python
except Exception as e:
    error_msg = str(e)
    print(f"Error executing step {step.get('step_id')}: {error_msg}")
    
    # Check if we should retry
    retry_count = step.get("retry_count", 0)
    max_retries = 2
    
    if retry_count < max_retries:
        print(f"Retrying step {step.get('step_id')} (attempt {retry_count + 1}/{max_retries})...")
        
        # Add error context to step for retry
        retry_step = step.copy()
        retry_step["retry_count"] = retry_count + 1
        retry_step["previous_error"] = error_msg
        
        # Adjust prompt to include error context
        retry_step["description"] = (
            step.get("description", "") + 
            f"\n\nNOTE: Previous attempt failed with error: {error_msg}. "
            "Please try again with more detail and error handling."
        )
        
        # Recursive retry
        return self.execute_step(retry_step, plan_context, retry_count=retry_count + 1)
    
    # Max retries reached
    return {
        "step_id": step.get("step_id"),
        "status": "failure",
        "output": None,
        "error": error_msg,
        "confidence": 0.0,
        "tools_used": [],
        "errors": [error_msg],
        "retry_count": retry_count
    }
```

**Impact:** 
- ✅ Automatic retry on errors
- ✅ Error context included in retry
- ✅ Graceful degradation after max retries

**Estimated Lines Changed:** ~30 lines

---

### PHASE 5: Standardize Step Output Structure (P1 - High)

#### File: `src/agentic_engine/orchestrator.py`

**Update `execute_step` method** (lines 284-295)

**Replace executor_fn result** (lines 285-295):
```python
def executor_fn(step_data, context):
    # Ensure consistent structure
    output_text = execution_data.get("output", "Step executed")
    if isinstance(output_text, dict):
        output_text = json.dumps(output_text, indent=2)
    elif not isinstance(output_text, str):
        output_text = str(output_text)
    
    return {
        "step_id": step_data.get("step_id"),
        "status": "success",
        "output": output_text,  # Always string
        "findings": execution_data.get("findings", []),  # Always list
        "risks": execution_data.get("risks", []),  # Always list
        "confidence": float(execution_data.get("confidence", 0.7)),
        "tools_used": tool_execution_result.get("tools_used", []),  # From tool execution
        "errors": [],
        "metrics": {
            "execution_time": 0.0,  # Will be set by agent_loop
            "timestamp": datetime.utcnow().isoformat()
        }
    }
```

**Also update executor prompt construction** (lines 243-260) to include tool results:
```python
# Get tool results
tool_names = self._identify_required_tools(step, plan_context)
tool_execution_result = self._execute_tools(tool_names, step, plan_context)

# Build tool context string
tool_context_str = ""
if tool_execution_result.get("tool_results"):
    tool_context_str = f"\n\nAvailable Tool Results:\n{json.dumps(tool_execution_result['tool_results'], indent=2)}"

full_prompt = f"""{executor_prompt}

Step to Execute:
{step_description}

Rationale:
{step_rationale}{context_str}{tool_context_str}

Previous Steps Completed:
{self._summarize_previous_steps(self.execution_state['step_outputs'])}

Please execute this step and provide:
1. The main output/result
2. Any key findings or insights
3. Any risks or concerns identified
4. Confidence in the execution (0.0 to 1.0)

Respond in JSON format with keys: output, findings, risks, confidence"""
```

**Add `_summarize_previous_steps` method** (after `_execute_tools`):
```python
def _summarize_previous_steps(self, step_outputs: List[Dict]) -> str:
    """Summarize previous steps for context"""
    if not step_outputs:
        return "No previous steps completed."
    
    summary = "Previous steps completed:\n"
    # Only include last 3 steps to avoid prompt bloat
    for i, output in enumerate(step_outputs[-3:], 1):
        step_id = output.get('step_id', f'step_{i}')
        output_text = output.get('output', '')[:200]  # Truncate
        summary += f"\n{i}. {step_id}: {output_text}...\n"
        if output.get('findings'):
            summary += f"   Key findings: {', '.join(output['findings'][:2])}\n"
    
    return summary
```

**Impact:** 
- ✅ Consistent output structure
- ✅ Tool results in prompt
- ✅ Better context management

**Estimated Lines Changed:** ~80 lines

---

### PHASE 6: Fix API → UI Alignment (P1 - High)

#### File: `src/api/agentic_routes.py`

**Update `transform_orchestrator_result`** (lines 209-218)

**Enhance StepOutput transformation:**
```python
# Transform step_outputs
transformed_step_outputs = []
for output in result.get("step_outputs", []):
    transformed_step_outputs.append(StepOutput(
        step_id=output.get("step_id", "unknown"),
        status=output.get("status", "unknown"),
        output=str(output.get("output", "")),
        tools_used=output.get("tools_used", []),
        metrics={
            **output.get("metrics", {}),
            "findings": output.get("findings", []),  # Add findings
            "risks": output.get("risks", []),  # Add risks
            "confidence": output.get("confidence", 0.7)  # Add confidence
        }
    ))
```

**Update Reflection transformation** (lines 233-241) to keep scores:
```python
transformed_reflections.append(Reflection(
    step_id=step_id,
    quality_score=reflection.get("overall_quality", 0.7),
    correctness=reflection.get("correctness_score", 0.7) > 0.7,  # Boolean for display
    correctness_score=reflection.get("correctness_score", 0.7),  # Keep score
    completeness=reflection.get("completeness_score", 0.7) > 0.7,
    completeness_score=reflection.get("completeness_score", 0.7),  # Keep score
    confidence=reflection.get("confidence_score", 0.7),
    issues=reflection.get("issues", []),
    suggestions=reflection.get("suggestions", [])
))
```

**Note:** This requires updating the `Reflection` model to include optional score fields.

**Impact:** 
- ✅ Findings and risks available in API response
- ✅ Both boolean and score values for UI flexibility

**Estimated Lines Changed:** ~20 lines

---

#### File: `src/api/agentic_routes.py`

**Update Reflection model** (lines 102-111):
```python
class Reflection(BaseModel):
    """Reflection on step execution"""
    step_id: str
    quality_score: float
    correctness: bool
    correctness_score: Optional[float] = None  # Add score field
    completeness: bool
    completeness_score: Optional[float] = None  # Add score field
    confidence: float
    issues: List[str]
    suggestions: List[str]
```

**Update StepOutput model** (lines 93-100):
```python
class StepOutput(BaseModel):
    """Output from a single step execution"""
    step_id: str
    status: str
    output: str
    tools_used: List[str]
    metrics: Dict[str, Any]  # Now includes findings, risks, confidence
```

**Impact:** 
- ✅ Models support new fields
- ✅ Backward compatible (Optional fields)

**Estimated Lines Changed:** ~10 lines

---

### PHASE 7: Update UI Display (P1 - High)

#### File: `dashboard/pages/5_Agentic_Analysis.py`

**Update Step Outputs tab** (lines 389-409)

**Replace step output display:**
```python
with st.expander(f"{status_icon} {step_id.replace('_', ' ').title()}", expanded=False):
    st.markdown(f"**Status:** `{status}`")
    
    st.markdown(f"**Output:**")
    st.text(output.get("output", "No output"))
    
    # Display findings
    findings = output.get("metrics", {}).get("findings", [])
    if findings:
        st.markdown(f"**🔍 Key Findings:**")
        for finding in findings:
            st.markdown(f"- {finding}")
    
    # Display risks
    risks = output.get("metrics", {}).get("risks", [])
    if risks:
        st.markdown(f"**⚠️ Risks Identified:**")
        for risk in risks:
            st.markdown(f"- {risk}")
    
    # Display confidence
    confidence = output.get("metrics", {}).get("confidence", 0.0)
    if confidence:
        st.metric("Confidence", f"{confidence:.2%}")
    
    tools_used = output.get("tools_used", [])
    if tools_used:
        st.markdown(f"**🔧 Tools Used:** {', '.join(tools_used)}")
    
    metrics = output.get("metrics", {})
    if metrics:
        st.markdown(f"**📊 Metrics:**")
        st.json({k: v for k, v in metrics.items() if k not in ["findings", "risks", "confidence"]})
```

**Update Reflections tab** (lines 439-445) to show scores:
```python
col1, col2, col3, col4 = st.columns(4)
with col1:
    correctness_score = reflection.get("correctness_score", None)
    if correctness_score is not None:
        st.metric("Correctness", f"{correctness_score:.2%}", 
                 "✅" if reflection.get("correctness") else "❌")
    else:
        st.metric("Correctness", "✅" if reflection.get("correctness") else "❌")
with col2:
    completeness_score = reflection.get("completeness_score", None)
    if completeness_score is not None:
        st.metric("Completeness", f"{completeness_score:.2%}",
                 "✅" if reflection.get("completeness") else "❌")
    else:
        st.metric("Completeness", "✅" if reflection.get("completeness") else "❌")
with col3:
    st.metric("Confidence", f"{reflection.get('confidence', 0.0):.2%}")
with col4:
    st.metric("Quality Score", f"{reflection.get('quality_score', 0.0):.2%}")
```

**Impact:** 
- ✅ Findings and risks visible
- ✅ Detailed scores displayed
- ✅ Better user experience

**Estimated Lines Changed:** ~40 lines

---

### PHASE 8: Update API Status Endpoint (P2 - Medium)

#### File: `src/api/agentic_routes.py`

**Update status endpoint** (lines 346-363):
```python
return {
    "status": "experimental",
    "version": "1.0.0",  # Updated from 0.1.0
    "phase": "PHASE 2 Complete - PHASE 3 Pending",  # Updated
    "orchestrator_implemented": True,
    "agent_loop_implemented": True,
    "reasoning_engine_implemented": True,
    "tools_implemented": True,
    "tools_integrated": True,  # NEW: Indicates tools are actually called
    "memory_implemented": False,
    "integration_complete": True,  # Updated from False
    "next_steps": [
        "PHASE 3: Implement memory systems (EpisodicMemory, SemanticMemory)",
        "PHASE 3: Add database persistence for memory",
        "PHASE 3: Integrate ScoreAssistant",
        "Enhance tool auto-integration intelligence"
    ],
    "message": "PHASE 2 complete (Implementation + Integration). PHASE 3 (Memory + Scoring) pending."
}
```

**Impact:** 
- ✅ Accurate status information
- ✅ Reflects actual completion state

**Estimated Lines Changed:** ~15 lines

---

## 📋 SUMMARY

### Files to Modify

1. **`src/agentic_engine/orchestrator.py`** (~400 lines changed)
   - Tool initialization
   - Tool identification and execution
   - Reflection retry loop
   - Error recovery
   - Step output standardization
   - Context summarization

2. **`src/agentic_engine/reasoning/prompts/planner_prompt.txt`** (1 → ~80 lines)
   - Complete rewrite with compliance expertise

3. **`src/agentic_engine/reasoning/prompts/executor_prompt.txt`** (1 → ~70 lines)
   - Complete rewrite with tool guidance

4. **`src/agentic_engine/reasoning/prompts/reflection_prompt.txt`** (1 → ~90 lines)
   - Complete rewrite with structured evaluation

5. **`src/api/agentic_routes.py`** (~45 lines changed)
   - Update transformation logic
   - Update models
   - Update status endpoint

6. **`dashboard/pages/5_Agentic_Analysis.py`** (~40 lines changed)
   - Display findings and risks
   - Show detailed scores

### Total Estimated Changes
- **Lines Added:** ~600 lines
- **Lines Modified:** ~200 lines
- **Files Changed:** 6 files
- **New Methods:** 4 methods

### Impact Assessment

**Positive Impacts:**
- ✅ Tools actually used (0% → 100% integration)
- ✅ Prompts provide domain expertise (1 line → comprehensive)
- ✅ Reflection drives improvement (feedback loop active)
- ✅ Error recovery prevents failures
- ✅ UI shows complete information
- ✅ Consistent data structures

**Risks:**
- ⚠️ Tool execution may add latency (mitigated by async/parallel execution potential)
- ⚠️ More LLM calls for retries (mitigated by quality thresholds)
- ⚠️ Prompt size increase (mitigated by summarization)

**Compatibility:**
- ✅ Backward compatible (Optional fields, graceful degradation)
- ✅ No breaking API changes
- ✅ UI enhancements are additive

---

## ✅ SAFETY CONFIRMATION

**Before proceeding, please confirm:**

1. ✅ **Tool Integration:** Proceed with integrating all 4 tools into execution?
2. ✅ **Prompt Rewrites:** Replace minimal prompts with comprehensive versions?
3. ✅ **Reflection Retry:** Implement retry loop based on reflection feedback?
4. ✅ **Error Recovery:** Add automatic retry on execution errors?
5. ✅ **UI Updates:** Display findings, risks, and detailed scores?
6. ✅ **API Updates:** Update status endpoint and response models?

**Proceed with implementation?** (Yes/No)

---

**Plan Generated:** November 2025  
**Next Step:** Await user approval before implementation

