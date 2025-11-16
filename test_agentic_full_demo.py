#!/usr/bin/env python3
"""
Full Agentic System Demo
========================
Demonstrates all capabilities:
- Entity lookup
- HTTP call simulation
- Deadline calculation (calendar tool)
- Risk scoring (task tool)
- Multi-pass reasoning
- Post-run metrics
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agentic_engine.orchestrator import AgenticAIOrchestrator
from src.db.base import get_db
from sqlalchemy.orm import Session

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---\n")

def main():
    """Run a comprehensive agentic analysis demo."""
    
    print_section("🤖 AGENTIC COMPLIANCE ANALYSIS - FULL SYSTEM DEMO")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Version: 1.1.0-agentic-orchestrated")
    
    # Complex compliance scenario
    print_section("📋 SCENARIO: Multi-Jurisdictional GDPR Compliance")
    
    scenario = {
        "entity": {
            "entity_name": "GlobalTech Solutions Inc",
            "entity_type": "PRIVATE_COMPANY",
            "locations": ["United States", "European Union countries", "United Kingdom"],
            "industry": "Technology and software",
            "employee_count": 500,
            "annual_revenue": 50000000,
            "has_personal_data": True,
            "is_regulated": False,
            "previous_violations": 1
        },
        "task": {
            "task_description": "Comprehensive GDPR Article 30 compliance assessment for multi-jurisdictional operations. Analyze requirements, assess current state, identify gaps, calculate deadlines for remediation, and provide risk-scored recommendations. Include external regulatory guidance lookup.",
            "task_category": "DATA_PROTECTION",
            "priority": "HIGH",
            "deadline": (datetime.now() + timedelta(days=90)).isoformat()
        },
        "max_iterations": 10
    }
    
    print("Entity:", scenario["entity"]["entity_name"])
    print("Locations:", ", ".join(scenario["entity"]["locations"]))
    print("Task:", scenario["task"]["task_description"])
    print("Deadline:", scenario["task"]["deadline"])
    
    # Initialize orchestrator
    print_section("🔧 INITIALIZING ORCHESTRATOR")
    
    try:
        # Get database session
        db_gen = get_db()
        db_session = next(db_gen)
        
        orchestrator = AgenticAIOrchestrator(
            config={
                "max_steps": 10,
                "enable_reflection": True,
                "enable_memory": True
            },
            db_session=db_session
        )
        
        print("✅ Orchestrator initialized")
        print(f"   - Tools available: {list(orchestrator.tools.keys())}")
        print(f"   - ToolRegistry: {'✅' if hasattr(orchestrator, 'tool_registry') else '❌'}")
        print(f"   - Safety checks: {'✅' if hasattr(orchestrator, 'tool_registry') else '❌'}")
        
    except Exception as e:
        print(f"❌ Error initializing orchestrator: {e}")
        print("   Note: Database connection may not be available. Continuing with in-memory mode...")
        orchestrator = AgenticAIOrchestrator(
            config={
                "max_steps": 10,
                "enable_reflection": True,
                "enable_memory": True
            },
            db_session=None
        )
    
    # Prepare task description
    task_description = (
        f"Analyze compliance task for {scenario['entity']['entity_name']}: "
        f"{scenario['task']['task_description']}"
    )
    
    context = {
        "entity": scenario["entity"],
        "task": scenario["task"]
    }
    
    # Run orchestrator
    print_section("🚀 EXECUTING AGENTIC ANALYSIS")
    print("This may take 60-120 seconds (planning + execution + reflection + multi-pass reasoning)...\n")
    
    start_time = datetime.now()
    
    try:
        result = orchestrator.run(
            task=task_description,
            context=context,
            max_iterations=scenario["max_iterations"]
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Analysis completed in {execution_time:.2f} seconds\n")
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Display Results
    print_section("📊 ANALYSIS RESULTS")
    
    # Plan
    print_subsection("📋 EXECUTION PLAN")
    plan = result.get("plan", [])
    print(f"Total steps: {len(plan)}\n")
    for i, step in enumerate(plan, 1):
        print(f"Step {i}: {step.get('description', 'N/A')}")
        print(f"  Rationale: {step.get('rationale', 'N/A')}")
        if step.get('tools'):
            print(f"  Suggested tools: {', '.join(step.get('tools', []))}")
        print()
    
    # Step Outputs
    print_subsection("⚙️ STEP OUTPUTS")
    step_outputs = result.get("step_outputs", [])
    print(f"Total steps executed: {len(step_outputs)}\n")
    
    for i, output in enumerate(step_outputs, 1):
        step_id = output.get("step_id", f"step_{i}")
        status = output.get("status", "unknown")
        tools_used = output.get("tools_used", [])
        confidence = output.get("confidence", 0.0)
        findings = output.get("findings", [])
        risks = output.get("risks", [])
        reasoning_passes = output.get("metrics", {}).get("reasoning_passes", 1)
        
        status_icon = "✅" if status == "success" else "❌"
        print(f"{status_icon} {step_id}")
        print(f"   Status: {status}")
        print(f"   Confidence: {confidence:.2%}")
        if reasoning_passes > 1:
            print(f"   Reasoning passes: {reasoning_passes} (multi-pass)")
        if tools_used:
            print(f"   Tools used: {', '.join(tools_used)}")
        if findings:
            print(f"   Findings: {len(findings)} found")
            for finding in findings[:2]:  # Show first 2
                print(f"     - {finding[:100]}...")
        if risks:
            print(f"   Risks: {len(risks)} identified")
            for risk in risks[:2]:  # Show first 2
                print(f"     - {risk[:100]}...")
        print()
    
    # Reflections
    print_subsection("🔍 QUALITY REFLECTIONS")
    reflections = result.get("reflections", [])
    print(f"Total reflections: {len(reflections)}\n")
    
    for i, reflection in enumerate(reflections, 1):
        quality = reflection.get("overall_quality", 0.0)
        correctness = reflection.get("correctness_score", 0.0)
        completeness = reflection.get("completeness_score", 0.0)
        requires_retry = reflection.get("requires_retry", False)
        
        quality_icon = "✅" if quality >= 0.7 else "⚠️" if quality >= 0.5 else "❌"
        print(f"{quality_icon} Step {i} Reflection")
        print(f"   Quality Score: {quality:.2%}")
        print(f"   Correctness: {correctness:.2%}")
        print(f"   Completeness: {completeness:.2%}")
        print(f"   Requires Retry: {'Yes' if requires_retry else 'No'}")
        
        issues = reflection.get("issues", [])
        if issues:
            print(f"   Issues: {len(issues)}")
            for issue in issues[:2]:
                print(f"     - {issue[:80]}...")
        print()
    
    # Final Recommendation
    print_subsection("💡 FINAL RECOMMENDATION")
    recommendation = result.get("final_recommendation", "No recommendation available")
    confidence_score = result.get("confidence_score", 0.0)
    
    print(f"Confidence: {confidence_score:.2%}\n")
    print(recommendation[:500] + "..." if len(recommendation) > 500 else recommendation)
    print()
    
    # Tool Metrics
    print_section("🔧 TOOL USAGE METRICS")
    
    if hasattr(orchestrator, 'tool_metrics'):
        tool_metrics = orchestrator.tool_metrics
        print(f"Total tool calls: {tool_metrics.get('total_tool_calls', 0)}")
        print(f"Tools called: {len(set(tool_metrics.get('tools_called', [])))} unique tools\n")
        
        print("Tool Call Statistics:")
        for tool_name in set(tool_metrics.get('tools_called', [])):
            call_count = tool_metrics.get('tool_call_count', {}).get(tool_name, 0)
            success_count = tool_metrics.get('tool_success_count', {}).get(tool_name, 0)
            error_count = tool_metrics.get('tool_error_count', {}).get(tool_name, 0)
            
            print(f"  {tool_name}:")
            print(f"    Calls: {call_count}")
            print(f"    Success: {success_count}")
            print(f"    Errors: {error_count}")
            print()
    else:
        print("⚠️ Tool metrics not available")
    
    # Agent Loop Metrics
    print_section("📈 EXECUTION METRICS")
    
    agent_loop_metrics = orchestrator.agent_loop.get_metrics()
    
    print(f"Total Steps: {agent_loop_metrics.get('total_steps', 0)}")
    print(f"Successful Steps: {agent_loop_metrics.get('successful_steps', 0)}")
    print(f"Failed Steps: {agent_loop_metrics.get('failed_steps', 0)}")
    print(f"Total Retries: {agent_loop_metrics.get('total_retries', 0)}")
    print(f"Total Execution Time: {agent_loop_metrics.get('total_execution_time', 0):.2f}s")
    if agent_loop_metrics.get('average_step_time'):
        print(f"Average Step Time: {agent_loop_metrics.get('average_step_time', 0):.3f}s")
    if agent_loop_metrics.get('success_rate'):
        print(f"Success Rate: {agent_loop_metrics.get('success_rate', 0):.1f}%")
    
    # Reasoning Metrics (if available)
    if hasattr(orchestrator, 'reasoning_engine') and hasattr(orchestrator.reasoning_engine, 'reasoning_metrics'):
        print_section("🧠 REASONING METRICS")
        
        reasoning_metrics = orchestrator.reasoning_engine.reasoning_metrics
        print(f"Total Reasoning Passes: {reasoning_metrics.get('total_passes', 0)}")
        print(f"Pass History: {len(reasoning_metrics.get('pass_history', []))} entries")
        
        confidence_evolution = reasoning_metrics.get('confidence_evolution', [])
        if confidence_evolution:
            print(f"Confidence Evolution: {[f'{c:.2f}' for c in confidence_evolution]}")
    
    # Summary
    print_section("✅ DEMO COMPLETE")
    
    print("Summary:")
    print(f"  ✅ Plan generated: {len(plan)} steps")
    print(f"  ✅ Steps executed: {len(step_outputs)}")
    print(f"  ✅ Reflections: {len(reflections)}")
    print(f"  ✅ Tools used: {len(set(tool_metrics.get('tools_called', []))) if hasattr(orchestrator, 'tool_metrics') else 0}")
    print(f"  ✅ Execution time: {execution_time:.2f}s")
    print(f"  ✅ Final confidence: {confidence_score:.2%}")
    
    # Save results to file
    output_file = project_root / "agentic_demo_results.json"
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0-agentic-orchestrated",
        "scenario": scenario,
        "result": result,
        "tool_metrics": orchestrator.tool_metrics if hasattr(orchestrator, 'tool_metrics') else {},
        "agent_loop_metrics": agent_loop_metrics,
        "execution_time_seconds": execution_time
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"\n📄 Full results saved to: {output_file}")
    print("\n" + "=" * 80)
    print("  Demo completed successfully!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()

