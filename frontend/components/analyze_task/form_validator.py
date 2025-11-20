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
            errors.append(
                "**Company Name** is required. "
                "💡 Enter the name of your organization. This helps personalize the analysis."
            )
        elif len(company_name) < 2:
            errors.append(
                "**Company Name** must be at least 2 characters. "
                "💡 Please enter a valid company name."
            )
        
        # Validate company type
        if not company_type or company_type == "-- Please select --":
            errors.append(
                "**Organization Type** is required. "
                "💡 Select the type that best describes your organization (e.g., Private company, Public company, Startup)."
            )
        
        # Validate industry
        if not industry or industry == "-- Please select --":
            errors.append(
                "**Industry** is required. "
                "💡 Select your industry or sector. Different industries have different compliance requirements."
            )
        
        # Validate employee count
        employee_count_value = parse_positive_int(
            employee_count,
            "Number of Employees",
            errors,
            minimum=1
        )
        if employee_count_value:
            if employee_count_value == 1 and not handles_customer_data:
                warnings.append(
                    "**Single Employee**: You entered 1 employee. "
                    "💡 If correct, continue. Otherwise, adjust above. Single-person operations typically have simpler compliance requirements."
                )
            elif employee_count_value > 10000000:
                errors.append(
                    "**Number of Employees** seems too large. "
                    "💡 Please check your number. If you have more than 10 million employees, contact support."
                )
        
        # Validate locations
        if not locations or len(locations) == 0:
            errors.append(
                "**Operating Locations** is required. "
                "💡 Select at least one location where your organization operates. This determines which regulations apply (e.g., GDPR for EU, HIPAA for US healthcare)."
            )
        
        # Validate task description
        if not task_description:
            errors.append(
                "**Task Description** is required. "
                "💡 Describe what you need to do in your own words. Be specific about the compliance task or question."
            )
        elif len(task_description) < 10:
            errors.append(
                "**Task Description** needs more detail. "
                "💡 Please provide at least 10 characters. More detail helps the AI give better guidance."
            )
        
        # Validate task type
        if not task_type or task_type == "-- Please select --":
            errors.append(
                "**Task Type** is required. "
                "💡 Select the category that best describes your task (e.g., Data Privacy, Policy Review, Regulatory Filing)."
            )
        
        # Validate impact level
        if not impact_level or impact_level == "-- Select impact --":
            errors.append(
                "**Impact Level** is required. "
                "💡 Choose how serious it would be if something went wrong. This helps assess the risk level."
            )
        
        # Validate deadline if checkbox is checked
        has_deadline = form_data.get('has_deadline', False)
        deadline_date = form_data.get('deadline_date')
        if has_deadline and not deadline_date:
            errors.append(
                "**Deadline** is required. "
                "💡 Since you checked the deadline checkbox, please select a deadline date. This helps prioritize the task."
            )
        
        # Validate people affected (optional but warn if extreme)
        people_affected_value = parse_optional_int(
            people_affected,
            "People Affected",
            errors,
            minimum=0
        )
        if people_affected_value and people_affected_value > 1000000:
            warnings.append(
                "**People Affected**: Over 1 million people - this is very high-impact. "
                "💡 This task will likely require expert review due to the large number of people potentially affected."
            )
        
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

