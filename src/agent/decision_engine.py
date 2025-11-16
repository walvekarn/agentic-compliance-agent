"""Decision engine for autonomous action vs escalation logic"""

# Design Decision: Why 6-Factor Model?
# Jurisdiction (15%): Different regulatory frameworks across regions
# Entity (15%): Startup vs bank have different capabilities
# Task (20%): Filing is higher risk than inquiry
# Data Sensitivity (20%): PII/health data require escalation
# Regulatory (20%): GDPR/HIPAA/SOX rules differ
# Impact (10%): Financial consequences drive urgency
# Result: 30-40% autonomous, 60-70% review/escalate

from typing import List, Tuple
from .risk_models import (
    EntityContext,
    TaskContext,
    RiskFactors,
    RiskLevel,
    ActionDecision,
    DecisionAnalysis,
    TaskCategory
)
from .jurisdiction_analyzer import JurisdictionAnalyzer
from .entity_analyzer import EntityAnalyzer


class DecisionEngine:
    """
    Core decision engine that determines when to act autonomously vs escalate
    
    Decision Logic:
    - LOW risk + HIGH confidence → AUTONOMOUS action
    - MEDIUM risk → REVIEW_REQUIRED (human review before action)
    - HIGH risk → ESCALATE (require expert involvement)
    """
    
    # Risk thresholds
    LOW_RISK_THRESHOLD = 0.35
    MEDIUM_RISK_THRESHOLD = 0.65
    
    # Task category risk weights
    TASK_CATEGORY_RISK = {
        TaskCategory.GENERAL_INQUIRY: 0.1,
        TaskCategory.POLICY_REVIEW: 0.4,
        TaskCategory.RISK_ASSESSMENT: 0.5,
        TaskCategory.DATA_PRIVACY: 0.7,
        TaskCategory.CONTRACT_REVIEW: 0.7,
        TaskCategory.SECURITY_AUDIT: 0.75,
        TaskCategory.FINANCIAL_REPORTING: 0.85,
        TaskCategory.REGULATORY_FILING: 0.9,
        TaskCategory.INCIDENT_RESPONSE: 0.95,
    }
    
    def __init__(self):
        self.jurisdiction_analyzer = JurisdictionAnalyzer()
        self.entity_analyzer = EntityAnalyzer()
    
    def analyze_and_decide(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> DecisionAnalysis:
        """
        Perform complete analysis and make decision
        
        Args:
            entity: Entity context information
            task: Task context information
            
        Returns:
            DecisionAnalysis with full reasoning and recommendation
        """
        # Step 1: Analyze jurisdiction risks
        jurisdiction_risk, jurisdiction_reasoning = self.jurisdiction_analyzer.analyze_jurisdiction_risk(
            entity, task
        )
        
        # Step 2: Analyze entity risks
        entity_risk, entity_reasoning = self.entity_analyzer.analyze_entity_risk(
            entity, task
        )
        
        # Step 3: Analyze task-specific risks
        task_risk, task_reasoning = self._analyze_task_risk(entity, task)
        
        # Step 4: Calculate data sensitivity risk
        data_risk, data_reasoning = self._analyze_data_sensitivity(entity, task)
        
        # Step 5: Assess regulatory risk
        regulatory_risk, regulatory_reasoning = self._analyze_regulatory_risk(entity, task)
        
        # Step 6: Assess potential impact
        impact_risk, impact_reasoning = self._analyze_impact_risk(entity, task)
        
        # Compile risk factors
        risk_factors = RiskFactors(
            jurisdiction_risk=jurisdiction_risk,
            entity_risk=entity_risk,
            task_risk=task_risk,
            data_sensitivity_risk=data_risk,
            regulatory_risk=regulatory_risk,
            impact_risk=impact_risk
        )
        
        # Calculate overall risk level
        overall_score = risk_factors.overall_score
        risk_level = self._classify_risk_level(overall_score)
        
        # Make decision
        decision, confidence, decision_reasoning = self._make_decision(
            risk_level, overall_score, entity, task, risk_factors
        )
        
        # Compile all reasoning
        all_reasoning = (
            ["🎯 RISK ANALYSIS:"] +
            jurisdiction_reasoning +
            entity_reasoning +
            task_reasoning +
            data_reasoning +
            regulatory_reasoning +
            impact_reasoning +
            [f"\n📊 OVERALL RISK SCORE: {overall_score:.2f} ({risk_level.value})"] +
            decision_reasoning
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            decision, risk_level, entity, task, risk_factors
        )
        
        # Determine escalation reason if applicable
        escalation_reason = None
        if decision in [ActionDecision.ESCALATE, ActionDecision.REVIEW_REQUIRED]:
            escalation_reason = self._generate_escalation_reason(
                decision, risk_level, risk_factors, entity, task
            )
        
        return DecisionAnalysis(
            entity_context=entity,
            task_context=task,
            risk_factors=risk_factors,
            risk_level=risk_level,
            decision=decision,
            confidence=confidence,
            reasoning=all_reasoning,
            recommendations=recommendations,
            escalation_reason=escalation_reason
        )
    
    def _analyze_task_risk(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Tuple[float, List[str]]:
        """Analyze task-specific risks"""
        reasoning = []
        base_risk = self.TASK_CATEGORY_RISK.get(task.category, 0.5)
        
        reasoning.append(
            f"📋 Task Category: {task.category.value} - "
            f"Base risk level: {'HIGH' if base_risk > 0.7 else 'MEDIUM' if base_risk > 0.4 else 'LOW'}"
        )
        
        # Deadline pressure increases risk
        if task.regulatory_deadline:
            reasoning.append(
                "⏰ Regulatory deadline present: Time pressure may limit review options"
            )
            base_risk = min(base_risk + 0.1, 1.0)
        
        # Stakeholder impact
        if task.stakeholder_count and task.stakeholder_count > 1000:
            reasoning.append(
                f"👥 High stakeholder impact ({task.stakeholder_count:,} affected): "
                "Increased scrutiny required"
            )
            base_risk = min(base_risk + 0.15, 1.0)
        
        return base_risk, reasoning
    
    def _analyze_data_sensitivity(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Tuple[float, List[str]]:
        """Analyze data sensitivity risks"""
        reasoning = []
        risk = 0.3  # Base low risk
        
        if task.affects_personal_data:
            risk += 0.3
            reasoning.append(
                "🔐 Involves personal data: Privacy regulations apply, breach notification required"
            )
        
        if task.affects_financial_data:
            risk += 0.3
            reasoning.append(
                "💳 Involves financial data: Additional security and compliance requirements"
            )
        
        if task.affects_personal_data and task.affects_financial_data:
            risk = min(risk + 0.2, 1.0)
            reasoning.append(
                "⚠️ Combines personal AND financial data: Highest protection standards required"
            )
        
        if not reasoning:
            reasoning.append("ℹ️ No sensitive data indicated: Standard data handling applies")
        
        return min(risk, 1.0), reasoning
    
    def _analyze_regulatory_risk(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Tuple[float, List[str]]:
        """Analyze regulatory compliance risks"""
        reasoning = []
        
        # For general inquiries, start with lower base risk
        if task.category == TaskCategory.GENERAL_INQUIRY:
            risk = 0.2  # Low base for general questions
        else:
            risk = 0.4  # Standard base for other tasks
        
        # Identify applicable regulations
        regulations = self.jurisdiction_analyzer.identify_applicable_regulations(entity, task)
        
        if regulations:
            risk = 0.6 + (len(regulations) * 0.05)
            reasoning.append(
                f"📜 Applicable regulations ({len(regulations)}): {', '.join(regulations[:3])}"
                + ("..." if len(regulations) > 3 else "")
            )
        
        if entity.is_regulated:
            risk = min(risk + 0.2, 1.0)
            reasoning.append(
                "🎯 Directly regulated entity: Regular reporting and audit requirements"
            )
        
        if task.category == TaskCategory.REGULATORY_FILING:
            risk = min(risk + 0.25, 1.0)
            reasoning.append(
                "📤 Regulatory filing task: Errors can result in penalties and legal consequences"
            )
        
        if not reasoning and task.category == TaskCategory.GENERAL_INQUIRY:
            reasoning.append("ℹ️ General inquiry: Minimal regulatory compliance risk")
        
        return min(risk, 1.0), reasoning
    
    def _analyze_impact_risk(
        self,
        entity: EntityContext,
        task: TaskContext
    ) -> Tuple[float, List[str]]:
        """Analyze potential impact risks"""
        reasoning = []
        risk = 0.3
        
        if task.potential_impact:
            impact_lower = task.potential_impact.lower()
            if any(word in impact_lower for word in ['critical', 'severe', 'major', 'significant']):
                risk = 0.9
                reasoning.append(
                    f"🚨 High-impact scenario: '{task.potential_impact}' - "
                    "Errors could have serious consequences"
                )
            elif any(word in impact_lower for word in ['moderate', 'medium']):
                risk = 0.6
                reasoning.append(f"⚡ Moderate impact: '{task.potential_impact}'")
            else:
                risk = 0.3
                reasoning.append(f"ℹ️ Standard impact: '{task.potential_impact}'")
        else:
            # For informational queries (GENERAL_INQUIRY), use low risk
            if task.category == TaskCategory.GENERAL_INQUIRY:
                reasoning.append("ℹ️ General inquiry with no specified impact: Low risk")
                risk = 0.2
            else:
                reasoning.append("ℹ️ Impact level not specified: Assuming low-moderate risk")
                risk = 0.4
        
        return risk, reasoning
    
    def _classify_risk_level(self, score: float) -> RiskLevel:
        """Classify numeric risk score into risk level"""
        if score < self.LOW_RISK_THRESHOLD:
            return RiskLevel.LOW
        elif score < self.MEDIUM_RISK_THRESHOLD:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _make_decision(
        self,
        risk_level: RiskLevel,
        overall_score: float,
        entity: EntityContext,
        task: TaskContext,
        risk_factors: RiskFactors
    ) -> Tuple[ActionDecision, float, List[str]]:
        """
        Make the final decision on autonomous action vs escalation
        
        Returns:
            Tuple of (decision, confidence, reasoning)
        """
        reasoning = ["\n🤔 DECISION LOGIC:"]
        
        # Assess entity capability
        capability_desc, capability_confidence = self.entity_analyzer.assess_entity_capability(entity)
        reasoning.append(f"🏢 Entity capability: {capability_desc}")
        
        # Decision matrix
        if risk_level == RiskLevel.LOW:
            if capability_confidence > 0.6:
                decision = ActionDecision.AUTONOMOUS
                confidence = 0.85
                reasoning.extend([
                    "✅ LOW risk + capable entity → AUTONOMOUS action approved",
                    "Agent can proceed with recommended actions without human review"
                ])
            else:
                decision = ActionDecision.REVIEW_REQUIRED
                confidence = 0.7
                reasoning.extend([
                    "⚠️ LOW risk but limited entity capability → REVIEW recommended",
                    "Quick human review suggested before implementation"
                ])
        
        elif risk_level == RiskLevel.MEDIUM:
            # Medium risk always requires review
            if overall_score < 0.55:
                decision = ActionDecision.REVIEW_REQUIRED
                confidence = 0.75
                reasoning.extend([
                    "⚠️ MEDIUM risk (lower range) → REVIEW_REQUIRED",
                    "Human review and approval needed before taking action",
                    "Agent can provide recommendations, but cannot execute autonomously"
                ])
            else:
                decision = ActionDecision.REVIEW_REQUIRED
                confidence = 0.8
                reasoning.extend([
                    "⚠️ MEDIUM risk (higher range) → REVIEW_REQUIRED",
                    "Thorough human review recommended",
                    "Consider involving compliance specialist"
                ])
        
        else:  # HIGH risk
            decision = ActionDecision.ESCALATE
            confidence = 0.9
            reasoning.extend([
                "🚨 HIGH risk → ESCALATE to human expert",
                "Requires involvement of compliance specialist or legal counsel",
                "Agent should NOT take autonomous action",
                "Provide detailed analysis for expert review"
            ])
        
        # Special override conditions
        if entity.previous_violations > 2:
            if decision == ActionDecision.AUTONOMOUS:
                decision = ActionDecision.REVIEW_REQUIRED
                reasoning.append(
                    "⚠️ Override: Multiple previous violations require human oversight"
                )
        
        if task.category == TaskCategory.INCIDENT_RESPONSE:
            if decision != ActionDecision.ESCALATE:
                decision = ActionDecision.ESCALATE
                reasoning.append(
                    "🚨 Override: Incident response always requires immediate expert involvement"
                )
        
        return decision, confidence, reasoning
    
    def _generate_recommendations(
        self,
        decision: ActionDecision,
        risk_level: RiskLevel,
        entity: EntityContext,
        task: TaskContext,
        risk_factors: RiskFactors
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if decision == ActionDecision.AUTONOMOUS:
            recommendations.extend([
                "✅ Proceed with recommended compliance actions",
                "Document all decisions and rationale",
                "Set up monitoring for ongoing compliance",
            ])
        
        elif decision == ActionDecision.REVIEW_REQUIRED:
            recommendations.extend([
                "📋 Submit analysis to compliance team for review",
                "Prepare detailed documentation of reasoning and approach",
                "Schedule review meeting within 2-3 business days",
            ])
            
            if risk_factors.data_sensitivity_risk > 0.7:
                recommendations.append(
                    "🔐 Have data protection officer review data handling procedures"
                )
        
        else:  # ESCALATE
            recommendations.extend([
                "🚨 IMMEDIATE: Escalate to compliance specialist or legal counsel",
                "Prepare comprehensive briefing document with all context",
                "Do NOT proceed with any actions until expert approval received",
            ])
            
            if risk_factors.regulatory_risk > 0.8:
                recommendations.append(
                    "⚖️ Consider engaging external regulatory counsel"
                )
            
            if task.regulatory_deadline:
                recommendations.append(
                    "⏰ Note regulatory deadline - prioritize expert review"
                )
        
        # General recommendations based on context
        if entity.previous_violations > 0:
            recommendations.append(
                "📝 Extra diligence required due to violation history - document thoroughly"
            )
        
        if task.involves_cross_border:
            recommendations.append(
                "🌍 Cross-border implications - verify data transfer mechanisms"
            )
        
        return recommendations
    
    def _generate_escalation_reason(
        self,
        decision: ActionDecision,
        risk_level: RiskLevel,
        risk_factors: RiskFactors,
        entity: EntityContext,
        task: TaskContext
    ) -> str:
        """Generate clear escalation reason summary"""
        reasons = []
        
        if risk_level == RiskLevel.HIGH:
            reasons.append(f"High overall risk level (score: {risk_factors.overall_score:.2f})")
        
        if risk_factors.regulatory_risk > 0.8:
            reasons.append("Significant regulatory compliance requirements")
        
        if risk_factors.data_sensitivity_risk > 0.8:
            reasons.append("Highly sensitive data involved")
        
        if risk_factors.impact_risk > 0.8:
            reasons.append("Potentially severe impact of errors")
        
        if entity.previous_violations > 0:
            reasons.append(f"Previous compliance violations ({entity.previous_violations})")
        
        if task.category in [TaskCategory.INCIDENT_RESPONSE, TaskCategory.REGULATORY_FILING]:
            reasons.append(f"High-stakes task category: {task.category.value}")
        
        if not reasons:
            reasons.append("Standard review required for medium-risk compliance task")
        
        return "; ".join(reasons)

