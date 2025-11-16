"""
Example script demonstrating the entity analysis and audit log endpoints

This script shows how to:
1. Analyze an entity and get a compliance calendar
2. Retrieve audit logs for specific tasks
3. Understand autonomy decisions
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000/api/v1"


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_analyze_entity():
    """Example 1: Analyze an entity and get compliance calendar"""
    print_section("Example 1: Entity Analysis with Compliance Calendar")
    
    # Prepare request
    request_data = {
        "entity_name": "GlobalTech Solutions",
        "locations": ["US", "EU", "UK"],
        "entity_type": "PRIVATE_COMPANY",
        "industry": "TECHNOLOGY",
        "employee_count": 500,
        "annual_revenue": 50000000,
        "has_personal_data": True,
        "is_regulated": False,
        "previous_violations": 0
    }
    
    print("Analyzing entity:")
    print(f"  Name: {request_data['entity_name']}")
    print(f"  Locations: {', '.join(request_data['locations'])}")
    print(f"  Industry: {request_data['industry']}")
    print(f"  Employees: {request_data['employee_count']}")
    print()
    
    try:
        # Make API request
        response = requests.post(
            f"{BASE_URL}/entity/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Display results
        print("✓ Analysis Complete!\n")
        
        print(f"Entity: {result['entity_name']}")
        print(f"Jurisdictions: {', '.join(result['jurisdictions'])}")
        print(f"Applicable Regulations: {', '.join(result['applicable_regulations'][:5])}")
        if len(result['applicable_regulations']) > 5:
            print(f"  ... and {len(result['applicable_regulations']) - 5} more")
        print()
        
        # Display summary
        summary = result['summary']
        print("SUMMARY:")
        print(f"  Total Tasks: {summary['total_tasks']}")
        print(f"  Autonomous Tasks: {summary['decisions'].get('autonomous', 0)}")
        print(f"  Review Required: {summary['decisions'].get('reviewrequired', 0)}")
        print(f"  Escalate: {summary['decisions'].get('escalate', 0)}")
        print(f"  Average Confidence: {summary['average_confidence']:.2%}")
        print(f"  Autonomy Rate: {summary['autonomous_percentage']:.1f}%")
        print()
        
        print(f"Risk Distribution:")
        print(f"  HIGH Risk: {summary['high_risk_tasks']} tasks")
        print(f"  MEDIUM Risk: {summary['medium_risk_tasks']} tasks")
        print(f"  LOW Risk: {summary['low_risk_tasks']} tasks")
        print()
        
        # Display first few tasks
        print("COMPLIANCE CALENDAR (first 5 tasks):\n")
        for task in result['tasks'][:5]:
            print(f"📋 {task['task_name']} ({task['task_id']})")
            print(f"   Description: {task['description']}")
            print(f"   Category: {task['category']}")
            print(f"   Frequency: {task['frequency']}")
            if task['deadline']:
                print(f"   Deadline: {task['deadline'][:10]}")
            print(f"   Decision: {task['decision']} (Confidence: {task['confidence']:.2%})")
            print(f"   Risk Level: {task['risk_level']}")
            print(f"   Audit ID: {task['audit_id']}")
            print()
        
        if len(result['tasks']) > 5:
            print(f"... and {len(result['tasks']) - 5} more tasks")
            print()
        
        # Return first task_id for next example
        return result['tasks'][0]['task_id'] if result['tasks'] else None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def example_2_get_audit_log(task_id: str):
    """Example 2: Retrieve audit log for a specific task"""
    print_section(f"Example 2: Retrieve Audit Log for Task {task_id}")
    
    try:
        # Make API request
        response = requests.get(f"{BASE_URL}/audit_log/{task_id}")
        response.raise_for_status()
        
        audit_log = response.json()
        
        # Display audit log
        print("AUDIT LOG DETAILS:\n")
        
        print(f"Task ID: {audit_log['task_id']}")
        print(f"Audit ID: {audit_log['audit_id']}")
        print(f"Timestamp: {audit_log['timestamp']}")
        print()
        
        print(f"Entity: {audit_log['entity_name']}")
        print(f"Task: {audit_log['task_description']}")
        print(f"Category: {audit_log['task_category']}")
        print()
        
        print(f"DECISION: {audit_log['decision_outcome']}")
        print(f"Confidence: {audit_log['confidence_score']:.2%}")
        print(f"Risk Level: {audit_log['risk_level']}")
        print(f"Risk Score: {audit_log['risk_score']:.2f}")
        print()
        
        # Display risk factors
        if audit_log['risk_factors']:
            print("RISK FACTORS:")
            for factor, score in audit_log['risk_factors'].items():
                if factor != 'overall_score':
                    print(f"  {factor}: {score:.2f}")
            print()
        
        # Display reasoning chain
        print("REASONING CHAIN:")
        for i, reason in enumerate(audit_log['reasoning_chain'], 1):
            print(f"  {i}. {reason}")
        print()
        
        # Display recommendations
        if audit_log['recommendations']:
            print("RECOMMENDATIONS:")
            for i, rec in enumerate(audit_log['recommendations'], 1):
                print(f"  {i}. {rec}")
            print()
        
        # Display escalation reason if present
        if audit_log['escalation_reason']:
            print(f"ESCALATION REASON:")
            print(f"  {audit_log['escalation_reason']}")
            print()
        
        return audit_log
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None


def example_3_financial_institution():
    """Example 3: Analyze a financial institution (high-risk entity)"""
    print_section("Example 3: Financial Institution Analysis")
    
    request_data = {
        "entity_name": "SecureBank Corp",
        "locations": ["US"],
        "entity_type": "FINANCIAL_INSTITUTION",
        "industry": "FINANCIAL_SERVICES",
        "employee_count": 2500,
        "annual_revenue": 500000000,
        "has_personal_data": True,
        "is_regulated": True,
        "previous_violations": 0
    }
    
    print("Analyzing financial institution:")
    print(f"  Name: {request_data['entity_name']}")
    print(f"  Type: {request_data['entity_type']}")
    print(f"  Regulated: Yes")
    print()
    
    try:
        response = requests.post(
            f"{BASE_URL}/entity/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        print("✓ Analysis Complete!\n")
        
        summary = result['summary']
        print("SUMMARY:")
        print(f"  Total Tasks: {summary['total_tasks']}")
        print(f"  Autonomous Rate: {summary['autonomous_percentage']:.1f}%")
        print(f"  Average Confidence: {summary['average_confidence']:.2%}")
        print()
        
        # Show tasks requiring escalation
        escalate_tasks = [t for t in result['tasks'] if t['decision'] == 'ESCALATE']
        if escalate_tasks:
            print(f"TASKS REQUIRING ESCALATION ({len(escalate_tasks)}):")
            for task in escalate_tasks:
                print(f"  • {task['task_name']}: {task['risk_level']} risk")
            print()
        
        # Show autonomous tasks
        autonomous_tasks = [t for t in result['tasks'] if t['decision'] == 'AUTONOMOUS']
        if autonomous_tasks:
            print(f"AUTONOMOUS TASKS ({len(autonomous_tasks)}):")
            for task in autonomous_tasks:
                print(f"  • {task['task_name']}: {task['risk_level']} risk (confidence: {task['confidence']:.0%})")
            print()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")


def example_4_export_to_json(task_id: str):
    """Example 4: Export audit log as JSON file"""
    print_section("Example 4: Export Audit Log to JSON File")
    
    try:
        response = requests.get(f"{BASE_URL}/audit_log/{task_id}")
        response.raise_for_status()
        
        audit_log = response.json()
        
        # Save to file
        filename = f"audit_log_{task_id}.json"
        with open(filename, 'w') as f:
            json.dump(audit_log, f, indent=2)
        
        print(f"✓ Audit log exported to: {filename}")
        print(f"  Task: {audit_log['task_description']}")
        print(f"  Decision: {audit_log['decision_outcome']}")
        print(f"  Reasoning steps: {len(audit_log['reasoning_chain'])}")
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")


def example_5_multi_entity_comparison():
    """Example 5: Compare multiple entities"""
    print_section("Example 5: Multi-Entity Comparison")
    
    entities = [
        {
            "entity_name": "Small Startup",
            "locations": ["US"],
            "entity_type": "STARTUP",
            "industry": "TECHNOLOGY",
            "employee_count": 25,
            "has_personal_data": True
        },
        {
            "entity_name": "Mid-Size Company",
            "locations": ["US", "EU"],
            "entity_type": "PRIVATE_COMPANY",
            "industry": "TECHNOLOGY",
            "employee_count": 500,
            "has_personal_data": True
        },
        {
            "entity_name": "Large Enterprise",
            "locations": ["US", "EU", "UK"],
            "entity_type": "PUBLIC_COMPANY",
            "industry": "FINANCIAL_SERVICES",
            "employee_count": 5000,
            "has_personal_data": True,
            "is_regulated": True
        }
    ]
    
    results = []
    
    for entity_data in entities:
        try:
            response = requests.post(
                f"{BASE_URL}/entity/analyze",
                json=entity_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            results.append(response.json())
        except:
            continue
    
    # Compare results
    print("ENTITY COMPARISON:\n")
    print(f"{'Entity':<25} {'Tasks':<8} {'Autonomous %':<15} {'Avg Confidence':<15}")
    print("-" * 65)
    
    for result in results:
        summary = result['summary']
        print(f"{result['entity_name']:<25} "
              f"{summary['total_tasks']:<8} "
              f"{summary['autonomous_percentage']:<14.1f}% "
              f"{summary['average_confidence']:<14.1%}")
    print()


def main():
    """Run all examples"""
    print("\n" + "█" * 80)
    print("  ENTITY ANALYSIS & AUDIT LOG DEMONSTRATION")
    print("█" * 80)
    
    print("\n⚠️  Make sure the API server is running:")
    print("   python main.py")
    print()
    
    input("Press Enter to continue...")
    
    try:
        # Example 1: Analyze entity
        task_id = example_1_analyze_entity()
        
        if task_id:
            # Example 2: Get audit log
            example_2_get_audit_log(task_id)
            
            # Example 4: Export to JSON
            example_4_export_to_json(task_id)
        
        # Example 3: Financial institution
        example_3_financial_institution()
        
        # Example 5: Multi-entity comparison
        example_5_multi_entity_comparison()
        
        print_section("Summary")
        print("✓ All examples completed successfully!")
        print()
        print("Key Features Demonstrated:")
        print("  1. Entity analysis with compliance calendar generation")
        print("  2. Autonomy decisions (AUTONOMOUS/REVIEW_REQUIRED/ESCALATE)")
        print("  3. Detailed audit log retrieval with reasoning chain")
        print("  4. Risk assessment and confidence scoring")
        print("  5. Multi-entity comparison")
        print()
        print("API Endpoints Used:")
        print("  • POST /api/v1/entity/analyze")
        print("  • GET /api/v1/audit_log/{task_id}")
        print()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

