"""
Tool Registry Module

Centralized registry of all available tools with their capabilities,
keywords, and input schemas for intelligent tool selection.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ToolCapability:
    """Represents a capability of a tool."""
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class ToolSchema:
    """Input schema for a tool method."""
    method_name: str
    description: str
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    param_descriptions: Dict[str, str] = field(default_factory=dict)


@dataclass
class ToolMetadata:
    """Complete metadata for a tool."""
    name: str
    description: str
    capabilities: List[ToolCapability] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    schemas: List[ToolSchema] = field(default_factory=list)
    read_only: bool = True  # Default to read-only for safety
    requires_db: bool = False
    requires_http: bool = False


class ToolRegistry:
    """
    Registry of all available tools with their capabilities and schemas.
    
    Enables intelligent tool selection based on step descriptions and context.
    """
    
    def __init__(self):
        """Initialize the tool registry with all available tools."""
        self._tools: Dict[str, ToolMetadata] = {}
        self._initialize_registry()
    
    def _initialize_registry(self):
        """Initialize registry with all tool metadata."""
        # Entity Tool
        self._tools["entity_tool"] = ToolMetadata(
            name="entity_tool",
            description="Analyzes entities and retrieves entity information, risk assessments, and historical data",
            capabilities=[
                ToolCapability(
                    name="entity_analysis",
                    description="Analyze entity risk and capability",
                    keywords=["entity", "organization", "company", "organization", "business", "firm", "corporation"]
                ),
                ToolCapability(
                    name="entity_details",
                    description="Fetch detailed entity information",
                    keywords=["entity details", "entity info", "entity data", "entity information", "entity profile"]
                ),
                ToolCapability(
                    name="similar_tasks",
                    description="Find similar compliance tasks from audit log",
                    keywords=["similar", "previous", "past", "history", "audit log", "similar tasks", "related tasks"]
                ),
                ToolCapability(
                    name="entity_history",
                    description="Retrieve historical analysis for an entity",
                    keywords=["history", "historical", "past analysis", "entity history", "previous analysis"]
                )
            ],
            keywords=[
                "entity", "organization", "company", "business", "firm", "corporation",
                "entity analysis", "entity details", "entity information", "entity profile",
                "similar tasks", "audit log", "history", "historical", "previous", "past"
            ],
            schemas=[
                ToolSchema(
                    method_name="fetch_entity_details",
                    description="Fetch entity details and risk assessment",
                    required_params=["entity_name"],
                    optional_params=["entity_type", "industry", "employee_count", "annual_revenue", 
                                   "has_personal_data", "is_regulated", "previous_violations", "jurisdictions"],
                    param_descriptions={
                        "entity_name": "Name of the entity to analyze",
                        "entity_type": "Type of entity (PUBLIC_COMPANY, PRIVATE_COMPANY, etc.)",
                        "industry": "Industry category (TECHNOLOGY, FINANCE, etc.)",
                        "employee_count": "Number of employees",
                        "annual_revenue": "Annual revenue amount",
                        "has_personal_data": "Whether entity handles personal data",
                        "is_regulated": "Whether entity is in regulated industry",
                        "previous_violations": "Number of previous compliance violations",
                        "jurisdictions": "List of jurisdictions where entity operates"
                    }
                ),
                ToolSchema(
                    method_name="fetch_similar_tasks",
                    description="Find similar compliance tasks from audit log",
                    required_params=["query"],
                    optional_params=["entity_name", "limit"],
                    param_descriptions={
                        "query": "Search query or task description",
                        "entity_name": "Optional entity name to filter by",
                        "limit": "Maximum number of results (default: 5)"
                    }
                ),
                ToolSchema(
                    method_name="get_entity_history",
                    description="Retrieve historical compliance queries for an entity",
                    required_params=["entity_name"],
                    optional_params=["limit"],
                    param_descriptions={
                        "entity_name": "Name of the entity",
                        "limit": "Maximum number of historical records (default: 10)"
                    }
                )
            ],
            read_only=True,
            requires_db=True,
            requires_http=False
        )
        
        # Calendar Tool
        self._tools["calendar_tool"] = ToolMetadata(
            name="calendar_tool",
            description="Manages compliance calendars, deadlines, and urgency calculations",
            capabilities=[
                ToolCapability(
                    name="deadline_calculation",
                    description="Calculate deadlines from various input formats",
                    keywords=["deadline", "due date", "deadline calculation", "calculate deadline", 
                            "date calculation", "when due", "due by"]
                ),
                ToolCapability(
                    name="urgency_scoring",
                    description="Calculate urgency scores based on deadlines",
                    keywords=["urgency", "urgent", "urgency score", "priority", "time sensitive", 
                            "time-sensitive", "critical", "high priority"]
                ),
                ToolCapability(
                    name="deadline_parsing",
                    description="Parse natural language deadline descriptions",
                    keywords=["parse deadline", "deadline text", "natural language deadline", 
                            "deadline parsing", "date parsing"]
                )
            ],
            keywords=[
                "deadline", "due date", "calendar", "date", "time", "urgency", "urgent",
                "deadline calculation", "calculate deadline", "urgency score", "priority",
                "time sensitive", "time-sensitive", "critical", "high priority", "when due",
                "due by", "parse deadline", "deadline text", "natural language deadline"
            ],
            schemas=[
                ToolSchema(
                    method_name="calculate_deadline",
                    description="Calculate deadline from various inputs",
                    required_params=[],
                    optional_params=["base_date", "days_ahead", "deadline_text"],
                    param_descriptions={
                        "base_date": "Base date in ISO format (YYYY-MM-DD)",
                        "days_ahead": "Number of days ahead from base_date",
                        "deadline_text": "Natural language deadline (e.g., '30 days', 'Q4 2024')"
                    }
                ),
                ToolSchema(
                    method_name="calculate_urgency_score",
                    description="Calculate urgency score for a task based on deadline",
                    required_params=["deadline"],
                    optional_params=["task_category"],
                    param_descriptions={
                        "deadline": "Deadline in ISO format or natural language",
                        "task_category": "Task category for risk weighting (default: GENERAL_INQUIRY)"
                    }
                )
            ],
            read_only=True,
            requires_db=False,
            requires_http=False
        )
        
        # HTTP Tool
        self._tools["http_tool"] = ToolMetadata(
            name="http_tool",
            description="Makes HTTP requests to external APIs and services",
            capabilities=[
                ToolCapability(
                    name="http_get",
                    description="Make HTTP GET requests",
                    keywords=["http", "api", "external", "fetch", "retrieve", "url", "get request",
                            "http request", "api call", "external api", "fetch data", "retrieve data"]
                ),
                ToolCapability(
                    name="http_post",
                    description="Make HTTP POST requests",
                    keywords=["post", "submit", "send", "http post", "post request", "api post"]
                )
            ],
            keywords=[
                "http", "https", "api", "external", "fetch", "retrieve", "url", "endpoint",
                "http request", "api call", "external api", "fetch data", "retrieve data",
                "get request", "post request", "http get", "http post", "api endpoint"
            ],
            schemas=[
                ToolSchema(
                    method_name="get_sync",
                    description="Make synchronous HTTP GET request",
                    required_params=["url"],
                    optional_params=["params", "headers"],
                    param_descriptions={
                        "url": "Target URL to fetch",
                        "params": "Query parameters as dictionary",
                        "headers": "HTTP headers as dictionary"
                    }
                ),
                ToolSchema(
                    method_name="post_sync",
                    description="Make synchronous HTTP POST request",
                    required_params=["url"],
                    optional_params=["data", "json", "headers"],
                    param_descriptions={
                        "url": "Target URL",
                        "data": "Form data as dictionary",
                        "json": "JSON data as dictionary",
                        "headers": "HTTP headers as dictionary"
                    }
                )
            ],
            read_only=True,  # HTTP tool is read-only (no writes)
            requires_db=False,
            requires_http=True
        )
        
        # Task Tool
        self._tools["task_tool"] = ToolMetadata(
            name="task_tool",
            description="Analyzes compliance tasks, calculates risk scores, and classifies task categories",
            capabilities=[
                ToolCapability(
                    name="task_risk_analysis",
                    description="Analyze task risk and provide recommendations",
                    keywords=["task", "risk", "compliance", "regulation", "task risk", "risk analysis",
                            "compliance risk", "task analysis", "risk assessment", "compliance task"]
                ),
                ToolCapability(
                    name="task_classification",
                    description="Classify tasks into categories",
                    keywords=["classify", "category", "task category", "task type", "task classification",
                            "categorize task", "task classification"]
                ),
                ToolCapability(
                    name="task_analysis",
                    description="Analyze task and extract key information",
                    keywords=["analyze task", "task analysis", "task details", "task info", "task information"]
                )
            ],
            keywords=[
                "task", "risk", "compliance", "regulation", "task risk", "risk analysis",
                "compliance risk", "task analysis", "risk assessment", "compliance task",
                "classify", "category", "task category", "task type", "task classification",
                "categorize task", "analyze task", "task details", "task info", "task information"
            ],
            schemas=[
                ToolSchema(
                    method_name="run_task_risk_analyzer",
                    description="Run task risk analyzer from production engine",
                    required_params=["task_description"],
                    optional_params=["task_category", "affects_personal_data", "deadline", "requires_filing", "data_types"],
                    param_descriptions={
                        "task_description": "Description of the compliance task",
                        "task_category": "Category of task (GENERAL_INQUIRY, REGULATORY_FILING, etc.)",
                        "affects_personal_data": "Whether task affects personal data",
                        "deadline": "Task deadline",
                        "requires_filing": "Whether task requires regulatory filing",
                        "data_types": "List of data types involved"
                    }
                ),
                ToolSchema(
                    method_name="classify_task_category",
                    description="Classify task into appropriate category based on description",
                    required_params=["task_description"],
                    optional_params=[],
                    param_descriptions={
                        "task_description": "Description of the task"
                    }
                ),
                ToolSchema(
                    method_name="analyze_task",
                    description="Analyze a task and extract key information",
                    required_params=["task_description"],
                    optional_params=[],
                    param_descriptions={
                        "task_description": "Description of the task"
                    }
                )
            ],
            read_only=True,
            requires_db=False,
            requires_http=False
        )
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            ToolMetadata if found, None otherwise
        """
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, ToolMetadata]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def match_tools_to_step(
        self, 
        step_description: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Match tools to a step based on description and context.
        
        Uses keyword matching and capability analysis to identify relevant tools.
        Supports multi-tool selection.
        
        Args:
            step_description: Description of the step
            context: Optional context information
            
        Returns:
            List of tool names that match the step
        """
        step_lower = step_description.lower()
        matched_tools: Set[str] = set()
        
        # Score each tool based on keyword matches
        tool_scores: Dict[str, float] = {}
        
        for tool_name, metadata in self._tools.items():
            score = 0.0
            
            # Check keyword matches
            for keyword in metadata.keywords:
                if keyword.lower() in step_lower:
                    # Weight by keyword length (longer keywords are more specific)
                    score += len(keyword) * 0.1
            
            # Check capability keyword matches
            for capability in metadata.capabilities:
                for keyword in capability.keywords:
                    if keyword.lower() in step_lower:
                        score += len(keyword) * 0.15  # Capability keywords weighted higher
            
            # Context-based matching
            if context:
                # Check if context mentions entities
                if tool_name == "entity_tool":
                    if context.get("entity") or any(
                        word in step_lower for word in ["entity", "organization", "company"]
                    ):
                        score += 5.0
                
                # Check if context mentions deadlines
                if tool_name == "calendar_tool":
                    if context.get("task", {}).get("deadline") or any(
                        word in step_lower for word in ["deadline", "due date", "urgency"]
                    ):
                        score += 5.0
                
                # Check if context mentions tasks
                if tool_name == "task_tool":
                    if context.get("task") or any(
                        word in step_lower for word in ["task", "risk", "compliance"]
                    ):
                        score += 5.0
                
                # Check if context mentions URLs or external APIs
                if tool_name == "http_tool":
                    if "http://" in step_lower or "https://" in step_lower or "api" in step_lower:
                        score += 5.0
            
            if score > 0:
                tool_scores[tool_name] = score
        
        # Select tools with score >= 2.0 (threshold for relevance)
        threshold = 2.0
        for tool_name, score in tool_scores.items():
            if score >= threshold:
                matched_tools.add(tool_name)
        
        # Always return at least one tool if any match, otherwise return empty
        return sorted(list(matched_tools), key=lambda t: tool_scores.get(t, 0), reverse=True)
    
    def get_tool_capabilities(self, tool_name: str) -> List[str]:
        """
        Get list of capability names for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of capability names
        """
        metadata = self.get_tool_metadata(tool_name)
        if metadata:
            return [cap.name for cap in metadata.capabilities]
        return []
    
    def get_tool_schemas(self, tool_name: str) -> List[ToolSchema]:
        """
        Get input schemas for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of ToolSchema objects
        """
        metadata = self.get_tool_metadata(tool_name)
        if metadata:
            return metadata.schemas
        return []
    
    def is_read_only(self, tool_name: str) -> bool:
        """
        Check if a tool is read-only.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if read-only, False otherwise
        """
        metadata = self.get_tool_metadata(tool_name)
        if metadata:
            return metadata.read_only
        return True  # Default to read-only for safety
    
    def requires_http(self, tool_name: str) -> bool:
        """
        Check if a tool requires HTTP access.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if requires HTTP, False otherwise
        """
        metadata = self.get_tool_metadata(tool_name)
        if metadata:
            return metadata.requires_http
        return False

