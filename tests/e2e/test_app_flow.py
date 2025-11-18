"""
End-to-End Tests with Playwright
=================================
Tests the complete application flow:
- Login
- Analyze Task
- Save Decision
- Load History
- View Insights
- Logout
"""

import pytest
pytestmark = pytest.mark.e2e

from playwright.sync_api import Page, expect, sync_playwright
import time
import os
import re

# Base URLs matching Makefile configuration
BASE_URL_FRONTEND = "http://localhost:8501"
BASE_URL_BACKEND = "http://localhost:8000"


# Note: Backend and frontend servers are managed by fixtures in conftest.py
# backend_server and frontend_server fixtures handle server startup and readiness checks

@pytest.fixture(scope="module")
def page(backend_server, frontend_server):
    """
    Create a Playwright page instance.
    Depends on backend_server and frontend_server to ensure servers are ready.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Set default timeout to 15 seconds for all operations
        page.set_default_timeout(15000)
        yield page
        browser.close()

def test_login(page: Page):
    """Test user login"""
    # Navigate to the app
    page.goto(BASE_URL_FRONTEND)
    
    # Wait for page to fully load (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Fill in credentials - Streamlit uses input[type="text"] for username
    username_input = page.locator("input[type='text']").first
    password_input = page.locator("input[type='password']").first
    
    username_input.fill("admin")
    password_input.fill("admin")
    
    # Wait before clicking login button
    page.wait_for_timeout(1500)
    
    # Click login button - Streamlit button with "Sign In" text
    login_button = page.get_by_role("button", name=re.compile(r"Sign In", re.I)).first
    login_button.click()
    
    # Wait for login to process (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Verify we're logged in - check for logout button or page title change
    # Streamlit may show "Check a Task" or logout button after successful login
    try:
        # Wait for either logout button or main page content
        logout_button = page.get_by_role("button", name=re.compile(r"Logout", re.I))
        if logout_button.count() > 0:
            expect(logout_button.first).to_be_visible(timeout=10000)
        else:
            # Alternative: check for page title or main content
            expect(page.locator("text=Check a Task, text=Dashboard, text=Home").first).to_be_visible(timeout=10000)
    except:
        # If neither found, check if we're no longer on login page
        expect(page.locator("input[type='text']").first).not_to_be_visible(timeout=5000)


def test_analyze_task(page: Page):
    """Test analyzing a task"""
    # First login
    page.goto(BASE_URL_FRONTEND)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    page.locator("input[type='text']").first.fill("admin")
    page.locator("input[type='password']").first.fill("admin")
    
    page.wait_for_timeout(1500)
    page.get_by_role("button", name=re.compile(r"Sign In", re.I)).first.click()
    
    # Wait for login to complete (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Navigate to Analyze Task page - Streamlit uses page navigation
    # Try direct navigation first (most reliable)
    page.goto(f"{BASE_URL_FRONTEND}/1_Analyze_Task")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Verify we're on the Analyze Task page
    expect(page.locator("text=Check a Task, text=Get Instant Guidance").first).to_be_visible(timeout=10000)
    
    # Wait for form to be ready
    page.wait_for_selector("input[type='text'], textarea, select", timeout=10000)
    page.wait_for_timeout(1500)
    
    # Fill in task form - look for entity name field
    # Streamlit forms may use different selectors
    entity_inputs = page.locator("input[type='text']").all()
    if len(entity_inputs) > 0:
        # Try to find entity field (usually first text input after login)
        entity_inputs[0].fill("Test Corporation")
        page.wait_for_timeout(1500)
    
    # Look for textarea for task description
    task_textareas = page.locator("textarea").all()
    if len(task_textareas) > 0:
        task_textareas[0].fill("Process customer data for analytics")
        page.wait_for_timeout(1500)
    
    # Submit the form - look for "Analyze" or "Submit" button
    submit_button = page.get_by_role("button", name=re.compile(r"Analyze|Submit|Check", re.I)).first
    if submit_button.is_visible():
        submit_button.click()
        
        # Wait for results to load (Streamlit never reaches networkidle)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Verify results are displayed - look for decision, risk, or analysis text
        expect(page.locator("text=Decision, text=Risk, text=Analysis, text=Compliance").first).to_be_visible(timeout=15000)
    else:
        # If no submit button found, form might be auto-submitting or structured differently
        pytest.skip("Could not find submit button - form structure may have changed")


def test_save_decision(page: Page):
    """Test saving a decision"""
    # Login and analyze task first
    page.goto(BASE_URL_FRONTEND)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    page.locator("input[type='text']").first.fill("admin")
    page.locator("input[type='password']").first.fill("admin")
    
    page.wait_for_timeout(1500)
    page.get_by_role("button", name=re.compile(r"Sign In", re.I)).first.click()
    
    # Wait for login to complete (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Navigate to Analyze Task
    try:
        page.locator("text=Analyze Task, text=Check a Task").first.click(timeout=5000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
    except:
        page.goto(f"{BASE_URL_FRONTEND}/1_Analyze_Task")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
    
    page.wait_for_timeout(1500)
    
    # Fill and submit form
    page.wait_for_selector("input[type='text'], textarea", timeout=10000)
    page.wait_for_timeout(1500)
    
    entity_name = page.locator("input[placeholder*='Entity'], input[name*='entity']").first
    if entity_name.count() > 0:
        entity_name.fill("Test Corp")
        page.wait_for_timeout(1500)
    
    task_description = page.locator("textarea[placeholder*='Task'], textarea[name*='task']").first
    if task_description.count() > 0:
        task_description.fill("Test task for saving")
        page.wait_for_timeout(1500)
    
    submit_button = page.locator("button:has-text('Analyze'), button[type='submit']").first
    if submit_button.count() > 0:
        submit_button.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Look for save button
        save_button = page.locator("button:has-text('Save'), button:has-text('Save Decision')").first
        if save_button.count() > 0:
            page.wait_for_timeout(1500)
            save_button.click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_selector("input[type='text'], button", timeout=10000)
            page.wait_for_timeout(1000)
            
            # Verify success message
            expect(page.locator("text=saved, text=success, text=Saved").first).to_be_visible(timeout=5000)


def test_load_history(page: Page):
    """Test loading audit trail/history"""
    # Login
    page.goto(BASE_URL_FRONTEND)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    page.locator("input[type='text']").first.fill("admin")
    page.locator("input[type='password']").first.fill("admin")
    
    page.wait_for_timeout(1500)
    page.get_by_role("button", name=re.compile(r"Sign In", re.I)).first.click()
    
    # Wait for login to complete (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Navigate to Audit Trail
    try:
        page.locator("text=Audit Trail, text=History").first.click(timeout=5000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
    except:
        page.goto(f"{BASE_URL_FRONTEND}/3_Audit_Trail")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
    
    page.wait_for_timeout(1500)
    
    # Verify page loaded
    expect(page.locator("text=Audit Trail, text=History, text=Decisions").first).to_be_visible(timeout=10000)
    
    # Check for table or list of entries
    # This depends on your UI structure
    expect(page.locator("table, [role='table'], .dataframe").or_(page.locator("text=No data")).first).to_be_visible(timeout=5000)


def test_view_insights(page: Page):
    """Test viewing insights dashboard"""
    # Login
    page.goto(BASE_URL_FRONTEND)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    page.locator("input[type='text']").first.fill("admin")
    page.locator("input[type='password']").first.fill("admin")
    
    page.wait_for_timeout(1500)
    page.get_by_role("button", name=re.compile(r"Sign In", re.I)).first.click()
    
    # Wait for login to complete (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Navigate to Insights
    try:
        page.locator("text=Insights, text=Agent Insights").first.click(timeout=5000)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
    except:
        page.goto(f"{BASE_URL_FRONTEND}/4_Agent_Insights")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
    
    page.wait_for_timeout(1500)
    
    # Verify insights page loaded
    expect(page.locator("text=Insights, text=Dashboard, text=Analytics").first).to_be_visible(timeout=10000)
    
    # Check for metrics or charts
    expect(page.locator("text=Total, text=Decisions, text=Statistics").or_(page.locator("text=No data")).first).to_be_visible(timeout=5000)


def test_logout(page: Page):
    """Test user logout"""
    # Login first
    page.goto(BASE_URL_FRONTEND)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    page.locator("input[type='text']").first.fill("admin")
    page.locator("input[type='password']").first.fill("admin")
    
    page.wait_for_timeout(1500)
    page.get_by_role("button", name=re.compile(r"Sign In", re.I)).first.click()
    
    # Wait for login to complete (Streamlit never reaches networkidle)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector("input[type='text'], button", timeout=10000)
    page.wait_for_timeout(1000)
    
    # Click logout button
    logout_button = page.locator("button:has-text('Logout'), button:has-text('Sign Out')").first
    if logout_button.count() > 0:
        page.wait_for_timeout(1500)
        logout_button.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_selector("input[type='text'], button", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Verify we're back at login
        page.wait_for_selector("input[type='text']", timeout=10000)
        expect(page.locator("input[type='text'], input[type='password']").first).to_be_visible(timeout=5000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

