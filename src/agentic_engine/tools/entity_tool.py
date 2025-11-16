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
    
    def _get_entity_analyzer(self):
        """Lazy load EntityAnalyzer to avoid circular imports."""
        if self._entity_analyzer is None:
            try:
                from src.agent.entity_analyzer import EntityAnalyzer
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
            **kwargs: Additional entity attributes (employee_count, annual_revenue, etc.)
            
        Returns:
            Dictionary containing entity details and risk assessment
        """
        try:
            # Import EntityContext and related enums
            from src.agent.risk_models import EntityContext, EntityType, IndustryCategory
            
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
                        "previous_violations": kwargs.get('previous_violations', 0)
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
            from src.db.models import ComplianceQuery
            
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
    
    def analyze_entity(
        self,
        entity_name: str,
        entity_type: str = "PRIVATE_COMPANY",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze an entity and return structured information.
        
        Alias for fetch_entity_details for backward compatibility.
        
        Args:
            entity_name: Name of the entity
            entity_type: Type of entity
            **kwargs: Additional entity attributes
            
        Returns:
            Dictionary containing entity analysis
        """
        return self.fetch_entity_details(entity_name, entity_type, **kwargs)
    
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

