"""
Integration Tests for Refactored Components
===========================================
Tests the new modular component architecture.
"""

import pytest
from dashboard.components.constants import (
    TYPE_MAP, INDUSTRY_MAP, TASK_MAP, IMPACT_MAP, 
    JURISDICTION_DISPLAY_TO_CODE
)
from dashboard.components.analyze_task.form_validator import FormValidator


class TestConstantsMappings:
    """Test that all mapping constants are valid"""
    
    def test_industry_map_has_other_not_unknown(self):
        """Verify critical bug fix: 'Other' maps to 'OTHER' not 'UNKNOWN'"""
        assert "Other" in INDUSTRY_MAP
        assert INDUSTRY_MAP["Other"] == "OTHER", "Industry 'Other' must map to 'OTHER' not 'UNKNOWN'"
        assert "UNKNOWN" not in INDUSTRY_MAP.values(), "UNKNOWN should not be in industry values"
    
    def test_all_mappings_have_values(self):
        """Verify no empty mappings"""
        assert len(TYPE_MAP) > 0
        assert len(INDUSTRY_MAP) > 0
        assert len(TASK_MAP) > 0
        assert len(IMPACT_MAP) > 0
        assert len(JURISDICTION_DISPLAY_TO_CODE) > 0
    
    def test_no_placeholder_values_in_mappings(self):
        """Verify no placeholder or select values in backend mappings"""
        for value in TYPE_MAP.values():
            assert "select" not in value.lower()
            assert "--" not in value
        
        for value in INDUSTRY_MAP.values():
            assert "select" not in value.lower()
            assert "--" not in value


class TestFormValidation:
    """Test form validation logic"""
    
    def test_valid_form_passes(self):
        """Test that a valid form passes validation"""
        valid_form = {
            'company_name': 'Test Corp',
            'company_type': 'Private company (not traded publicly)',
            'industry': 'Technology and software',
            'employee_count': '50',
            'locations': ['United States'],
            'handles_data': True,
            'is_regulated': False,
            'task_description': 'We need to update our privacy policy to comply with new regulations',
            'task_type': 'Reviewing or updating a policy',
            'involves_personal': True,
            'involves_financial': False,
            'crosses_borders': False,
            'has_deadline': True,
            'deadline_date': '2025-12-31',
            'impact_level': 'Serious issues',
            'people_affected': '1000'
        }
        
        errors, warnings = FormValidator.validate(valid_form)
        assert len(errors) == 0, f"Valid form should have no errors, got: {errors}"
    
    def test_missing_required_fields_fail(self):
        """Test that missing required fields generate errors"""
        empty_form = {}
        errors, warnings = FormValidator.validate(empty_form)
        assert len(errors) > 0, "Empty form should generate errors"
        
        # Check for specific required field errors
        error_text = " ".join(errors)
        assert "Company Name" in error_text
        assert "Organization Type" in error_text or "company_type" in error_text.lower()
        assert "Industry" in error_text or "industry" in error_text.lower()
    
    def test_short_company_name_fails(self):
        """Test that too-short company names generate errors"""
        form_with_short_name = {
            'company_name': 'A',  # Only 1 character
            'company_type': 'Private company (not traded publicly)',
            'industry': 'Technology and software',
            'employee_count': '50',
            'locations': ['United States'],
            'task_description': 'Test task description that is long enough',
            'task_type': 'Reviewing or updating a policy',
            'impact_level': 'Serious issues'
        }
        
        errors, warnings = FormValidator.validate(form_with_short_name)
        assert any('Company Name' in error for error in errors)
    
    def test_invalid_employee_count_fails(self):
        """Test that invalid employee count generates errors"""
        form_with_invalid_count = {
            'company_name': 'Test Corp',
            'company_type': 'Private company (not traded publicly)',
            'industry': 'Technology and software',
            'employee_count': 'not_a_number',  # Invalid
            'locations': ['United States'],
            'task_description': 'Test task description',
            'task_type': 'Reviewing or updating a policy',
            'impact_level': 'Serious issues'
        }
        
        errors, warnings = FormValidator.validate(form_with_invalid_count)
        assert any('employee' in error.lower() for error in errors)


class TestPayloadCreation:
    """Test API payload creation"""
    
    def test_payload_structure(self):
        """Test that payload has correct structure"""
        form_data = {
            'company_name': 'Test Corp',
            'company_type': 'Private company (not traded publicly)',
            'industry': 'Technology and software',
            'employee_count': '50',
            'task_description': 'Test task',
            'task_type': 'Reviewing or updating a policy',
            'impact_level': 'Serious issues',
            'handles_data': True,
            'is_regulated': False,
            'involves_personal': True,
            'involves_financial': False,
            'crosses_borders': False,
            'deadline_date': None,
            'people_affected': ''
        }
        
        location_codes = ['US_FEDERAL']
        
        payload = FormValidator.create_api_payload(
            form_data, TYPE_MAP, INDUSTRY_MAP, TASK_MAP, 
            IMPACT_MAP, location_codes
        )
        
        # Check top-level structure
        assert 'entity' in payload
        assert 'task' in payload
        
        # Check entity structure
        assert payload['entity']['name'] == 'Test Corp'
        assert payload['entity']['entity_type'] == 'PRIVATE_COMPANY'
        assert payload['entity']['industry'] == 'TECHNOLOGY'
        assert payload['entity']['jurisdictions'] == ['US_FEDERAL']
        assert payload['entity']['employee_count'] == 50
        
        # Check task structure
        assert payload['task']['description'] == 'Test task'
        assert payload['task']['category'] == 'POLICY_REVIEW'
        assert payload['task']['potential_impact'] == 'Significant'
    
    def test_payload_with_other_industry(self):
        """Test that 'Other' industry maps to 'OTHER' not 'UNKNOWN'"""
        form_data = {
            'company_name': 'Test Corp',
            'company_type': 'Private company (not traded publicly)',
            'industry': 'Other',  # Critical test case
            'employee_count': '50',
            'task_description': 'Test task',
            'task_type': 'Reviewing or updating a policy',
            'impact_level': 'Serious issues',
            'handles_data': False,
            'is_regulated': False,
            'involves_personal': False,
            'involves_financial': False,
            'crosses_borders': False,
            'deadline_date': None,
            'people_affected': ''
        }
        
        payload = FormValidator.create_api_payload(
            form_data, TYPE_MAP, INDUSTRY_MAP, TASK_MAP,
            IMPACT_MAP, ['US_FEDERAL']
        )
        
        assert payload['entity']['industry'] == 'OTHER', \
            "Industry 'Other' must map to 'OTHER' in payload"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

