"""
Example script demonstrating audit trail functionality

This script shows how to:
1. Make decisions that get logged to audit trail
2. Query audit trail entries
3. Export audit trail as JSON
4. Get statistics about agent decisions
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.decision_engine import DecisionEngine
from src.agent.audit_service import AuditService
from src.agent.risk_models import (
    EntityContext,
    TaskContext,
    EntityType,
    IndustryCategory,
    Jurisdiction,
    TaskCategory
)
from src.db.base import get_db


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def example_1_log_decisions():
    """Example 1: Make decisions and log them to audit trail"""
    print_section("Example 1: Logging Decisions to Audit Trail")
    
    # Get database session
    db = next(get_db())
    
    # Create test entity
    entity = EntityContext(
        name="TechStartup Inc",
        entity_type=EntityType.STARTUP,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        employee_count=50,
        annual_revenue=2_000_000,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )
    
    # Create various tasks
    tasks = [
        TaskContext(
            description="Review employee data privacy policy",
            category=TaskCategory.POLICY_REVIEW,
            affects_personal_data=True,
            potential_impact="Moderate"
        ),
        TaskContext(
            description="Implement security controls for customer database",
            category=TaskCategory.SECURITY_AUDIT,
            affects_personal_data=True,
            potential_impact="Significant"
        ),
        TaskContext(
            description="General GDPR compliance question",
            category=TaskCategory.GENERAL_INQUIRY
        )
    ]
    
    # Initialize decision engine
    decision_engine = DecisionEngine()
    
    # Process each task and log to audit trail
    print("Processing tasks and logging decisions...\n")
    
    for i, task in enumerate(tasks, 1):
        print(f"Task {i}: {task.description}")
        
        # Make decision
        analysis = decision_engine.analyze_and_decide(entity, task)
        
        # Log to audit trail
        audit_entry = AuditService.log_decision_analysis(
            db=db,
            analysis=analysis,
            agent_type="decision_engine",
            metadata={"example": "audit_trail_demo", "task_number": i}
        )
        
        print(f"  Decision: {analysis.decision.value}")
        print(f"  Risk Level: {analysis.risk_level.value}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Audit ID: {audit_entry.id}")
        print()
    
    print(f"✓ Successfully logged {len(tasks)} decisions to audit trail")
    
    return entity.name


def example_2_query_audit_trail(entity_name: str):
    """Example 2: Query audit trail entries"""
    print_section("Example 2: Querying Audit Trail")
    
    db = next(get_db())
    
    # Query 1: Get recent entries
    print("Query 1: Recent audit entries (limit 5)")
    recent_entries = AuditService.get_audit_trail(db=db, limit=5)
    
    for entry in recent_entries:
        print(f"  [{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
              f"{entry.entity_name or 'Unknown'} - "
              f"{entry.decision_outcome} (confidence: {entry.confidence_score:.2f})")
    print()
    
    # Query 2: Filter by entity
    print(f"Query 2: Entries for entity '{entity_name}'")
    entity_entries = AuditService.get_audit_trail(db=db, entity_name=entity_name, limit=10)
    
    for entry in entity_entries:
        print(f"  Task: {entry.task_description[:50]}...")
        print(f"  Decision: {entry.decision_outcome}, Risk: {entry.risk_level}")
        print()
    
    # Query 3: Filter by risk level
    print("Query 3: High-risk decisions")
    high_risk_entries = AuditService.get_audit_trail(db=db, risk_level="HIGH", limit=5)
    
    if high_risk_entries:
        for entry in high_risk_entries:
            print(f"  [{entry.entity_name}] {entry.task_description[:50]}...")
            print(f"  Risk Score: {entry.risk_score:.2f}")
            if entry.escalation_reason:
                print(f"  Escalation Reason: {entry.escalation_reason}")
            print()
    else:
        print("  No high-risk decisions found")
    print()
    
    # Query 4: Filter by date range
    print("Query 4: Decisions in last 24 hours")
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_decisions = AuditService.get_audit_trail(db=db, start_date=yesterday, limit=10)
    print(f"  Found {len(recent_decisions)} decisions in last 24 hours")
    print()


def example_3_export_json():
    """Example 3: Export audit trail as JSON"""
    print_section("Example 3: Exporting Audit Trail as JSON")
    
    db = next(get_db())
    
    # Export audit trail
    print("Exporting audit trail (limit 5 for demonstration)...\n")
    json_data = AuditService.export_audit_trail_json(db=db, limit=5)
    
    # Pretty print JSON
    print("Sample Audit Entry (first entry):")
    if json_data:
        print(json.dumps(json_data[0], indent=2, default=str))
    else:
        print("No audit entries found")
    
    # Save to file
    filename = f"audit_trail_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print(f"\n✓ Full audit trail exported to: {filename}")


def example_4_statistics():
    """Example 4: Get audit trail statistics"""
    print_section("Example 4: Audit Trail Statistics")
    
    db = next(get_db())
    
    # Get overall statistics
    print("Overall Statistics:\n")
    stats = AuditService.get_audit_statistics(db=db)
    
    print(f"Total Decisions: {stats['total_decisions']}")
    print(f"Average Confidence: {stats['average_confidence']:.2%}")
    print(f"Average Risk Score: {stats['average_risk_score']:.2%}")
    print()
    
    print("Decisions by Outcome:")
    for outcome, count in stats['by_outcome'].items():
        percentage = (count / stats['total_decisions'] * 100) if stats['total_decisions'] > 0 else 0
        print(f"  {outcome}: {count} ({percentage:.1f}%)")
    print()
    
    print("Decisions by Risk Level:")
    for risk_level, count in stats['by_risk_level'].items():
        percentage = (count / stats['total_decisions'] * 100) if stats['total_decisions'] > 0 else 0
        print(f"  {risk_level}: {count} ({percentage:.1f}%)")
    print()
    
    print("Decisions by Agent Type:")
    for agent_type, count in stats['by_agent_type'].items():
        percentage = (count / stats['total_decisions'] * 100) if stats['total_decisions'] > 0 else 0
        print(f"  {agent_type}: {count} ({percentage:.1f}%)")
    print()
    
    if stats['by_task_category']:
        print("Decisions by Task Category:")
        for category, count in sorted(stats['by_task_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
    print()


def example_5_detailed_entry():
    """Example 5: Retrieve and display detailed audit entry"""
    print_section("Example 5: Detailed Audit Entry")
    
    db = next(get_db())
    
    # Get most recent entry
    entries = AuditService.get_audit_trail(db=db, limit=1)
    
    if not entries:
        print("No audit entries found")
        return
    
    entry = entries[0]
    
    print(f"Audit ID: {entry.id}")
    print(f"Timestamp: {entry.timestamp}")
    print(f"Agent Type: {entry.agent_type}")
    print()
    
    print(f"Entity: {entry.entity_name} ({entry.entity_type})")
    print(f"Task: {entry.task_description}")
    print(f"Category: {entry.task_category}")
    print()
    
    print(f"Decision: {entry.decision_outcome}")
    print(f"Confidence: {entry.confidence_score:.2%}")
    print(f"Risk Level: {entry.risk_level}")
    print(f"Risk Score: {entry.risk_score:.2f}" if entry.risk_score else "Risk Score: N/A")
    print()
    
    if entry.risk_factors:
        print("Risk Factors:")
        for factor, value in entry.risk_factors.items():
            if factor != 'overall_score':
                print(f"  {factor}: {value:.2f}")
    print()
    
    if entry.reasoning_chain:
        print("Reasoning Chain:")
        for i, reason in enumerate(entry.reasoning_chain[:5], 1):  # Show first 5 reasons
            print(f"  {i}. {reason}")
        if len(entry.reasoning_chain) > 5:
            print(f"  ... and {len(entry.reasoning_chain) - 5} more steps")
    print()
    
    if entry.recommendations:
        print("Recommendations:")
        for i, rec in enumerate(entry.recommendations, 1):
            print(f"  {i}. {rec}")
    print()
    
    if entry.escalation_reason:
        print(f"Escalation Reason: {entry.escalation_reason}")
        print()


def example_6_custom_logging():
    """Example 6: Log custom decisions"""
    print_section("Example 6: Custom Decision Logging")
    
    db = next(get_db())
    
    print("Logging custom decision...\n")
    
    # Log a custom decision (e.g., from manual review or external system)
    audit_entry = AuditService.log_custom_decision(
        db=db,
        task_description="Manual review of high-risk transaction",
        decision_outcome="APPROVED_WITH_CONDITIONS",
        confidence_score=0.95,
        reasoning_chain=[
            "Transaction reviewed by compliance officer",
            "Additional documentation verified",
            "Enhanced due diligence completed",
            "Approved with monitoring requirements"
        ],
        agent_type="human_reviewer",
        task_category="RISK_ASSESSMENT",
        entity_name="High-Value Client Corp",
        entity_type="PUBLIC_COMPANY",
        risk_level="HIGH",
        risk_score=0.75,
        recommendations=[
            "Continue enhanced monitoring for 90 days",
            "Quarterly review required",
            "Flag for next audit cycle"
        ],
        metadata={
            "reviewer": "John Doe",
            "review_duration_minutes": 45,
            "additional_checks_performed": True
        }
    )
    
    print(f"✓ Custom decision logged with Audit ID: {audit_entry.id}")
    print(f"  Task: {audit_entry.task_description}")
    print(f"  Decision: {audit_entry.decision_outcome}")
    print(f"  Confidence: {audit_entry.confidence_score:.2%}")
    print()


def main():
    """Run all examples"""
    print("\n" + "█" * 80)
    print("  AUDIT TRAIL DEMONSTRATION")
    print("█" * 80)
    
    try:
        # Run examples
        entity_name = example_1_log_decisions()
        example_2_query_audit_trail(entity_name)
        example_3_export_json()
        example_4_statistics()
        example_5_detailed_entry()
        example_6_custom_logging()
        
        print_section("Summary")
        print("✓ All audit trail examples completed successfully!")
        print()
        print("The audit trail system provides comprehensive logging of all agent decisions.")
        print("Use the API endpoints to query, filter, and export audit data for compliance reporting.")
        print()
        print("API Documentation: See AUDIT_TRAIL.md for complete API reference")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

