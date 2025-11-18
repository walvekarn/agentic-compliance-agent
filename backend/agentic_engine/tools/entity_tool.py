"""
Entity Tool Module

Provides entity analysis and information retrieval capabilities.
Connects to the production engine for entity data and audit logs.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session


class EntityTool:
    """
    Tool for analyzing entities and retrieving entity information.
    
    Connects to production engine components:
    - EntityAnalyzer for entity risk assessment
    - ComplianceQuery audit log for similar tasks
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize entity tool.
        
        Args:
            db_session: Optional database session for audit log queries
        """
        self.db_session = db_session
        self._entity_analyzer = None
    
    @property
    def name(self) -> str:
        """Get tool name"""
        return "entity_tool"
    
    @property
    def description(self) -> str:
        """Get tool description"""
        return "Analyzes entities and retrieves entity information, risk assessments, and historical data. Fetches entity details, similar tasks from audit log, and entity history."
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Get tool JSON schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["fetch_entity_details", "fetch_similar_tasks", "get_entity_history"],
                    "description": "Action to perform"
                },
                "entity_name": {
                    "type": "string",
                    "description": "Name of the entity"
                },
                "entity_type": {
                    "type": "string",
                    "enum": ["PUBLIC_COMPANY", "PRIVATE_COMPANY", "NONPROFIT", "GOVERNMENT"],
                    "description": "Type of entity"
                },
                "industry": {
                    "type": "string",
                    "description": "Industry category"
                },
                "query": {
                    "type": "string",
                    "description": "Search query for similar tasks"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results"
                },
                "employee_count": {
                    "type": "integer",
                    "description": "Number of employees"
                },
                "annual_revenue": {
                    "type": "number",
                    "description": "Annual revenue"
                },
                "has_personal_data": {
                    "type": "boolean",
                    "description": "Whether entity handles personal data"
                },
                "is_regulated": {
                    "type": "boolean",
                    "description": "Whether entity is in regulated industry"
                },
                "previous_violations": {
                    "type": "integer",
                    "description": "Number of previous compliance violations"
                },
                "jurisdictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of jurisdictions where entity operates"
                }
            },
            "required": ["action", "entity_name"]
        }
    
    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute entity operation.
        
        Args:
            input: Dictionary containing:
                - action: "fetch_entity_details", "fetch_similar_tasks", or "get_entity_history" (required)
                - entity_name: Name of the entity (required)
                - entity_type: Type of entity (optional)
                - industry: Industry category (optional)
                - query: Search query for similar tasks (optional, for fetch_similar_tasks)
                - limit: Maximum number of results (optional)
                - Additional entity attributes (optional, for fetch_entity_details)
        
        Returns:
            Dictionary containing:
                - success: Whether operation succeeded
                - data: Result data (varies by action)
                - error: Error message if failed
        """
        action = input.get("action")
        entity_name = input.get("entity_name")
        
        if not action:
            return {
                "success": False,
                "error": "action is required. Use 'fetch_entity_details', 'fetch_similar_tasks', or 'get_entity_history'"
            }
        
        if not entity_name:
            return {
                "success": False,
                "error": "entity_name is required"
            }
        
        try:
            if action == "fetch_entity_details":
                result = self.fetch_entity_details(
                    entity_name=entity_name,
                    entity_type=input.get("entity_type", "PRIVATE_COMPANY"),
                    industry=input.get("industry", "TECHNOLOGY"),
                    employee_count=input.get("employee_count"),
                    annual_revenue=input.get("annual_revenue"),
                    has_personal_data=input.get("has_personal_data", False),
                    is_regulated=input.get("is_regulated", False),
                    previous_violations=input.get("previous_violations", 0),
                    jurisdictions=input.get("jurisdictions", [])
                )
                return {
                    "success": "error" not in result,
                    "data": result,
                    "error": result.get("error")
                }
            
            elif action == "fetch_similar_tasks":
                result = self.fetch_similar_tasks(
                    query=input.get("query", ""),
                    entity_name=entity_name,
                    limit=input.get("limit", 5)
                )
                return {
                    "success": True,
                    "data": result,
                    "error": None
                }
            
            elif action == "get_entity_history":
                result = self.get_entity_history(
                    entity_name=entity_name,
                    limit=input.get("limit", 10)
                )
                return {
                    "success": True,
                    "data": result,
                    "error": None
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}. Use 'fetch_entity_details', 'fetch_similar_tasks', or 'get_entity_history'"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute entity operation: {str(e)}",
                "data": None
            }
    
    def _get_entity_analyzer(self):
        """Lazy load EntityAnalyzer to avoid circular imports."""
        if self._entity_analyzer is None:
            try:
                from backend.agent.entity_analyzer import EntityAnalyzer
                self._entity_analyzer = EntityAnalyzer()
            except ImportError as e:
                print(f"Warning: Could not import EntityAnalyzer: {e}")
                self._entity_analyzer = None
        return self._entity_analyzer
    
    def fetch_entity_details(
        self,
        entity_name: str,
        entity_type: str = "PRIVATE_COMPANY",
        industry: str = "TECHNOLOGY",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetch entity details from production engine.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of entity (PUBLIC_COMPANY, PRIVATE_COMPANY, etc.)
            industry: Industry category
            **kwargs: Additional entity attributes
        
        Returns:
            Dictionary containing entity details and risk assessment
        """
        try:
            # Import EntityContext and related enums
            from backend.agent.risk_models import EntityContext, EntityType, IndustryCategory
            
            # Map string types to enums
            entity_type_enum = EntityType[entity_type] if entity_type in EntityType.__members__ else EntityType.PRIVATE_COMPANY
            industry_enum = IndustryCategory[industry] if industry in IndustryCategory.__members__ else IndustryCategory.TECHNOLOGY
            
            # Create entity context
            entity = EntityContext(
                name=entity_name,
                entity_type=entity_type_enum,
                industry=industry_enum,
                jurisdictions=kwargs.get('jurisdictions', []),
                employee_count=kwargs.get('employee_count'),
                annual_revenue=kwargs.get('annual_revenue'),
                has_personal_data=kwargs.get('has_personal_data', False),
                is_regulated=kwargs.get('is_regulated', False),
                previous_violations=kwargs.get('previous_violations', 0)
            )
            
            # Get entity analyzer
            analyzer = self._get_entity_analyzer()
            
            if analyzer:
                # Assess capability
                capability, confidence = analyzer.assess_entity_capability(entity)
                
                result = {
                    "name": entity_name,
                    "type": entity_type,
                    "industry": industry,
                    "capability": capability,
                    "confidence": confidence,
                    "details": {
                        "employee_count": kwargs.get('employee_count'),
                        "annual_revenue": kwargs.get('annual_revenue'),
                        "has_personal_data": kwargs.get('has_personal_data', False),
                        "is_regulated": kwargs.get('is_regulated', False),
                        "previous_violations": kwargs.get('previous_violations', 0),
                        "jurisdictions": kwargs.get('jurisdictions', [])
                    }
                }
            else:
                # Fallback if analyzer not available
                result = {
                    "name": entity_name,
                    "type": entity_type,
                    "industry": industry,
                    "capability": "Unknown - Analyzer unavailable",
                    "confidence": 0.5,
                    "details": kwargs
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to fetch entity details: {str(e)}",
                "name": entity_name,
                "type": entity_type,
                "industry": industry
            }
    
    def fetch_similar_tasks(
        self,
        query: str,
        entity_name: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Fetch similar tasks from audit log.
        
        Args:
            query: Search query or task description
            entity_name: Optional entity name to filter by
            limit: Maximum number of results
        
        Returns:
            List of similar tasks from audit log
        """
        if not self.db_session:
            return [{
                "message": "Database session not available",
                "query": query
            }]
        
        try:
            from backend.db.models import ComplianceQuery
            
            # Build query
            db_query = self.db_session.query(ComplianceQuery)
            
            # Filter by entity if provided
            if entity_name:
                db_query = db_query.filter(
                    ComplianceQuery.meta_data['entity'].astext.contains(entity_name)
                )
            
            # Filter by query text (simple contains search)
            if query:
                db_query = db_query.filter(
                    ComplianceQuery.query.contains(query) |
                    ComplianceQuery.response.contains(query)
                )
            
            # Order by most recent and limit
            results = db_query.order_by(
                ComplianceQuery.created_at.desc()
            ).limit(limit).all()
            
            # Format results
            similar_tasks = []
            for result in results:
                similar_tasks.append({
                    "id": result.id,
                    "query": result.query[:200] + "..." if len(result.query) > 200 else result.query,
                    "response_preview": result.response[:200] + "..." if len(result.response) > 200 else result.response,
                    "model": result.model,
                    "status": result.status,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "metadata": result.meta_data
                })
            
            return similar_tasks
            
        except Exception as e:
            return [{
                "error": f"Failed to fetch similar tasks: {str(e)}",
                "query": query
            }]
    
    def get_entity_history(
        self,
        entity_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical analysis data for an entity.
        
        Args:
            entity_name: Name of the entity
            limit: Maximum number of historical records
        
        Returns:
            List of historical compliance queries for the entity
        """
        return self.fetch_similar_tasks("", entity_name=entity_name, limit=limit)
