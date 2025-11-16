"""Entity analysis module for assessing business context and risk"""

from typing import Tuple, List
from .risk_models import (
    EntityContext,
    EntityType,
    IndustryCategory,
    TaskContext
)


class EntityAnalyzer:
    """Analyzes entity characteristics for compliance risk assessment"""
    
    # Entity type risk multipliers
    ENTITY_TYPE_RISK = {
        EntityType.PUBLIC_COMPANY: 0.9,  # High scrutiny, regulatory oversight
        EntityType.FINANCIAL_INSTITUTION: 0.95,  # Highest regulatory requirements
        EntityType.HEALTHCARE: 0.9,  # HIPAA and sensitive data
        EntityType.GOVERNMENT: 0.85,  # Public accountability
        EntityType.PRIVATE_COMPANY: 0.6,  # Moderate oversight
        EntityType.NONPROFIT: 0.5,  # Lower risk profile
        EntityType.STARTUP: 0.4,  # Limited resources but lower scrutiny
        EntityType.UNKNOWN: 0.6,  # Default moderate
    }
    
    # Industry risk scores
    INDUSTRY_RISK = {
        IndustryCategory.FINANCIAL_SERVICES: 0.95,
        IndustryCategory.HEALTHCARE: 0.9,
        IndustryCategory.GOVERNMENT: 0.85,
        IndustryCategory.TECHNOLOGY: 0.7,
        IndustryCategory.RETAIL: 0.6,
        IndustryCategory.EDUCATION: 0.65,
        IndustryCategory.MANUFACTURING: 0.5,
        IndustryCategory.OTHER: 0.5,
    }
    
    def analyze_entity_risk(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Tuple[float, List[str]]:
        """
        Analyze entity-specific risk factors
        
        Args:
            entity: Entity context information
            task: Task context information
            
        Returns:
            Tuple of (risk_score, reasoning_list)
        """
        reasoning = []
        risk_factors = []
        
        # Base entity type risk
        entity_type_risk = self.ENTITY_TYPE_RISK.get(entity.entity_type, 0.6)
        risk_factors.append(entity_type_risk)
        
        if entity.entity_type == EntityType.PUBLIC_COMPANY:
            reasoning.append(
                "🏢 Public company: High regulatory scrutiny, "
                "SEC reporting requirements, shareholder accountability"
            )
        elif entity.entity_type == EntityType.FINANCIAL_INSTITUTION:
            reasoning.append(
                "🏦 Financial institution: Highest compliance standards, "
                "regular audits, strict regulatory oversight"
            )
        elif entity.entity_type == EntityType.HEALTHCARE:
            reasoning.append(
                "🏥 Healthcare entity: HIPAA compliance mandatory, "
                "sensitive patient data protection critical"
            )
        
        # Industry risk
        industry_risk = self.INDUSTRY_RISK.get(entity.industry, 0.5)
        risk_factors.append(industry_risk)
        reasoning.append(
            f"🏭 Industry: {entity.industry.value} - "
            f"{'High' if industry_risk > 0.8 else 'Moderate' if industry_risk > 0.6 else 'Standard'} "
            "regulatory requirements"
        )
        
        # Company size and resources
        if entity.employee_count:
            if entity.employee_count > 5000:
                reasoning.append(
                    "👥 Large organization (5000+ employees): "
                    "Higher compliance capacity but more complex operations"
                )
                risk_factors.append(0.7)
            elif entity.employee_count > 500:
                reasoning.append(
                    "👥 Medium organization (500-5000 employees): "
                    "Balanced resources and complexity"
                )
                risk_factors.append(0.5)
            elif entity.employee_count < 50:
                reasoning.append(
                    "👥 Small organization (<50 employees): "
                    "Limited compliance resources, may need external guidance"
                )
                risk_factors.append(0.4)
        
        # Previous violations increase risk
        if entity.previous_violations > 0:
            violation_risk = min(0.3 + (entity.previous_violations * 0.15), 0.9)
            risk_factors.append(violation_risk)
            reasoning.append(
                f"⚠️ {entity.previous_violations} previous violation(s): "
                "Increased regulatory scrutiny expected"
            )
        
        # Regulated entity flag
        if entity.is_regulated:
            risk_factors.append(0.8)
            reasoning.append(
                "📋 Regulated entity: Subject to direct regulatory oversight, "
                "periodic audits, and strict compliance requirements"
            )
        
        # Data handling considerations
        if entity.has_personal_data and task.affects_personal_data:
            risk_factors.append(0.75)
            reasoning.append(
                "🔐 Handles personal data: Privacy regulations apply, "
                "data breach notification requirements, enhanced security needed"
            )
        
        # Revenue considerations (for potential fines)
        if entity.annual_revenue:
            if entity.annual_revenue > 1_000_000_000:  # > $1B
                reasoning.append(
                    "💰 High revenue organization: Significant potential fines for violations, "
                    "greater reputational risk"
                )
                risk_factors.append(0.75)
            elif entity.annual_revenue > 10_000_000:  # > $10M
                reasoning.append(
                    "💰 Medium revenue organization: Material fines possible, "
                    "reputational considerations important"
                )
                risk_factors.append(0.6)
        
        # Calculate final score
        final_risk = sum(risk_factors) / len(risk_factors) if risk_factors else 0.5
        
        return final_risk, reasoning
    
    def assess_entity_capability(self, entity: EntityContext) -> Tuple[str, float]:
        """
        Assess entity's capability to handle compliance tasks
        
        Args:
            entity: Entity context
            
        Returns:
            Tuple of (capability_description, autonomy_confidence)
        """
        # Larger, well-resourced entities can handle more autonomy
        confidence = 0.5  # Default
        
        if entity.entity_type in [EntityType.PUBLIC_COMPANY, EntityType.FINANCIAL_INSTITUTION]:
            confidence = 0.8
            capability = "High - Likely has dedicated compliance team"
        elif entity.employee_count and entity.employee_count > 500:
            confidence = 0.7
            capability = "Moderate-High - Should have compliance resources"
        elif entity.employee_count and entity.employee_count < 50:
            confidence = 0.4
            capability = "Low - May need external guidance"
        else:
            capability = "Moderate - Standard compliance capability"
        
        # Reduce confidence if previous violations
        if entity.previous_violations > 0:
            confidence *= 0.8
            capability += f" (Note: {entity.previous_violations} previous violations)"
        
        return capability, confidence

