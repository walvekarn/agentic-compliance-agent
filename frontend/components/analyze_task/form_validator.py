"""
Form Validator
==============
Centralized form validation logic.
"""

from typing import Dict, Any, List, Tuple
from .form_utils import parse_positive_int, parse_optional_int


class FormValidator:
    """Validates form inputs and returns errors/warnings"""
    
    @staticmethod
    def validate(form_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
        Validate all form fields.
        
        Args:
            form_data: Dictionary of form field values
            
        Returns:
            Tuple of (errors, warnings) - both are lists of strings
        """
        errors = []
        warnings = []
        
        # Extract form data
        company_name = form_data.get('company_name', '').strip()
        company_type = form_data.get('company_type', '')
        industry = form_data.get('industry', '')
        employee_count = form_data.get('employee_count', '')
        locations = form_data.get('locations', [])
        handles_customer_data = form_data.get('handles_data', False)
        task_description = form_data.get('task_description', '').strip()
        task_type = form_data.get('task_type', '')
        impact_level = form_data.get('impact_level', '')
        people_affected = form_data.get('people_affected', '')
        
        # Validate company name
        if not company_name:
            errors.append("**Company Name**: Please enter your company name")
        elif len(company_name) < 2:
            errors.append("**Company Name**: Please enter a valid company name (at least 2 characters)")
        
        # Validate company type
        if not company_type or company_type == "-- Please select --":
            errors.append("**Organization Type**: Please select your type of organization")
        
        # Validate industry
        if not industry or industry == "-- Please select --":
            errors.append("**Industry**: Please select your industry")
        
        # Validate employee count
        employee_count_value = parse_positive_int(
            employee_count,
            "the number of employees",
            errors,
            minimum=1
        )
        if employee_count_value == 1 and not handles_customer_data:
            warnings.append("**Single Employee**: You entered 1 employee. If correct, continue. Otherwise, adjust above.")
        
        # Validate locations
        if not locations or len(locations) == 0:
            errors.append("**Operating Locations**: Please select at least one location")
        
        # Validate task description
        if not task_description:
            errors.append("**Task Description**: Please describe what you need to do")
        elif len(task_description) < 10:
            errors.append("**Task Description**: Please provide more details (at least 10 characters)")
        
        # Validate task type
        if not task_type or task_type == "-- Please select --":
            errors.append("**Task Type**: Please select what kind of task this is")
        
        # Validate impact level
        if not impact_level or impact_level == "-- Select impact --":
            errors.append("**Impact**: Please choose how serious it would be if something went wrong")
        
        # Validate deadline if checkbox is checked
        has_deadline = form_data.get('has_deadline', False)
        deadline_date = form_data.get('deadline_date')
        if has_deadline and not deadline_date:
            errors.append("**Deadline**: Please select a deadline date since you checked the deadline checkbox")
        
        # Validate people affected (optional but warn if extreme)
        people_affected_value = parse_optional_int(
            people_affected,
            "the number of people affected",
            errors,
            minimum=0
        )
        if people_affected_value and people_affected_value > 1000000:
            warnings.append("**People Affected**: Over 1 million people - this is very high-impact and will likely require expert review")
        
        return errors, warnings
    
    @staticmethod
    def create_api_payload(form_data: Dict[str, Any], type_map: Dict, industry_map: Dict, 
                          task_map: Dict, impact_map: Dict, location_codes: List[str]) -> Dict[str, Any]:
        """
        Create API payload from validated form data.
        
        Args:
            form_data: Validated form data
            type_map: Company type mapping
            industry_map: Industry mapping
            task_map: Task type mapping
            impact_map: Impact level mapping
            location_codes: List of jurisdiction codes
            
        Returns:
            Dictionary payload for API
        """
        # Parse employee count (already validated)
        employee_count_value = None
        if form_data.get('employee_count'):
            try:
                employee_count_value = int(form_data['employee_count'].strip())
            except ValueError:
                pass
        
        # Parse people affected (optional)
        people_affected_value = None
        if form_data.get('people_affected'):
            try:
                people_affected_value = int(form_data['people_affected'].strip())
            except ValueError:
                pass
        
        # Build payload
        payload = {
            "entity": {
                "name": form_data['company_name'].strip(),
                "entity_type": type_map[form_data['company_type']],
                "industry": industry_map[form_data['industry']],
                "jurisdictions": location_codes,
                "employee_count": employee_count_value,
                "has_personal_data": form_data.get('handles_data', False),
                "is_regulated": form_data.get('is_regulated', False),
                "previous_violations": 0
            },
            "task": {
                "description": form_data['task_description'].strip(),
                "category": task_map[form_data['task_type']],
                "affects_personal_data": form_data.get('involves_personal', False),
                "affects_financial_data": form_data.get('involves_financial', False),
                "involves_cross_border": form_data.get('crosses_borders', False),
                "regulatory_deadline": form_data.get('deadline_date').isoformat() if form_data.get('deadline_date') else None,
                "potential_impact": impact_map[form_data['impact_level']],
                "stakeholder_count": people_affected_value
            }
        }
        
        return payload

