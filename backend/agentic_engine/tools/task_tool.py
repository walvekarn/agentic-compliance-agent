"""
Task Tool Module

Provides task management and analysis capabilities.
Connects to the production decision engine for risk analysis.
"""

from typing import Dict, Any, Optional
import logging


class TaskTool:
    """
    Tool for managing and analyzing compliance tasks.
    
    Connects to production engine components:
    - DecisionEngine for task risk analysis
    - Task risk classification and scoring
    """
    
    def __init__(self):
        """Initialize task tool."""
        self._decision_engine = None
        self._logger = logging.getLogger(__name__)
    
    @property
    def name(self) -> str:
        """Get tool name"""
        return "task_tool"
    
    @property
    def description(self) -> str:
        """Get tool description"""
        return "Analyzes compliance tasks, calculates risk scores, and classifies task categories. Provides task risk assessment and recommendations."
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Get tool JSON schema"""
        return {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Description of the compliance task"
                },
                "task_category": {
                    "type": "string",
                    "enum": [
                        "GENERAL_INQUIRY",
                        "POLICY_REVIEW",
                        "RISK_ASSESSMENT",
                        "DATA_PRIVACY",
                        "CONTRACT_REVIEW",
                        "SECURITY_AUDIT",
                        "FINANCIAL_REPORTING",
                        "REGULATORY_FILING",
                        "INCIDENT_RESPONSE"
                    ],
                    "description": "Category of task"
                },
                "affects_personal_data": {
                    "type": "boolean",
                    "description": "Whether task affects personal data"
                },
                "requires_filing": {
                    "type": "boolean",
                    "description": "Whether task requires regulatory filing"
                },
                "deadline": {
                    "type": "string",
                    "description": "Task deadline (ISO format or natural language)"
                },
                "data_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of data types involved"
                }
            },
            "required": ["task_description"]
        }
    
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task analysis.
        
        Args:
            input: Dictionary containing:
                - task_description: Description of the task (required)
                - task_category: Category of task (optional)
                - affects_personal_data: Whether affects personal data (optional)
                - requires_filing: Whether requires filing (optional)
                - deadline: Task deadline (optional)
                - data_types: List of data types (optional)
        
        Returns:
            Dictionary containing:
                - success: Whether analysis succeeded
                - task_description: Task description
                - category: Task category
                - risk_score: Risk score (0.0 to 1.0)
                - risk_level: Risk level (LOW, MEDIUM, HIGH)
                - recommendation: Recommendation text
                - reasoning: List of reasoning steps
                - analysis: Detailed analysis
                - error: Error message if failed
        """
        task_description = input.get("task_description")
        if not task_description:
            return {
                "success": False,
                "error": "task_description is required",
                "task_description": None
            }
        
        try:
            return self.run_task_risk_analyzer(
                task_description=task_description,
                task_category=input.get("task_category", "GENERAL_INQUIRY"),
                affects_personal_data=input.get("affects_personal_data", False),
                requires_filing=input.get("requires_filing", False),
                deadline=input.get("deadline"),
                data_types=input.get("data_types", [])
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze task: {str(e)}",
                "task_description": task_description
            }
    
    def _get_decision_engine(self):
        """Lazy load DecisionEngine to avoid circular imports."""
        if self._decision_engine is None:
            try:
                from backend.agent.decision_engine import DecisionEngine
                self._decision_engine = DecisionEngine()
            except ImportError as e:
                self._logger.warning(f"Could not import DecisionEngine: {e}")
                self._decision_engine = None
        return self._decision_engine
    
    def run_task_risk_analyzer(
        self,
        task_description: str,
        task_category: str = "GENERAL_INQUIRY",
        affects_personal_data: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run task risk analyzer from production engine.
        
        Args:
            task_description: Description of the compliance task
            task_category: Category of task
            affects_personal_data: Whether task affects personal data
            **kwargs: Additional task context
        
        Returns:
            Dictionary containing risk analysis and recommendations
        """
        try:
            from backend.agent.risk_models import TaskContext, TaskCategory
            
            # Map string to TaskCategory enum
            try:
                task_cat_enum = TaskCategory[task_category]
            except KeyError:
                task_cat_enum = TaskCategory.GENERAL_INQUIRY
            
            # Get decision engine
            engine = self._get_decision_engine()
            
            if engine:
                # Calculate task risk using production engine
                task_risk = engine.TASK_CATEGORY_RISK.get(task_cat_enum, 0.5)
                
                # Analyze task-specific factors
                risk_factors = []
                reasoning = []
                
                # Base category risk
                risk_factors.append(task_risk)
                reasoning.append(
                    f"Task category: {task_category} - "
                    f"{'High' if task_risk > 0.7 else 'Medium' if task_risk > 0.4 else 'Low'} base risk"
                )
                
                # Personal data factor
                if affects_personal_data:
                    risk_factors.append(0.7)
                    reasoning.append("Task affects personal data - privacy regulations apply")
                
                # Filing requirement
                if kwargs.get('requires_filing'):
                    risk_factors.append(0.8)
                    reasoning.append("Requires regulatory filing - high compliance scrutiny")
                
                # Deadline urgency
                if kwargs.get('deadline'):
                    risk_factors.append(0.6)
                    reasoning.append("Has deadline - time-sensitive compliance requirement")
                
                # Calculate overall task risk
                overall_risk = sum(risk_factors) / len(risk_factors) if risk_factors else 0.5
                
                # Classify risk level
                if overall_risk < engine.LOW_RISK_THRESHOLD:
                    risk_level = "LOW"
                    recommendation = "Task can likely be handled autonomously"
                elif overall_risk < engine.MEDIUM_RISK_THRESHOLD:
                    risk_level = "MEDIUM"
                    recommendation = "Review required before action"
                else:
                    risk_level = "HIGH"
                    recommendation = "Escalate to expert - high-risk task"
                
                return {
                    "success": True,
                    "task_description": task_description,
                    "category": task_category,
                    "risk_score": round(overall_risk, 2),
                    "risk_level": risk_level,
                    "recommendation": recommendation,
                    "reasoning": reasoning,
                    "analysis": {
                        "affects_personal_data": affects_personal_data,
                        "requires_filing": kwargs.get('requires_filing', False),
                        "has_deadline": kwargs.get('deadline') is not None,
                        "base_category_risk": task_risk
                    }
                }
            else:
                # Fallback if engine not available
                return {
                    "success": True,
                    "task_description": task_description,
                    "category": task_category,
                    "risk_score": 0.5,
                    "risk_level": "MEDIUM",
                    "recommendation": "Engine unavailable - manual review recommended",
                    "reasoning": ["Decision engine not available"],
                    "analysis": kwargs
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze task risk: {str(e)}",
                "task_description": task_description,
                "category": task_category
            }
    
    def classify_task_category(self, task_description: str) -> str:
        """
        Classify task into appropriate category based on description.
        
        Args:
            task_description: Description of the task
            
        Returns:
            Predicted task category
        """
        description_lower = task_description.lower()
        
        # Simple keyword-based classification
        if any(word in description_lower for word in ['gdpr', 'privacy', 'personal data', 'pii']):
            return "DATA_PRIVACY"
        elif any(word in description_lower for word in ['file', 'filing', 'submit', 'report to']):
            return "REGULATORY_FILING"
        elif any(word in description_lower for word in ['contract', 'agreement', 'vendor']):
            return "CONTRACT_REVIEW"
        elif any(word in description_lower for word in ['security', 'breach', 'incident']):
            return "SECURITY_AUDIT"
        elif any(word in description_lower for word in ['financial', 'audit', 'sox', 'revenue']):
            return "FINANCIAL_REPORTING"
        elif any(word in description_lower for word in ['risk', 'assess', 'evaluation']):
            return "RISK_ASSESSMENT"
        elif any(word in description_lower for word in ['policy', 'procedure', 'guideline']):
            return "POLICY_REVIEW"
        else:
            return "GENERAL_INQUIRY"
