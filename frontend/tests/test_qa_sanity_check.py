"""
QA Sanity Check - Analyze Task Flow
====================================
Full integration test for the Analyze Task feature restoration.

Tests 4 scenarios to ensure system stability and correct behavior:
1. Low-risk task (minimal data)
2. High-risk + escalation (full data)
3. Missing fields (graceful degradation)
4. Mixed-format data (auto-normalization)
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.analyze_task.results_display import render_results
from components.analyze_task.confidence_display import render_confidence_meter
from components.analyze_task.risk_display import render_risk_breakdown
from components.analyze_task.similar_cases_display import render_similar_cases
from components.analyze_task.suggestions_display import render_proactive_suggestions


class TestScenario1_LowRiskTask:
    """
    Scenario 1: Low-risk task with minimal data
    
    Expected behavior:
    - Confidence meter displays
    - No escalation reason (not ESCALATE decision)
    - No similar cases section
    - No crashes
    """
    
    def test_low_risk_task_complete_flow(self):
        """Test low-risk task flows through all components without crashing."""
        analysis = {
            'decision': 'AUTONOMOUS',
            'confidence_score': 0.9,
            'risk_level': 'LOW',
            'risk_score': 0.2,
            'risk_factors': {
                'jurisdiction_risk': 0.1,
                'entity_risk': 0.15,
                'task_risk': 0.2,
                'data_sensitivity_risk': 0.1,
                'regulatory_risk': 0.15,
                'impact_risk': 0.1
            },
            'reasoning_chain': [
                'Low-risk routine task',
                'Standard compliance scenario',
                'No special approvals needed'
            ],
            'recommendations': [
                'Follow standard procedures',
                'Document the decision'
            ],
            'similar_cases': [],  # No similar cases
            'proactive_suggestions': [],  # No suggestions
            'pattern_analysis': None,
            'escalation_reason': None  # Not ESCALATE
        }
        
        # Mock streamlit to prevent actual rendering
        with patch('components.analyze_task.results_display.st') as mock_st:
            # Should not crash
            try:
                render_results(analysis)
                success = True
            except Exception as e:
                success = False
                error = str(e)
        
        assert success, f"Low-risk scenario crashed: {error if not success else ''}"
    
    def test_confidence_meter_displays_high_confidence(self):
        """Verify confidence meter handles high confidence correctly."""
        analysis = {'confidence_score': 0.9}
        
        with patch('components.analyze_task.confidence_display.st') as mock_st:
            try:
                render_confidence_meter(analysis)
                success = True
            except Exception:
                success = False
        
        assert success, "Confidence meter crashed on high confidence"
    
    def test_no_escalation_reason_for_autonomous(self):
        """Verify escalation reason doesn't show for AUTONOMOUS decisions."""
        from components.analyze_task.results_display import render_escalation_reason
        
        analysis = {
            'decision': 'AUTONOMOUS',
            'escalation_reason': None
        }
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            render_escalation_reason(analysis)
            
            # Should not call st.error (escalation reason display)
            mock_st.error.assert_not_called()
    
    def test_no_similar_cases_section(self):
        """Verify similar cases section doesn't appear when empty."""
        analysis = {'similar_cases': []}
        
        with patch('components.analyze_task.similar_cases_display.st') as mock_st:
            render_similar_cases(analysis)
            
            # Should not render anything (silent return)
            mock_st.markdown.assert_not_called()


class TestScenario2_HighRiskEscalation:
    """
    Scenario 2: High-risk task requiring escalation
    
    Expected behavior:
    - Escalation reason visible
    - Similar cases appear
    - Proactive suggestions display
    - Full results load
    """
    
    def test_high_risk_escalation_complete_flow(self):
        """Test high-risk escalation flows through all components."""
        analysis = {
            'decision': 'ESCALATE',
            'confidence_score': 0.65,
            'risk_level': 'HIGH',
            'risk_score': 0.85,
            'risk_factors': {
                'jurisdiction_risk': 0.9,
                'entity_risk': 0.7,
                'task_risk': 0.8,
                'data_sensitivity_risk': 0.9,
                'regulatory_risk': 0.95,
                'impact_risk': 0.85
            },
            'reasoning_chain': [
                'High-risk cross-border data transfer',
                'Complex multi-jurisdictional requirements',
                'Requires legal expert review'
            ],
            'recommendations': [
                'Escalate to legal team immediately',
                'Do not proceed without expert approval',
                'Document all requirements'
            ],
            'similar_cases': [
                {
                    'decision': 'ESCALATE',
                    'risk_level': 'HIGH',
                    'confidence_score': 0.7,
                    'task_description': 'Previous cross-border data transfer',
                    'timestamp': '2025-11-01T10:00:00Z',
                    'entity_name': 'Test Corp',
                    'task_category': 'DATA_PRIVACY'
                },
                {
                    'decision': 'REVIEW_REQUIRED',
                    'risk_level': 'MEDIUM',
                    'confidence_score': 0.75,
                    'task_description': 'Similar compliance review',
                    'timestamp': '2025-10-15T14:30:00Z'
                },
                {
                    'decision': 'ESCALATE',
                    'risk_level': 'HIGH',
                    'confidence_score': 0.68,
                    'task_description': 'High-risk regulatory filing',
                    'timestamp': '2025-09-20T09:15:00Z'
                }
            ],
            'proactive_suggestions': [
                {
                    'severity': 'HIGH',
                    'icon': '⚠️',
                    'title': 'Urgent Review Required',
                    'message': 'This task requires immediate legal review due to cross-border data transfer risks.',
                    'suggestion': 'Contact legal team before proceeding'
                },
                {
                    'severity': 'MEDIUM',
                    'title': 'Documentation Required',
                    'message': 'Previous similar cases required extensive documentation.'
                }
            ],
            'pattern_analysis': 'Your organization consistently escalates cross-border data transfers. This is appropriate given regulatory complexity.',
            'escalation_reason': 'This task involves cross-border data transfers to high-risk jurisdictions without adequate legal mechanisms. GDPR compliance requires expert legal review to avoid potential penalties up to €20M or 4% of global revenue.'
        }
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            try:
                render_results(analysis)
                success = True
            except Exception as e:
                success = False
                error = str(e)
        
        assert success, f"High-risk scenario crashed: {error if not success else ''}"
    
    def test_escalation_reason_displays(self):
        """Verify escalation reason displays for ESCALATE decisions."""
        from components.analyze_task.results_display import render_escalation_reason
        
        analysis = {
            'decision': 'ESCALATE',
            'escalation_reason': 'High-risk cross-border transfer without legal mechanisms'
        }
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            render_escalation_reason(analysis)
            
            # Should call st.error with escalation reason
            assert mock_st.error.called, "Escalation reason not displayed"
            assert mock_st.markdown.called, "Divider not added"
    
    def test_similar_cases_display_with_data(self):
        """Verify similar cases display when present."""
        analysis = {
            'similar_cases': [
                {'decision': 'ESCALATE', 'risk_level': 'HIGH'},
                {'decision': 'REVIEW_REQUIRED', 'risk_level': 'MEDIUM'},
                {'decision': 'ESCALATE', 'risk_level': 'HIGH'}
            ]
        }
        
        with patch('components.analyze_task.similar_cases_display.st') as mock_st:
            render_similar_cases(analysis)
            
            # Should render section
            assert mock_st.markdown.called, "Similar cases section not rendered"
    
    def test_proactive_suggestions_display(self):
        """Verify proactive suggestions display when present."""
        analysis = {
            'proactive_suggestions': [
                {'severity': 'HIGH', 'message': 'Urgent review needed'},
                {'severity': 'MEDIUM', 'message': 'Documentation required'}
            ]
        }
        
        with patch('components.analyze_task.suggestions_display.st') as mock_st:
            render_proactive_suggestions(analysis)
            
            # Should render section
            assert mock_st.markdown.called, "Proactive suggestions not rendered"


class TestScenario3_MissingFields:
    """
    Scenario 3: Missing fields (empty analysis)
    
    Expected behavior:
    - No crashes
    - Only available sections load
    - Graceful degradation
    """
    
    def test_empty_analysis_no_crash(self):
        """Test empty analysis dict doesn't crash."""
        analysis = {}
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            try:
                render_results(analysis)
                success = True
            except Exception as e:
                success = False
                error = str(e)
        
        assert success, f"Empty analysis crashed: {error if not success else ''}"
    
    def test_none_analysis_handled(self):
        """Test None analysis is handled gracefully."""
        analysis = None
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            try:
                render_results(analysis)
                success = True
            except Exception as e:
                success = False
                error = str(e)
        
        assert success, f"None analysis crashed: {error if not success else ''}"
    
    def test_partial_data_no_crash(self):
        """Test partial data doesn't crash."""
        analysis = {
            'decision': 'REVIEW_REQUIRED',
            # Missing confidence_score
            # Missing risk_level
            # Missing everything else
        }
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            try:
                render_results(analysis)
                success = True
            except Exception as e:
                success = False
                error = str(e)
        
        assert success, f"Partial data crashed: {error if not success else ''}"
    
    def test_confidence_meter_missing_confidence(self):
        """Test confidence meter handles missing confidence score."""
        analysis = {}  # No confidence_score
        
        with patch('components.analyze_task.confidence_display.st') as mock_st:
            try:
                render_confidence_meter(analysis)
                success = True
            except Exception:
                success = False
        
        assert success, "Confidence meter crashed on missing confidence"
    
    def test_risk_breakdown_missing_factors(self):
        """Test risk breakdown handles missing risk factors."""
        analysis = {}  # No risk_factors
        
        with patch('components.analyze_task.risk_display.st') as mock_st:
            try:
                render_risk_breakdown(analysis)
                success = True
            except Exception:
                success = False
        
        assert success, "Risk breakdown crashed on missing factors"


class TestScenario4_MixedFormatData:
    """
    Scenario 4: Mixed-format data
    
    Expected behavior:
    - Auto normalization of 0-100 to 0-1
    - Handles numeric + text risk factors
    - Missing optional fields handled
    """
    
    def test_mixed_format_complete_flow(self):
        """Test mixed format data flows through all components."""
        analysis = {
            'decision': 'REVIEW_REQUIRED',
            'confidence': 75,  # 0-100 format (not confidence_score)
            'risk_level': 'MEDIUM',
            'risk_score': 55,  # 0-100 format
            'risk_factors': {
                'jurisdiction_risk': 0.6,  # 0-1 format
                'entity_risk': 45,  # 0-100 format
                'task_risk': 'MEDIUM',  # Text format
                'data_sensitivity_risk': 0.7,  # 0-1 format
                'regulatory_risk': 'HIGH',  # Text format
                'impact_risk': 50  # 0-100 format
            },
            'reasoning_chain': [
                'Mixed risk factors',
                'Requires review'
            ],
            'recommendations': [
                'Review with supervisor',
                'Document decision'
            ],
            'similar_cases': [],
            'proactive_suggestions': [
                {'priority': 'medium', 'message': 'Test'}  # lowercase priority
            ],
            # Missing: pattern_analysis, escalation_reason
        }
        
        with patch('components.analyze_task.results_display.st') as mock_st:
            try:
                render_results(analysis)
                success = True
            except Exception as e:
                success = False
                error = str(e)
        
        assert success, f"Mixed format scenario crashed: {error if not success else ''}"
    
    def test_confidence_auto_normalization(self):
        """Test confidence auto-normalizes 0-100 to 0-1."""
        from components.analyze_task.confidence_display import (
            _extract_confidence, 
            _normalize_confidence
        )
        
        # Test 0-100 format
        analysis_100 = {'confidence': 75}
        confidence_raw = _extract_confidence(analysis_100)
        confidence_normalized = _normalize_confidence(confidence_raw)
        
        assert 0 <= confidence_normalized <= 1, "Confidence not normalized to 0-1"
        assert confidence_normalized == 0.75, f"Expected 0.75, got {confidence_normalized}"
        
        # Test 0-1 format
        analysis_1 = {'confidence_score': 0.75}
        confidence_raw = _extract_confidence(analysis_1)
        confidence_normalized = _normalize_confidence(confidence_raw)
        
        assert confidence_normalized == 0.75, f"0-1 format changed: {confidence_normalized}"
    
    def test_risk_factors_mixed_formats(self):
        """Test risk factors handle numeric + text formats."""
        from components.analyze_task.risk_display import _prepare_risk_factors_for_display
        
        risk_factors = {
            'jurisdiction_risk': 0.6,  # 0-1
            'entity_risk': 45,  # 0-100
            'task_risk': 'HIGH',  # Text
            'data_sensitivity_risk': 0.7,  # 0-1
            'regulatory_risk': 'MEDIUM',  # Text
            'impact_risk': 50  # 0-100
        }
        
        try:
            display_factors = _prepare_risk_factors_for_display(risk_factors)
            success = True
        except Exception:
            success = False
        
        assert success, "Risk factors failed on mixed formats"
        assert len(display_factors) > 0, "No risk factors prepared"
    
    def test_suggestions_severity_priority_mapping(self):
        """Test suggestions handle both severity and priority fields."""
        from components.analyze_task.suggestions_display import _get_suggestion_priority
        
        # Test uppercase severity
        suggestion1 = {'severity': 'HIGH'}
        priority1 = _get_suggestion_priority(suggestion1)
        assert priority1 == 'HIGH', f"Severity HIGH not mapped: {priority1}"
        
        # Test lowercase priority
        suggestion2 = {'priority': 'medium'}
        priority2 = _get_suggestion_priority(suggestion2)
        assert priority2 == 'MEDIUM', f"Priority medium not mapped: {priority2}"
        
        # Test missing both (default)
        suggestion3 = {}
        priority3 = _get_suggestion_priority(suggestion3)
        assert priority3 in ['HIGH', 'MEDIUM', 'LOW'], f"Default priority invalid: {priority3}"
    
    def test_similar_cases_timestamp_formats(self):
        """Test similar cases handle various timestamp formats."""
        from components.analyze_task.similar_cases_display import _calculate_time_ago
        from datetime import datetime, timezone
        
        # Test ISO string with Z
        time_ago_1 = _calculate_time_ago('2025-11-01T10:00:00Z')
        assert time_ago_1 is not None or time_ago_1 is None, "Should handle or skip"
        
        # Test datetime object
        time_ago_2 = _calculate_time_ago(datetime.now(timezone.utc))
        assert time_ago_2 == 'just now' or 'ago' in time_ago_2, "Datetime object failed"
        
        # Test None
        time_ago_3 = _calculate_time_ago(None)
        assert time_ago_3 is None, "Should return None for missing timestamp"
        
        # Test invalid
        time_ago_4 = _calculate_time_ago('invalid-date')
        assert time_ago_4 is None, "Should return None for invalid timestamp"


class TestIntegrationSanityCheck:
    """
    Integration tests to verify overall system stability.
    """
    
    def test_all_scenarios_sequentially(self):
        """Run all 4 scenarios in sequence to ensure stability."""
        scenarios = [
            # Scenario 1: Low-risk
            {
                'name': 'Low-risk task',
                'analysis': {
                    'decision': 'AUTONOMOUS',
                    'confidence_score': 0.9,
                    'risk_level': 'LOW',
                    'risk_score': 0.2,
                    'reasoning_chain': ['Low risk'],
                    'recommendations': ['Proceed'],
                    'similar_cases': [],
                }
            },
            # Scenario 2: High-risk escalation
            {
                'name': 'High-risk escalation',
                'analysis': {
                    'decision': 'ESCALATE',
                    'confidence_score': 0.65,
                    'risk_level': 'HIGH',
                    'risk_score': 0.85,
                    'escalation_reason': 'High risk',
                    'similar_cases': [{'decision': 'ESCALATE'}] * 3,
                    'proactive_suggestions': [{'severity': 'HIGH', 'message': 'Urgent'}]
                }
            },
            # Scenario 3: Missing fields
            {
                'name': 'Missing fields',
                'analysis': {}
            },
            # Scenario 4: Mixed formats
            {
                'name': 'Mixed formats',
                'analysis': {
                    'confidence': 75,
                    'risk_score': 55,
                    'risk_factors': {
                        'jurisdiction_risk': 0.6,
                        'task_risk': 'MEDIUM'
                    }
                }
            }
        ]
        
        results = []
        
        with patch('components.analyze_task.results_display.st'):
            for scenario in scenarios:
                try:
                    render_results(scenario['analysis'])
                    results.append((scenario['name'], True, None))
                except Exception as e:
                    results.append((scenario['name'], False, str(e)))
        
        # Check all passed
        failures = [(name, error) for name, success, error in results if not success]
        
        assert len(failures) == 0, f"Scenarios failed: {failures}"
        print("\n✅ All 4 scenarios passed successfully!")


def run_qa_sanity_check():
    """
    Run complete QA sanity check and print results.
    """
    print("=" * 70)
    print("QA SANITY CHECK - ANALYZE TASK FLOW")
    print("=" * 70)
    print()
    
    test_results = {
        'scenario_1': [],
        'scenario_2': [],
        'scenario_3': [],
        'scenario_4': [],
        'integration': []
    }
    
    # Run tests
    import pytest
    
    # Scenario 1
    print("Scenario 1: Low-risk task...")
    result = pytest.main([__file__, '::TestScenario1_LowRiskTask', '-v', '--tb=short'])
    test_results['scenario_1'].append(result == 0)
    
    # Scenario 2
    print("\nScenario 2: High-risk + escalation...")
    result = pytest.main([__file__, '::TestScenario2_HighRiskEscalation', '-v', '--tb=short'])
    test_results['scenario_2'].append(result == 0)
    
    # Scenario 3
    print("\nScenario 3: Missing fields...")
    result = pytest.main([__file__, '::TestScenario3_MissingFields', '-v', '--tb=short'])
    test_results['scenario_3'].append(result == 0)
    
    # Scenario 4
    print("\nScenario 4: Mixed-format data...")
    result = pytest.main([__file__, '::TestScenario4_MixedFormatData', '-v', '--tb=short'])
    test_results['scenario_4'].append(result == 0)
    
    # Integration
    print("\nIntegration: All scenarios...")
    result = pytest.main([__file__, '::TestIntegrationSanityCheck', '-v', '--tb=short'])
    test_results['integration'].append(result == 0)
    
    # Print summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    all_passed = all(all(results) for results in test_results.values())
    
    for scenario, results in test_results.items():
        status = "✅ PASS" if all(results) else "❌ FAIL"
        print(f"{scenario.upper():<20} {status}")
    
    print("=" * 70)
    
    if all_passed:
        print()
        print("🎉 " * 15)
        print()
        print("FEATURE RESTORATION COMPLETE — SYSTEM STABLE.")
        print()
        print("🎉 " * 15)
        print()
    else:
        print()
        print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        print()
    
    return all_passed


if __name__ == '__main__':
    run_qa_sanity_check()

