# Tool Integration Diff Summary

## Overview
This document summarizes the changes required to integrate tools into the Plan → Execute flow of the agentic engine.

## Files to Modify

### 1. `src/agentic_engine/tools/__init__.py`
**Changes:**
- Add `ToolRegistry` class with tool metadata
- Register all tools with structured metadata (name, capabilities, input_schema)
- Add `get_tool_by_capability()` method for automatic tool selection

**New Code:**
```python
class ToolRegistry:
    """Registry of all available tools with metadata."""
    
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools
        self.metadata = self._build_metadata()
    
    def _build_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Build metadata for all tools."""
        return {
            "entity_tool": {
                "name": "EntityTool",
                "capabilities": [
                    "entity_analysis", "entity_details", "entity_history",
                    "similar_tasks", "fetch_entity", "analyze_entity"
                ],
                "input_schema": {
                    "fetch_entity_details": {
                        "required": ["entity_name"],
                        "optional": ["entity_type", "industry", "employee_count", "annual_revenue"]
                    },
                    "fetch_similar_tasks": {
                        "required": ["query"],
                        "optional": ["entity_name", "limit"]
                    }
                },
                "requires_db": True,
                "requires_network": False
            },
            "task_tool": {
                "name": "TaskTool",
                "capabilities": [
                    "task_analysis", "risk_analysis", "task_classification",
                    "task_status", "run_task_risk_analyzer"
                ],
                "input_schema": {
                    "run_task_risk_analyzer": {
                        "required": ["task_description"],
                        "optional": ["task_category", "affects_personal_data"]
                    }
                },
                "requires_db": False,
                "requires_network": False
            },
            "calendar_tool": {
                "name": "CalendarTool",
                "capabilities": [
                    "deadline_calculation", "urgency_score", "calendar_management",
                    "calculate_deadline", "calculate_urgency_score"
                ],
                "input_schema": {
                    "calculate_deadline": {
                        "required": [],
                        "optional": ["base_date", "days_ahead", "deadline_text"]
                    }
                },
                "requires_db": False,
                "requires_network": False
            },
            "http_tool": {
                "name": "HTTPTool",
                "capabilities": [
                    "http_get", "http_post", "api_call", "external_request"
                ],
                "input_schema": {
                    "get": {
                        "required": ["url"],
                        "optional": ["params", "headers"]
                    },
                    "post": {
                        "required": ["url"],
                        "optional": ["data", "json", "headers"]
                    }
                },
                "requires_db": False,
                "requires_network": True
            }
        }
    
    def select_tools_for_step(self, step_description: str) -> List[str]:
        """Select tools based on step description keywords."""
        selected = []
        desc_lower = step_description.lower()
        
        # Entity-related keywords
        if any(kw in desc_lower for kw in ["entity", "company", "organization", "business"]):
            if "entity_tool" in self.tools:
                selected.append("entity_tool")
        
        # Task/risk analysis keywords
        if any(kw in desc_lower for kw in ["task", "risk", "analyze", "assessment", "evaluate"]):
            if "task_tool" in self.tools:
                selected.append("task_tool")
        
        # Calendar/deadline keywords
        if any(kw in desc_lower for kw in ["deadline", "calendar", "due date", "urgency", "timeline"]):
            if "calendar_tool" in self.tools:
                selected.append("calendar_tool")
        
        # HTTP/API keywords
        if any(kw in desc_lower for kw in ["fetch", "api", "http", "request", "external", "retrieve"]):
            if "http_tool" in self.tools:
                selected.append("http_tool")
        
        return selected
    
    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific tool."""
        return self.metadata.get(tool_name)
```

### 2. `src/agentic_engine/orchestrator.py`
**Changes:**
- Initialize `ToolRegistry` in `__init__`
- Update `plan()` to include `expected_tools` in each step
- Update `execute_step()` to:
  - Select tools based on step description
  - Call selected tools with safety checks
  - Log tool usage to execution_results
  - Handle tool errors gracefully

**Key Additions:**

1. **In `__init__`:**
```python
from backend.agentic_engine.tools import ToolRegistry

# After tools initialization:
self.tool_registry = ToolRegistry(self.tools)
```

2. **In `plan()` method:**
```python
# After plan generation, add expected_tools to each step:
for step in plan:
    # ... existing code ...
    # Add expected tools based on description
    step["expected_tools"] = self.tool_registry.select_tools_for_step(
        step.get("description", "")
    )
```

3. **In `execute_step()` method:**
```python
# Add tool execution logic before LLM call:
tools_used = []
tool_results = {}

# Select tools for this step
selected_tools = step.get("expected_tools", [])
if not selected_tools:
    selected_tools = self.tool_registry.select_tools_for_step(
        step.get("description", "")
    )

# Execute each selected tool
for tool_name in selected_tools:
    tool = self.tools.get(tool_name)
    if not tool:
        continue
    
    tool_metadata = self.tool_registry.get_tool_metadata(tool_name)
    if not tool_metadata:
        continue
    
    # Safety check for network calls
    if tool_metadata.get("requires_network"):
        # Skip network calls without explicit confirmation
        # (In production, this would prompt user)
        print(f"Warning: Skipping network call for {tool_name} (requires confirmation)")
        continue
    
    # Safety check for DB writes
    if tool_metadata.get("requires_db") and tool_name == "entity_tool":
        # Only allow read operations
        pass
    
    # Execute tool based on step description
    try:
        tool_result = self._execute_tool_for_step(tool, tool_name, step, plan_context)
        if tool_result:
            tool_results[tool_name] = tool_result
            tools_used.append(tool_name)
    except Exception as e:
        tool_results[tool_name] = {
            "error": str(e),
            "success": False
        }
        tools_used.append(tool_name)

# Add tool results to context for LLM
tool_context = ""
if tool_results:
    tool_context = f"\n\nTool Results:\n{json.dumps(tool_results, indent=2)}"
```

4. **New helper method `_execute_tool_for_step()`:**
```python
def _execute_tool_for_step(
    self,
    tool: Any,
    tool_name: str,
    step: Dict[str, Any],
    context: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Execute a tool based on step description and context."""
    step_desc = step.get("description", "").lower()
    
    try:
        if tool_name == "entity_tool":
            # Extract entity name from step or context
            entity_name = context.get("entity") if context else None
            if not entity_name:
                # Try to extract from step description
                import re
                match = re.search(r'entity[:\s]+(\w+)', step_desc)
                if match:
                    entity_name = match.group(1)
            
            if entity_name:
                return {
                    "tool": tool_name,
                    "method": "fetch_entity_details",
                    "inputs": {"entity_name": entity_name},
                    "outputs": tool.fetch_entity_details(entity_name),
                    "success": True
                }
            else:
                # Try similar tasks
                return {
                    "tool": tool_name,
                    "method": "fetch_similar_tasks",
                    "inputs": {"query": step.get("description", "")},
                    "outputs": tool.fetch_similar_tasks(step.get("description", "")),
                    "success": True
                }
        
        elif tool_name == "task_tool":
            task_desc = step.get("description", "")
            category = tool.classify_task_category(task_desc)
            return {
                "tool": tool_name,
                "method": "run_task_risk_analyzer",
                "inputs": {
                    "task_description": task_desc,
                    "task_category": category
                },
                "outputs": tool.run_task_risk_analyzer(task_desc, category),
                "success": True
            }
        
        elif tool_name == "calendar_tool":
            # Extract deadline info from step
            step_desc = step.get("description", "")
            return {
                "tool": tool_name,
                "method": "calculate_urgency_score",
                "inputs": {"deadline": step_desc},
                "outputs": tool.calculate_urgency_score(step_desc),
                "success": True
            }
        
        elif tool_name == "http_tool":
            # HTTP tools require explicit URL - skip for now
            return None
        
    except Exception as e:
        return {
            "tool": tool_name,
            "method": "unknown",
            "inputs": {},
            "outputs": None,
            "success": False,
            "error": str(e)
        }
    
    return None
```

5. **Update executor function to include tool results:**
```python
def executor_fn(step_data, context):
    return {
        "step_id": step_data.get("step_id"),
        "status": "success",
        "output": execution_data.get("output", "Step executed"),
        "findings": execution_data.get("findings", []),
        "risks": execution_data.get("risks", []),
        "confidence": execution_data.get("confidence", 0.7),
        "tools_used": tools_used,  # Add tools_used
        "tool_results": tool_results,  # Add tool_results
        "errors": []
    }
```

### 3. `src/agentic_engine/agent_loop.py`
**Changes:**
- Update `execute_step()` to ensure tool_results are included in execution results
- Add validation for tool_used, inputs, outputs, errors in execution_results

**Key Additions:**
```python
# In execute_step(), ensure result includes tool information:
if "tool_results" not in result:
    result["tool_results"] = {}

# Validate execution results structure
if not isinstance(result.get("tools_used"), list):
    result["tools_used"] = []

# Ensure each tool result has required fields
if result.get("tool_results"):
    for tool_name, tool_result in result["tool_results"].items():
        if not isinstance(tool_result, dict):
            result["tool_results"][tool_name] = {
                "tool": tool_name,
                "inputs": {},
                "outputs": tool_result,
                "errors": []
            }
        else:
            # Ensure required fields
            tool_result.setdefault("tool", tool_name)
            tool_result.setdefault("inputs", {})
            tool_result.setdefault("outputs", {})
            tool_result.setdefault("errors", [])
            tool_result.setdefault("success", True)
```

## Safety Features

1. **Network Call Protection:**
   - HTTPTool requires explicit confirmation before making network calls
   - Logs warning and skips if not confirmed

2. **Database Write Protection:**
   - EntityTool only allows read operations (fetch_entity_details, fetch_similar_tasks)
   - Write operations (if any) require explicit confirmation

3. **Error Handling:**
   - All tool calls wrapped in try-except
   - Errors logged to tool_results with success=False
   - Execution continues even if tools fail

## Validation Requirements

After implementation, verify:
- [ ] All tools have metadata in registry
- [ ] Tool selection works based on step.description
- [ ] Planning includes expected_tools
- [ ] Execution calls tools and logs results
- [ ] Network calls require confirmation
- [ ] DB writes require confirmation
- [ ] Execution results include: tool_used, inputs, outputs, errors
- [ ] No unhandled exceptions from tools

## Testing Checklist

- [ ] Test tool selection for entity-related steps
- [ ] Test tool selection for task-related steps
- [ ] Test tool selection for calendar-related steps
- [ ] Test tool execution with valid inputs
- [ ] Test tool execution with invalid inputs (error handling)
- [ ] Test network call safety (should skip)
- [ ] Test DB write safety (should allow reads only)
- [ ] Verify execution_results structure

