"""
Create sample data for demo purposes.

Run: python scripts/create_sample_data.py

This script creates sample compliance decisions for demonstration.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.base import engine, Base, get_db
from src.agent.decision_engine import DecisionEngine
from src.agent.risk_models import (
    EntityContext, TaskContext, EntityType, 
    IndustryCategory, Jurisdiction, TaskCategory
)
from src.agent.audit_service import AuditService


def create_sample_decisions():
    """Create 5 sample decisions for demo."""
    # Initialize database
    print("📊 Initializing database...")
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    engine_instance = DecisionEngine()
    
    print("🎯 Creating sample decisions...")
    
    # Sample 1: Low risk - Startup asking about GDPR basics
    print("  Creating sample 1: Low-risk GDPR inquiry...")
    entity1 = EntityContext(
        name="TechStartup Demo",
        entity_type=EntityType.STARTUP,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL],
        employee_count=25,
        has_personal_data=False,
        is_regulated=False,
        previous_violations=0
    )
    task1 = TaskContext(
        description="General question about GDPR data retention policies",
        category=TaskCategory.GENERAL_INQUIRY,
        affects_personal_data=False,
        affects_financial_data=False,
        involves_cross_border=False
    )
    analysis1 = engine_instance.analyze_and_decide(entity1, task1)
    AuditService.log_decision_analysis(db, analysis1, "demo_engine")
    
    # Sample 2: Medium risk - Company updating privacy policy
    print("  Creating sample 2: Medium-risk policy update...")
    entity2 = EntityContext(
        name="GrowthCorp Demo",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
        employee_count=500,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )
    task2 = TaskContext(
        description="Update privacy policy for GDPR compliance",
        category=TaskCategory.POLICY_REVIEW,
        affects_personal_data=True,
        involves_cross_border=True,
        stakeholder_count=1000
    )
    analysis2 = engine_instance.analyze_and_decide(entity2, task2)
    AuditService.log_decision_analysis(db, analysis2, "demo_engine")
    
    # Sample 3: High risk - Financial institution data breach
    print("  Creating sample 3: High-risk incident response...")
    entity3 = EntityContext(
        name="MegaBank Demo",
        entity_type=EntityType.FINANCIAL_INSTITUTION,
        industry=IndustryCategory.FINANCIAL_SERVICES,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.EU],
        employee_count=10000,
        has_personal_data=True,
        is_regulated=True,
        previous_violations=1
    )
    task3 = TaskContext(
        description="Data breach affecting 100K customers - incident response required",
        category=TaskCategory.INCIDENT_RESPONSE,
        affects_personal_data=True,
        affects_financial_data=True,
        stakeholder_count=100000,
        potential_impact="Critical"
    )
    analysis3 = engine_instance.analyze_and_decide(entity3, task3)
    AuditService.log_decision_analysis(db, analysis3, "demo_engine")
    
    # Sample 4: Low risk - General inquiry
    print("  Creating sample 4: Low-risk general inquiry...")
    entity4 = EntityContext(
        name="SmallBiz Demo",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.RETAIL,
        jurisdictions=[Jurisdiction.US_STATE],
        employee_count=15,
        has_personal_data=False,
        is_regulated=False,
        previous_violations=0
    )
    task4 = TaskContext(
        description="What are the basic requirements for customer data storage?",
        category=TaskCategory.GENERAL_INQUIRY,
        affects_personal_data=False
    )
    analysis4 = engine_instance.analyze_and_decide(entity4, task4)
    AuditService.log_decision_analysis(db, analysis4, "demo_engine")
    
    # Sample 5: Medium risk - Contract review
    print("  Creating sample 5: Medium-risk contract review...")
    entity5 = EntityContext(
        name="DataCorp Demo",
        entity_type=EntityType.PRIVATE_COMPANY,
        industry=IndustryCategory.TECHNOLOGY,
        jurisdictions=[Jurisdiction.US_FEDERAL, Jurisdiction.UK],
        employee_count=200,
        has_personal_data=True,
        is_regulated=False,
        previous_violations=0
    )
    task5 = TaskContext(
        description="Review data processing agreement with vendor",
        category=TaskCategory.CONTRACT_REVIEW,
        affects_personal_data=True,
        involves_cross_border=True,
        stakeholder_count=500
    )
    analysis5 = engine_instance.analyze_and_decide(entity5, task5)
    AuditService.log_decision_analysis(db, analysis5, "demo_engine")
    
    # Commit all changes
    db.commit()
    db.close()
    
    print("\n✅ Created 5 sample decisions")
    print("📊 View at: http://localhost:8501")
    print("🔍 Check audit trail at: http://localhost:8000/api/v1/audit/recent")


if __name__ == "__main__":
    try:
        create_sample_decisions()
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

