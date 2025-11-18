# End-to-End Tests with Playwright

This directory contains Playwright tests for the full application flow.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Running Tests

Run all E2E tests:
```bash
pytest tests/e2e/ -v
```

Run a specific test:
```bash
pytest tests/e2e/test_app_flow.py::test_login -v
```

## Prerequisites

Before running tests, ensure:
1. Backend is running on `http://127.0.0.1:8000` (or tests will start it automatically)
2. Frontend is running on `http://localhost:8501` (or tests will start it automatically)

## Test Coverage

- ✅ Login
- ✅ Analyze Task
- ✅ Save Decision
- ✅ Load History (Audit Trail)
- ✅ View Insights
- ✅ Logout

## Notes

- Tests will automatically start backend/frontend if not running
- Tests use headless browser by default
- Adjust selectors in `test_app_flow.py` if UI changes

