"""
Feature Contract Tests
======================
Ensures render_results() orchestrator calls ALL sub-components.

This test prevents accidental feature removals during refactoring
by verifying the "contract" that render_results() must always call
each registered sub-component.

WHY THIS TEST EXISTS:
---------------------
During a previous refactoring, 43 features were accidentally removed
from the UI. This test ensures it never happens again by explicitly
checking that every component is called.

See: FEATURE_INVENTORY.md for the full audit results.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add frontend directory to path
frontend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(frontend_dir))

from components.analyze_task.results_display import render_results


class TestRenderResultsContract:
    """
    Contract tests for render_results() orchestrator.
    
    These tests ensure that ALL registered sub-components are called,
    preventing accidental feature removals during refactoring.
    """
    
    def test_render_results_calls_all_core_components(self, monkeypatch):
        """
        Test that render_results() calls all P0 core components.
        
        Core components (P0 - Critical):
        - render_decision_banner
        - render_confidence_meter (imported from confidence_display)
        - render_risk_level_display
        """
        # Create fake analysis data
        fake_analysis = {
            'decision': 'AUTONOMOUS',
            'confidence_score': 0.85,
            'risk_level': 'LOW'
        }
        
        # Create mock functions to track calls
        mock_decision_banner = MagicMock()
        mock_confidence_meter = MagicMock()
        mock_risk_level = MagicMock()
        
        # Patch the components in results_display module
        with patch('components.analyze_task.results_display.render_decision_banner', mock_decision_banner), \
             patch('components.analyze_task.results_display.render_confidence_meter', mock_confidence_meter), \
             patch('components.analyze_task.results_display.render_risk_level_display', mock_risk_level):
            
            # Call render_results
            render_results(fake_analysis)
            
            # Assert all core components were called
            assert mock_decision_banner.called, "render_decision_banner was not called"
            assert mock_confidence_meter.called, "render_confidence_meter was not called"
            assert mock_risk_level.called, "render_risk_level_display was not called"
            
            # Verify they were called with the analysis dict
            mock_decision_banner.assert_called_once_with(fake_analysis)
            mock_confidence_meter.assert_called_once_with(fake_analysis)
            mock_risk_level.assert_called_once_with(fake_analysis)
    
    def test_render_results_calls_all_agentic_components(self, monkeypatch):
        """
        Test that render_results() calls all agentic AI components.
        
        Agentic components (P0 - Critical):
        - render_proactive_suggestions (imported from suggestions_display)
        - render_similar_cases (imported from similar_cases_display)
        - render_pattern_analysis
        """
        fake_analysis = {
            'proactive_suggestions': [],
            'similar_cases': [],
            'pattern_analysis': 'Test pattern'
        }
        
        mock_suggestions = MagicMock()
        mock_similar_cases = MagicMock()
        mock_pattern = MagicMock()
        
        with patch('components.analyze_task.results_display.render_proactive_suggestions', mock_suggestions), \
             patch('components.analyze_task.results_display.render_similar_cases', mock_similar_cases), \
             patch('components.analyze_task.results_display.render_pattern_analysis', mock_pattern):
            
            render_results(fake_analysis)
            
            assert mock_suggestions.called, "render_proactive_suggestions was not called"
            assert mock_similar_cases.called, "render_similar_cases was not called"
            assert mock_pattern.called, "render_pattern_analysis was not called"
    
    def test_render_results_calls_all_analysis_components(self, monkeypatch):
        """
        Test that render_results() calls all detailed analysis components.
        
        Analysis components (P0/P1):
        - render_risk_breakdown (imported from risk_display)
        - render_reasoning_chain
        - render_recommendations
        - render_action_plan
        - render_stakeholders
        - render_escalation_reason
        """
        fake_analysis = {
            'risk_factors': {},
            'reasoning_chain': [],
            'recommendations': [],
            'decision': 'ESCALATE',
            'escalation_reason': 'Test reason'
        }
        
        mock_risk = MagicMock()
        mock_reasoning = MagicMock()
        mock_recommendations = MagicMock()
        mock_action_plan = MagicMock()
        mock_stakeholders = MagicMock()
        mock_escalation = MagicMock()
        
        with patch('components.analyze_task.results_display.render_risk_breakdown', mock_risk), \
             patch('components.analyze_task.results_display.render_reasoning_chain', mock_reasoning), \
             patch('components.analyze_task.results_display.render_recommendations', mock_recommendations), \
             patch('components.analyze_task.results_display.render_action_plan', mock_action_plan), \
             patch('components.analyze_task.results_display.render_stakeholders', mock_stakeholders), \
             patch('components.analyze_task.results_display.render_escalation_reason', mock_escalation):
            
            render_results(fake_analysis)
            
            assert mock_risk.called, "render_risk_breakdown was not called"
            assert mock_reasoning.called, "render_reasoning_chain was not called"
            assert mock_recommendations.called, "render_recommendations was not called"
            assert mock_action_plan.called, "render_action_plan was not called"
            assert mock_stakeholders.called, "render_stakeholders was not called"
            assert mock_escalation.called, "render_escalation_reason was not called"
    
    def test_render_results_calls_all_transparency_components(self, monkeypatch):
        """
        Test that render_results() calls all AI transparency components.
        
        Transparency components (P0/P2):
        - render_confidence_warnings
        - render_agent_explainability
        - render_counterfactual_explanations
        """
        fake_analysis = {
            'confidence_score': 0.5,
            'risk_factors': {}
        }
        
        mock_warnings = MagicMock()
        mock_explainability = MagicMock()
        mock_counterfactual = MagicMock()
        
        with patch('components.analyze_task.results_display.render_confidence_warnings', mock_warnings), \
             patch('components.analyze_task.results_display.render_agent_explainability', mock_explainability), \
             patch('components.analyze_task.results_display.render_counterfactual_explanations', mock_counterfactual):
            
            render_results(fake_analysis)
            
            assert mock_warnings.called, "render_confidence_warnings was not called"
            assert mock_explainability.called, "render_agent_explainability was not called"
            assert mock_counterfactual.called, "render_counterfactual_explanations was not called"
    
    def test_render_results_calls_all_interaction_components(self, monkeypatch):
        """
        Test that render_results() calls all user interaction components.
        
        Interaction components (P0/P1):
        - render_feedback_form
        - render_export_section
        - render_chat_integration
        """
        fake_analysis = {
            'decision': 'REVIEW_REQUIRED'
        }
        
        mock_feedback = MagicMock()
        mock_export = MagicMock()
        mock_chat = MagicMock()
        
        with patch('components.analyze_task.results_display.render_feedback_form', mock_feedback), \
             patch('components.analyze_task.results_display.render_export_section', mock_export), \
             patch('components.analyze_task.results_display.render_chat_integration', mock_chat):
            
            render_results(fake_analysis)
            
            assert mock_feedback.called, "render_feedback_form was not called"
            assert mock_export.called, "render_export_section was not called"
            assert mock_chat.called, "render_chat_integration was not called"
    
    def test_render_results_calls_all_components_in_sequence(self, monkeypatch):
        """
        Integration test: Verify ALL components are called in a single pass.
        
        This is the master contract test that ensures no component is
        accidentally removed from the orchestrator.
        """
        fake_analysis = {
            'decision': 'REVIEW_REQUIRED',
            'confidence_score': 0.75,
            'risk_level': 'MEDIUM',
            'risk_factors': {},
            'reasoning_chain': [],
            'recommendations': [],
            'proactive_suggestions': [],
            'similar_cases': [],
            'pattern_analysis': 'Test',
            'escalation_reason': None
        }
        
        # Create mocks for ALL components
        mocks = {
            'decision_banner': MagicMock(),
            'confidence_meter': MagicMock(),
            'risk_level': MagicMock(),
            'proactive_suggestions': MagicMock(),
            'similar_cases': MagicMock(),
            'pattern_analysis': MagicMock(),
            'risk_breakdown': MagicMock(),
            'reasoning_chain': MagicMock(),
            'recommendations': MagicMock(),
            'action_plan': MagicMock(),
            'stakeholders': MagicMock(),
            'escalation_reason': MagicMock(),
            'confidence_warnings': MagicMock(),
            'agent_explainability': MagicMock(),
            'counterfactual': MagicMock(),
            'feedback_form': MagicMock(),
            'export_section': MagicMock(),
            'chat_integration': MagicMock()
        }
        
        # Patch ALL components
        with patch('components.analyze_task.results_display.render_decision_banner', mocks['decision_banner']), \
             patch('components.analyze_task.results_display.render_confidence_meter', mocks['confidence_meter']), \
             patch('components.analyze_task.results_display.render_risk_level_display', mocks['risk_level']), \
             patch('components.analyze_task.results_display.render_proactive_suggestions', mocks['proactive_suggestions']), \
             patch('components.analyze_task.results_display.render_similar_cases', mocks['similar_cases']), \
             patch('components.analyze_task.results_display.render_pattern_analysis', mocks['pattern_analysis']), \
             patch('components.analyze_task.results_display.render_risk_breakdown', mocks['risk_breakdown']), \
             patch('components.analyze_task.results_display.render_reasoning_chain', mocks['reasoning_chain']), \
             patch('components.analyze_task.results_display.render_recommendations', mocks['recommendations']), \
             patch('components.analyze_task.results_display.render_action_plan', mocks['action_plan']), \
             patch('components.analyze_task.results_display.render_stakeholders', mocks['stakeholders']), \
             patch('components.analyze_task.results_display.render_escalation_reason', mocks['escalation_reason']), \
             patch('components.analyze_task.results_display.render_confidence_warnings', mocks['confidence_warnings']), \
             patch('components.analyze_task.results_display.render_agent_explainability', mocks['agent_explainability']), \
             patch('components.analyze_task.results_display.render_counterfactual_explanations', mocks['counterfactual']), \
             patch('components.analyze_task.results_display.render_feedback_form', mocks['feedback_form']), \
             patch('components.analyze_task.results_display.render_export_section', mocks['export_section']), \
             patch('components.analyze_task.results_display.render_chat_integration', mocks['chat_integration']):
            
            # Call render_results
            render_results(fake_analysis)
            
            # Assert EVERY component was called
            for component_name, mock_func in mocks.items():
                assert mock_func.called, f"render_{component_name} was not called - FEATURE MISSING!"
                mock_func.assert_called_once_with(fake_analysis)
    
    def test_render_results_handles_empty_analysis(self, monkeypatch):
        """
        Test that render_results() gracefully handles empty analysis dict.
        
        This ensures the orchestrator doesn't crash on missing data.
        """
        empty_analysis = {}
        
        # Should not raise any exceptions
        # Components are responsible for their own graceful degradation
        mock_decision = MagicMock()
        
        with patch('components.analyze_task.results_display.render_decision_banner', mock_decision):
            render_results(empty_analysis)
            
            # Should still call components (they handle missing data)
            assert mock_decision.called
    
    def test_render_results_rejects_none_analysis(self, monkeypatch):
        """
        Test that render_results() handles None analysis gracefully.
        """
        # render_results should handle None by showing warning and returning
        # Components should NOT be called when analysis is None
        mock_decision = MagicMock()
        
        with patch('components.analyze_task.results_display.render_decision_banner', mock_decision):
            render_results(None)
            
            # Should not call components when analysis is None
            assert not mock_decision.called, "Components should not be called when analysis is None"


class TestComponentCallOrder:
    """
    Tests to ensure components are called in the correct order.
    
    The order matters for UX:
    1. Core decision info first
    2. Agentic features (proactive, memory)
    3. Detailed analysis
    4. Transparency features
    5. User interaction
    """
    
    def test_decision_banner_called_before_other_components(self, monkeypatch):
        """
        Verify decision banner is called first (user's primary answer).
        """
        fake_analysis = {'decision': 'AUTONOMOUS'}
        call_order = []
        
        def track_decision(*args):
            call_order.append('decision_banner')
        
        def track_confidence(*args):
            call_order.append('confidence_meter')
        
        with patch('components.analyze_task.results_display.render_decision_banner', track_decision), \
             patch('components.analyze_task.results_display.render_confidence_meter', track_confidence):
            
            render_results(fake_analysis)
            
            assert call_order[0] == 'decision_banner', "Decision banner should be called first"
            assert 'confidence_meter' in call_order, "Confidence meter should be called"
    
    def test_proactive_suggestions_called_before_detailed_analysis(self, monkeypatch):
        """
        Verify proactive suggestions appear before detailed analysis.
        
        Proactive suggestions should catch user's attention early.
        """
        fake_analysis = {}
        call_order = []
        
        def track_suggestions(*args):
            call_order.append('proactive_suggestions')
        
        def track_reasoning(*args):
            call_order.append('reasoning_chain')
        
        with patch('components.analyze_task.results_display.render_proactive_suggestions', track_suggestions), \
             patch('components.analyze_task.results_display.render_reasoning_chain', track_reasoning):
            
            render_results(fake_analysis)
            
            # Proactive should come before reasoning
            if 'proactive_suggestions' in call_order and 'reasoning_chain' in call_order:
                assert call_order.index('proactive_suggestions') < call_order.index('reasoning_chain'), \
                    "Proactive suggestions should be called before detailed reasoning"


class TestContractDocumentation:
    """
    Tests that verify the contract is properly documented.
    
    These tests ensure future developers understand the importance
    of the orchestrator contract.
    """
    
    def test_render_results_has_clear_documentation(self):
        """
        Verify render_results() has clear documentation about its role.
        """
        from components.analyze_task.results_display import render_results
        
        docstring = render_results.__doc__
        assert docstring is not None, "render_results must have a docstring"
        assert 'orchestrator' in docstring.lower() or 'orchestrate' in docstring.lower(), \
            "Documentation should mention orchestration role"
    
    def test_results_display_module_has_architecture_notes(self):
        """
        Verify the module has notes about the architecture.
        """
        import components.analyze_task.results_display as module
        
        module_doc = module.__doc__
        assert module_doc is not None, "Module should have documentation"


# =============================================================================
# REGRESSION TESTS
# =============================================================================

class TestFeatureRegressionPrevention:
    """
    Specific tests to prevent known regressions from the past.
    
    Based on FEATURE_INVENTORY.md audit results.
    """
    
    def test_similar_cases_not_accidentally_removed(self, monkeypatch):
        """
        Regression test: Similar cases display was missing in refactored UI.
        
        This was a P0 critical agentic feature that was accidentally removed.
        """
        fake_analysis = {'similar_cases': [{'decision': 'AUTONOMOUS'}]}
        mock_similar = MagicMock()
        
        with patch('components.analyze_task.results_display.render_similar_cases', mock_similar):
            render_results(fake_analysis)
            
            assert mock_similar.called, \
                "REGRESSION: Similar cases display is missing! This is a P0 agentic feature."
    
    def test_proactive_suggestions_not_accidentally_removed(self, monkeypatch):
        """
        Regression test: Proactive suggestions were missing in refactored UI.
        
        This was a P0 critical agentic feature that was accidentally removed.
        """
        fake_analysis = {'proactive_suggestions': [{'severity': 'HIGH'}]}
        mock_suggestions = MagicMock()
        
        with patch('components.analyze_task.results_display.render_proactive_suggestions', mock_suggestions):
            render_results(fake_analysis)
            
            assert mock_suggestions.called, \
                "REGRESSION: Proactive suggestions are missing! This is a P0 agentic feature."
    
    def test_risk_breakdown_not_accidentally_removed(self, monkeypatch):
        """
        Regression test: Risk breakdown was missing in refactored UI.
        
        This was a P1 important feature that was accidentally removed.
        """
        fake_analysis = {'risk_factors': {'jurisdiction_risk': 0.5}}
        mock_risk = MagicMock()
        
        with patch('components.analyze_task.results_display.render_risk_breakdown', mock_risk):
            render_results(fake_analysis)
            
            assert mock_risk.called, \
                "REGRESSION: Risk breakdown is missing! This is a P1 feature."


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

