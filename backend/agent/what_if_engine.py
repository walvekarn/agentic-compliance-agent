"""
What-If Engine Module

Provides scenario analysis capabilities to simulate changes in risk factors
and see how they affect the overall risk score and decision.
"""

from typing import Dict, Any, Optional, List
from .risk_models import (
    RiskFactors,
    RiskLevel,
    ActionDecision,
    DecisionAnalysis
)
from .decision_engine import DecisionEngine


class WhatIfEngine:
    """
    What-If Engine for scenario analysis.
    
    Allows users to simulate changes to risk factors and see:
    - Changed input
    - New score
    - Explanation
    - Factor deltas
    - Decision change (if any)
    """
    
    def __init__(self, decision_engine: Optional[DecisionEngine] = None):
        """
        Initialize What-If Engine.
        
        Args:
            decision_engine: Optional DecisionEngine instance. If not provided, creates a new one.
        """
        self.decision_engine = decision_engine or DecisionEngine()
    
    def analyze_scenario(
        self,
        baseline: DecisionAnalysis,
        changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a what-if scenario by modifying risk factors.
        
        Args:
            baseline: Baseline DecisionAnalysis to modify
            changes: Dictionary of changes to apply. Keys can be:
                - jurisdiction_risk: float (0.0 to 1.0)
                - entity_risk: float (0.0 to 1.0)
                - task_risk: float (0.0 to 1.0)
                - data_sensitivity_risk: float (0.0 to 1.0)
                - regulatory_risk: float (0.0 to 1.0)
                - impact_risk: float (0.0 to 1.0)
                - entity: EntityContext (modify entity context)
                - task: TaskContext (modify task context)
        
        Returns:
            Dictionary containing:
                - changed_input: Description of what changed
                - new_score: New overall risk score
                - explanation: Explanation of the impact
                - factor_deltas: Changes in each factor
                - decision_change: Whether decision changed and how
                - baseline_score: Original score
                - baseline_decision: Original decision
                - new_decision: New decision
        """
        # Get baseline risk factors
        baseline_factors = baseline.risk_factors
        baseline_score = baseline_factors.overall_score
        baseline_decision = baseline.decision
        baseline_level = baseline.risk_level
        
        # Create modified risk factors
        modified_factors = RiskFactors(
            jurisdiction_risk=changes.get('jurisdiction_risk', baseline_factors.jurisdiction_risk),
            entity_risk=changes.get('entity_risk', baseline_factors.entity_risk),
            task_risk=changes.get('task_risk', baseline_factors.task_risk),
            data_sensitivity_risk=changes.get('data_sensitivity_risk', baseline_factors.data_sensitivity_risk),
            regulatory_risk=changes.get('regulatory_risk', baseline_factors.regulatory_risk),
            impact_risk=changes.get('impact_risk', baseline_factors.impact_risk)
        )
        
        # Calculate new score
        new_score = modified_factors.overall_score
        new_level = modified_factors.classify_risk()
        
        # Calculate factor deltas
        factor_deltas = self._calculate_factor_deltas(baseline_factors, modified_factors)
        
        # Determine new decision if entity/task context changed
        new_decision = baseline_decision
        new_entity = changes.get('entity', baseline.entity_context)
        new_task = changes.get('task', baseline.task_context)
        
        # Recalculate decision if entity or task changed
        if 'entity' in changes or 'task' in changes:
            new_analysis = self.decision_engine.analyze_and_decide(new_entity, new_task)
            new_decision = new_analysis.decision
        else:
            # Use modified risk factors to determine decision
            new_decision, _, _ = self.decision_engine._make_decision(
                new_level, new_score, baseline.entity_context, baseline.task_context, modified_factors
            )
        
        # Generate explanation
        explanation = self._generate_explanation(
            baseline_factors, modified_factors, baseline_score, new_score,
            baseline_level, new_level, baseline_decision, new_decision
        )
        
        # Describe changed input
        changed_input = self._describe_changes(changes, baseline_factors, modified_factors)
        
        # Determine decision change
        decision_change = self._determine_decision_change(
            baseline_decision, new_decision, baseline_level, new_level
        )
        
        return {
            "changed_input": changed_input,
            "new_score": round(new_score, 3),
            "explanation": explanation,
            "factor_deltas": factor_deltas,
            "decision_change": decision_change,
            "baseline_score": round(baseline_score, 3),
            "baseline_decision": baseline_decision.value,
            "baseline_level": baseline_level.value,
            "new_decision": new_decision.value,
            "new_level": new_level.value,
            "score_delta": round(new_score - baseline_score, 3),
            "modified_factors": {
                "jurisdiction_risk": modified_factors.jurisdiction_risk,
                "entity_risk": modified_factors.entity_risk,
                "task_risk": modified_factors.task_risk,
                "data_sensitivity_risk": modified_factors.data_sensitivity_risk,
                "regulatory_risk": modified_factors.regulatory_risk,
                "impact_risk": modified_factors.impact_risk
            }
        }
    
    def _calculate_factor_deltas(
        self,
        baseline: RiskFactors,
        modified: RiskFactors
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate deltas for each risk factor.
        
        Returns:
            Dictionary mapping factor names to delta information
        """
        factors = {
            "jurisdiction": {
                "baseline": baseline.jurisdiction_risk,
                "modified": modified.jurisdiction_risk,
                "delta": modified.jurisdiction_risk - baseline.jurisdiction_risk,
                "weight": 0.15,
                "weighted_delta": (modified.jurisdiction_risk - baseline.jurisdiction_risk) * 0.15
            },
            "entity_risk": {
                "baseline": baseline.entity_risk,
                "modified": modified.entity_risk,
                "delta": modified.entity_risk - baseline.entity_risk,
                "weight": 0.15,
                "weighted_delta": (modified.entity_risk - baseline.entity_risk) * 0.15
            },
            "task_complexity": {
                "baseline": baseline.task_risk,
                "modified": modified.task_risk,
                "delta": modified.task_risk - baseline.task_risk,
                "weight": 0.20,
                "weighted_delta": (modified.task_risk - baseline.task_risk) * 0.20
            },
            "data_sensitivity": {
                "baseline": baseline.data_sensitivity_risk,
                "modified": modified.data_sensitivity_risk,
                "delta": modified.data_sensitivity_risk - baseline.data_sensitivity_risk,
                "weight": 0.20,
                "weighted_delta": (modified.data_sensitivity_risk - baseline.data_sensitivity_risk) * 0.20
            },
            "regulatory_oversight": {
                "baseline": baseline.regulatory_risk,
                "modified": modified.regulatory_risk,
                "delta": modified.regulatory_risk - baseline.regulatory_risk,
                "weight": 0.20,
                "weighted_delta": (modified.regulatory_risk - baseline.regulatory_risk) * 0.20
            },
            "impact": {
                "baseline": baseline.impact_risk,
                "modified": modified.impact_risk,
                "delta": modified.impact_risk - baseline.impact_risk,
                "weight": 0.10,
                "weighted_delta": (modified.impact_risk - baseline.impact_risk) * 0.10
            }
        }
        
        # Round values
        for factor_data in factors.values():
            factor_data["baseline"] = round(factor_data["baseline"], 3)
            factor_data["modified"] = round(factor_data["modified"], 3)
            factor_data["delta"] = round(factor_data["delta"], 3)
            factor_data["weighted_delta"] = round(factor_data["weighted_delta"], 3)
        
        return factors
    
    def _describe_changes(
        self,
        changes: Dict[str, Any],
        baseline: RiskFactors,
        modified: RiskFactors
    ) -> List[str]:
        """Describe what changed in the scenario."""
        descriptions = []
        
        # Risk factor changes
        if 'jurisdiction_risk' in changes:
            old_val = baseline.jurisdiction_risk
            new_val = modified.jurisdiction_risk
            descriptions.append(
                f"Jurisdiction risk: {old_val:.2f} → {new_val:.2f} "
                f"(Δ{new_val - old_val:+.2f})"
            )
        
        if 'entity_risk' in changes:
            old_val = baseline.entity_risk
            new_val = modified.entity_risk
            descriptions.append(
                f"Entity risk: {old_val:.2f} → {new_val:.2f} "
                f"(Δ{new_val - old_val:+.2f})"
            )
        
        if 'task_risk' in changes:
            old_val = baseline.task_risk
            new_val = modified.task_risk
            descriptions.append(
                f"Task complexity: {old_val:.2f} → {new_val:.2f} "
                f"(Δ{new_val - old_val:+.2f})"
            )
        
        if 'data_sensitivity_risk' in changes:
            old_val = baseline.data_sensitivity_risk
            new_val = modified.data_sensitivity_risk
            descriptions.append(
                f"Data sensitivity: {old_val:.2f} → {new_val:.2f} "
                f"(Δ{new_val - old_val:+.2f})"
            )
        
        if 'regulatory_risk' in changes:
            old_val = baseline.regulatory_risk
            new_val = modified.regulatory_risk
            descriptions.append(
                f"Regulatory oversight: {old_val:.2f} → {new_val:.2f} "
                f"(Δ{new_val - old_val:+.2f})"
            )
        
        if 'impact_risk' in changes:
            old_val = baseline.impact_risk
            new_val = modified.impact_risk
            descriptions.append(
                f"Impact severity: {old_val:.2f} → {new_val:.2f} "
                f"(Δ{new_val - old_val:+.2f})"
            )
        
        # Context changes
        if 'entity' in changes:
            entity = changes['entity']
            descriptions.append(f"Entity context changed: {entity.name} ({entity.entity_type.value})")
        
        if 'task' in changes:
            task = changes['task']
            descriptions.append(f"Task context changed: {task.category.value} - {task.description[:50]}...")
        
        if not descriptions:
            descriptions.append("No changes specified")
        
        return descriptions
    
    def _generate_explanation(
        self,
        baseline: RiskFactors,
        modified: RiskFactors,
        baseline_score: float,
        new_score: float,
        baseline_level: RiskLevel,
        new_level: RiskLevel,
        baseline_decision: ActionDecision,
        new_decision: ActionDecision
    ) -> List[str]:
        """Generate explanation of the scenario impact."""
        explanation = []
        
        score_delta = new_score - baseline_score
        
        # Overall impact
        if abs(score_delta) < 0.01:
            explanation.append("📊 Overall risk score remained essentially unchanged.")
        elif score_delta > 0:
            explanation.append(
                f"📈 Overall risk score increased by {score_delta:.3f} "
                f"({baseline_score:.3f} → {new_score:.3f})"
            )
        else:
            explanation.append(
                f"📉 Overall risk score decreased by {abs(score_delta):.3f} "
                f"({baseline_score:.3f} → {new_score:.3f})"
            )
        
        # Risk level change
        if baseline_level != new_level:
            explanation.append(
                f"🎯 Risk level changed: {baseline_level.value} → {new_level.value}"
            )
        else:
            explanation.append(f"🎯 Risk level remained: {new_level.value}")
        
        # Decision change
        if baseline_decision != new_decision:
            explanation.append(
                f"⚡ Decision changed: {baseline_decision.value} → {new_decision.value}"
            )
            if new_decision == ActionDecision.ESCALATE:
                explanation.append("   ⚠️ This scenario requires escalation to human expert")
            elif new_decision == ActionDecision.REVIEW_REQUIRED:
                explanation.append("   📋 This scenario requires human review before action")
            elif new_decision == ActionDecision.AUTONOMOUS:
                explanation.append("   ✅ This scenario allows autonomous action")
        else:
            explanation.append(f"⚡ Decision remained: {new_decision.value}")
        
        # Factor contributions
        explanation.append("\n📊 Factor Contributions to Score Change:")
        factor_names = {
            "jurisdiction": "Jurisdiction (15%)",
            "entity_risk": "Entity Risk (15%)",
            "task_complexity": "Task Complexity (20%)",
            "data_sensitivity": "Data Sensitivity (20%)",
            "regulatory_oversight": "Regulatory Oversight (20%)",
            "impact": "Impact (10%)"
        }
        
        deltas = self._calculate_factor_deltas(baseline, modified)
        for factor_name, factor_data in deltas.items():
            weighted_delta = factor_data["weighted_delta"]
            if abs(weighted_delta) > 0.001:  # Only show significant changes
                direction = "↑" if weighted_delta > 0 else "↓"
                explanation.append(
                    f"   {direction} {factor_names[factor_name]}: "
                    f"{weighted_delta:+.3f} contribution to overall score"
                )
        
        # Interpretation
        explanation.append("\n💡 Interpretation:")
        if new_score < 0.35:
            explanation.append("   Low risk scenario - suitable for autonomous action")
        elif new_score < 0.65:
            explanation.append("   Medium risk scenario - review recommended")
        else:
            explanation.append("   High risk scenario - expert involvement required")
        
        return explanation
    
    def _determine_decision_change(
        self,
        baseline_decision: ActionDecision,
        new_decision: ActionDecision,
        baseline_level: RiskLevel,
        new_level: RiskLevel
    ) -> Dict[str, Any]:
        """Determine if and how the decision changed."""
        changed = baseline_decision != new_decision
        level_changed = baseline_level != new_level
        
        result = {
            "changed": changed,
            "level_changed": level_changed,
            "baseline_decision": baseline_decision.value,
            "new_decision": new_decision.value,
            "baseline_level": baseline_level.value,
            "new_level": new_level.value
        }
        
        if changed:
            if new_decision == ActionDecision.ESCALATE:
                result["impact"] = "Decision escalated - requires expert involvement"
                result["severity"] = "high"
            elif new_decision == ActionDecision.REVIEW_REQUIRED:
                if baseline_decision == ActionDecision.AUTONOMOUS:
                    result["impact"] = "Decision requires review (was autonomous)"
                    result["severity"] = "medium"
                else:
                    result["impact"] = "Decision changed to require review"
                    result["severity"] = "medium"
            elif new_decision == ActionDecision.AUTONOMOUS:
                result["impact"] = "Decision allows autonomous action (was restricted)"
                result["severity"] = "low"
        else:
            result["impact"] = "Decision unchanged"
            result["severity"] = "none"
        
        return result
    
    def compare_scenarios(
        self,
        baseline: DecisionAnalysis,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare multiple what-if scenarios against a baseline.
        
        Args:
            baseline: Baseline DecisionAnalysis
            scenarios: List of scenario change dictionaries
        
        Returns:
            Dictionary with baseline and all scenario results
        """
        results = {
            "baseline": {
                "score": round(baseline.risk_factors.overall_score, 3),
                "level": baseline.risk_level.value,
                "decision": baseline.decision.value
            },
            "scenarios": []
        }
        
        for i, scenario_changes in enumerate(scenarios):
            scenario_result = self.analyze_scenario(baseline, scenario_changes)
            results["scenarios"].append({
                "scenario_id": i + 1,
                "changes": scenario_result["changed_input"],
                "score": scenario_result["new_score"],
                "score_delta": scenario_result["score_delta"],
                "level": scenario_result["new_level"],
                "decision": scenario_result["new_decision"],
                "decision_changed": scenario_result["decision_change"]["changed"],
                "explanation": scenario_result["explanation"]
            })
        
        return results

