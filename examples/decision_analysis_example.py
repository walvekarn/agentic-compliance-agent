"""
Example script demonstrating the decision engine capabilities
Run this after starting the FastAPI server
"""

import httpx
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"


def print_analysis(analysis: dict):
    """Pretty print decision analysis"""
    print("\n" + "="*80)
    print("🎯 COMPLIANCE DECISION ANALYSIS")
    print("="*80)
    
    print(f"\n📊 RISK ASSESSMENT:")
    print(f"  Overall Risk Score: {analysis['risk_factors']['overall_score']:.2f}")
    print(f"  Risk Level: {analysis['risk_level']}")
    print(f"  Decision: {analysis['decision']}")
    print(f"  Confidence: {analysis['confidence']:.0%}")
    
    print(f"\n🔍 RISK FACTORS:")
    for factor, value in analysis['risk_factors'].items():
        if factor != 'overall_score':
            print(f"  {factor.replace('_', ' ').title()}: {value:.2f}")
    
    print(f"\n💭 REASONING:")
    for reason in analysis['reasoning']:
        print(f"  {reason}")
    
    print(f"\n📋 RECOMMENDATIONS:")
    for rec in analysis['recommendations']:
        print(f"  • {rec}")
    
    if analysis.get('escalation_reason'):
        print(f"\n⚠️  ESCALATION REASON:")
        print(f"  {analysis['escalation_reason']}")
    
    print("="*80 + "\n")


async def example_1_low_risk_startup():
    """Example 1: Low-risk startup with general inquiry"""
    print("\n🔵 EXAMPLE 1: Low-Risk Startup - General Inquiry\n")
    
    entity = {
        "name": "TechStartup Inc",
        "entity_type": "STARTUP",
        "industry": "TECHNOLOGY",
        "jurisdictions": ["US_STATE"],
        "employee_count": 15,
        "annual_revenue": 500000,
        "has_personal_data": True,
        "is_regulated": False,
        "previous_violations": 0
    }
    
    task = {
        "description": "What are the basic GDPR requirements for our email newsletter?",
        "category": "GENERAL_INQUIRY",
        "affects_personal_data": True,
        "affects_financial_data": False,
        "involves_cross_border": False,
        "potential_impact": "Low - informational inquiry"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/decision/analyze",
            json={"entity": entity, "task": task},
            timeout=30.0
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print_analysis(analysis)
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def example_2_high_risk_financial():
    """Example 2: High-risk financial institution with incident response"""
    print("\n🔴 EXAMPLE 2: High-Risk Financial Institution - Data Breach Incident\n")
    
    entity = {
        "name": "Global Bank Corp",
        "entity_type": "FINANCIAL_INSTITUTION",
        "industry": "FINANCIAL_SERVICES",
        "jurisdictions": ["US_FEDERAL", "EU", "UK"],
        "employee_count": 15000,
        "annual_revenue": 10_000_000_000,
        "has_personal_data": True,
        "is_regulated": True,
        "previous_violations": 1
    }
    
    task = {
        "description": "Unauthorized access to customer account database detected",
        "category": "INCIDENT_RESPONSE",
        "affects_personal_data": True,
        "affects_financial_data": True,
        "involves_cross_border": True,
        "potential_impact": "Critical - 500,000 customers potentially affected",
        "stakeholder_count": 500000,
        "regulatory_deadline": (datetime.now() + timedelta(hours=72)).isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/decision/analyze",
            json={"entity": entity, "task": task},
            timeout=30.0
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print_analysis(analysis)
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def example_3_medium_risk_healthcare():
    """Example 3: Medium-risk healthcare provider with policy review"""
    print("\n🟡 EXAMPLE 3: Medium-Risk Healthcare Provider - Policy Review\n")
    
    entity = {
        "name": "City Hospital",
        "entity_type": "HEALTHCARE",
        "industry": "HEALTHCARE",
        "jurisdictions": ["US_FEDERAL", "US_STATE"],
        "employee_count": 2500,
        "annual_revenue": 150_000_000,
        "has_personal_data": True,
        "is_regulated": True,
        "previous_violations": 0
    }
    
    task = {
        "description": "Update patient data retention and deletion policies",
        "category": "POLICY_REVIEW",
        "affects_personal_data": True,
        "affects_financial_data": False,
        "involves_cross_border": False,
        "potential_impact": "Moderate - affects all patient records",
        "stakeholder_count": 50000
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/decision/analyze",
            json={"entity": entity, "task": task},
            timeout=30.0
        )
        
        if response.status_code == 200:
            analysis = response.json()
            print_analysis(analysis)
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def example_4_batch_analysis():
    """Example 4: Batch analysis of multiple tasks"""
    print("\n🔵 EXAMPLE 4: Batch Analysis - Multiple Tasks for One Entity\n")
    
    entity = {
        "name": "E-commerce Platform",
        "entity_type": "PRIVATE_COMPANY",
        "industry": "RETAIL",
        "jurisdictions": ["US_FEDERAL", "EU"],
        "employee_count": 500,
        "annual_revenue": 50_000_000,
        "has_personal_data": True,
        "is_regulated": False,
        "previous_violations": 0
    }
    
    tasks = [
        {
            "description": "Review cookie consent banner compliance",
            "category": "POLICY_REVIEW",
            "affects_personal_data": True,
            "affects_financial_data": False,
            "involves_cross_border": False
        },
        {
            "description": "Implement right to erasure requests",
            "category": "DATA_PRIVACY",
            "affects_personal_data": True,
            "affects_financial_data": False,
            "involves_cross_border": True
        },
        {
            "description": "Update payment processing security",
            "category": "SECURITY_AUDIT",
            "affects_personal_data": False,
            "affects_financial_data": True,
            "involves_cross_border": True
        }
    ]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/decision/batch-analyze",
            json={"entity": entity, "tasks": tasks},
            timeout=30.0
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"Analyzed {len(results)} tasks:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['task_description']}")
                print(f"   Risk: {result['risk_level']} | Decision: {result['decision']} | Score: {result['risk_score']:.2f}")
                if result.get('escalation_reason'):
                    print(f"   ⚠️  {result['escalation_reason']}")
                print()
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("🚀 COMPLIANCE DECISION ENGINE - EXAMPLES")
    print("="*80)
    print("\nMake sure the FastAPI server is running: python main.py\n")
    
    try:
        await example_1_low_risk_startup()
        await example_2_high_risk_financial()
        await example_3_medium_risk_healthcare()
        await example_4_batch_analysis()
        
        print("\n✅ All examples completed!")
        print("\nNext steps:")
        print("  • View full API docs: http://localhost:8000/docs")
        print("  • Check decision info: GET /api/v1/decision/risk-levels")
        print("  • Try quick check: POST /api/v1/decision/quick-check")
        
    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to API server.")
        print("   Please start the server first: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

