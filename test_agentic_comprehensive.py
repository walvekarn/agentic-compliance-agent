#!/usr/bin/env python3
"""
Comprehensive Agentic System Test
=================================
Forces all features:
- Entity lookup
- HTTP call (with explicit URL)
- Deadline calculation
- Risk scoring
- Multi-pass reasoning (complex step)
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agentic_engine.orchestrator import AgenticAIOrchestrator

def main():
    """Run comprehensive test forcing all features."""
    
    print("\n" + "=" * 80)
    print("  🚀 COMPREHENSIVE AGENTIC TEST - ALL FEATURES")
    print("=" * 80 + "\n")
    
    # Scenario designed to trigger ALL features
    scenario = {
        "entity": {
            "entity_name": "MultiNational Corp",
            "entity_type": "PRIVATE_COMPANY",
            "locations": ["United States", "European Union countries", "United Kingdom", "Canada"],
            "industry": "Technology and software",
            "employee_count": 1000,
            "annual_revenue": 100000000,
            "has_personal_data": True,
            "is_regulated": True,
            "previous_violations": 2
        },
        "task": {
            "task_description": "CRITICAL: Comprehensive multi-jurisdictional compliance analysis. Analyze GDPR Article 30 requirements by fetching official guidance from https://gdpr-info.eu/art-30-gdpr/. Assess entity risk profile, calculate urgent remediation deadlines, and provide detailed risk-scored recommendations. This is a complex, high-risk regulatory assessment requiring thorough analysis.",
            "task_category": "DATA_PROTECTION",
            "priority": "HIGH",
            "deadline": (datetime.now() + timedelta(days=30)).isoformat()
        },
        "max_iterations": 15
    }
    
    print("Scenario:")
    print(f"  Entity: {scenario['entity']['entity_name']}")
    print(f"  Locations: {len(scenario['entity']['locations'])} jurisdictions")
    print(f"  Task: {scenario['task']['task_description'][:100]}...")
    print(f"  Deadline: {scenario['task']['deadline']}\n")
    
    # Initialize
    orchestrator = AgenticAIOrchestrator(
        config={"max_steps": 15, "enable_reflection": True, "enable_memory": True},
        db_session=None
    )
    
    print("✅ Orchestrator ready\n")
    
    # Run
    print("Executing... (this will take 90-180 seconds)\n")
    start = datetime.now()
    
    result = orchestrator.run(
        task=f"Analyze compliance for {scenario['entity']['entity_name']}: {scenario['task']['task_description']}",
        context={"entity": scenario["entity"], "task": scenario["task"]},
        max_iterations=scenario["max_iterations"]
    )
    
    elapsed = (datetime.now() - start).total_seconds()
    
    # Results
    print("\n" + "=" * 80)
    print("  📊 RESULTS SUMMARY")
    print("=" * 80 + "\n")
    
    plan = result.get("plan", [])
    outputs = result.get("step_outputs", [])
    reflections = result.get("reflections", [])
    
    print(f"Plan Steps: {len(plan)}")
    print(f"Executed Steps: {len(outputs)}")
    print(f"Reflections: {len(reflections)}")
    print(f"Execution Time: {elapsed:.2f}s")
    print(f"Final Confidence: {result.get('confidence_score', 0):.2%}\n")
    
    # Tool Usage
    print("--- TOOL USAGE ---")
    tool_metrics = orchestrator.tool_metrics
    print(f"Total Tool Calls: {tool_metrics.get('total_tool_calls', 0)}")
    
    tools_used = set(tool_metrics.get('tools_called', []))
    print(f"Tools Used: {', '.join(tools_used) if tools_used else 'None'}")
    
    for tool in ['entity_tool', 'calendar_tool', 'http_tool', 'task_tool']:
        count = tool_metrics.get('tool_call_count', {}).get(tool, 0)
        if count > 0:
            print(f"  ✅ {tool}: {count} calls")
        else:
            print(f"  ❌ {tool}: Not used")
    
    # Multi-pass Reasoning
    print("\n--- MULTI-PASS REASONING ---")
    multi_pass_count = 0
    for output in outputs:
        metrics = output.get('metrics', {})
        passes = metrics.get('reasoning_passes', 1)
        if passes > 1:
            multi_pass_count += 1
            print(f"  ✅ Step {output.get('step_id')}: {passes} reasoning passes")
    
    if multi_pass_count == 0:
        print("  ⚠️ No multi-pass reasoning detected (steps may not have been complex enough)")
    
    # Step Details
    print("\n--- STEP DETAILS ---")
    for i, output in enumerate(outputs, 1):
        step_id = output.get('step_id', f'step_{i}')
        tools = output.get('tools_used', [])
        confidence = output.get('confidence', 0)
        passes = output.get('metrics', {}).get('reasoning_passes', 1)
        
        print(f"\nStep {i} ({step_id}):")
        print(f"  Tools: {', '.join(tools) if tools else 'None'}")
        print(f"  Confidence: {confidence:.2%}")
        print(f"  Reasoning Passes: {passes}")
    
    # Metrics
    print("\n--- METRICS ---")
    agent_metrics = orchestrator.agent_loop.get_metrics()
    print(f"Success Rate: {agent_metrics.get('success_rate', 0):.1f}%")
    print(f"Total Retries: {agent_metrics.get('total_retries', 0)}")
    
    # Save
    output_file = project_root / "comprehensive_test_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "result": result,
            "tool_metrics": tool_metrics,
            "agent_metrics": agent_metrics,
            "elapsed_seconds": elapsed
        }, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {output_file}")
    print("\n" + "=" * 80)
    print("  ✅ Test Complete")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

