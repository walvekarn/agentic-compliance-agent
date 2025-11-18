PYTHON=python3

# -------- BACKEND --------

backend:
	uvicorn backend.main:app --host 0.0.0.0 --port 8000

# If your backend entry point is different, tell me and I will adjust.

# -------- DASHBOARD --------

dashboard:
	cd frontend && $(PYTHON) -m streamlit run Home.py --server.port=8501

# -------- KILL ALL UVICORN + STREAMLIT --------

kill:
	@echo "🛑 Stopping services..."
	pkill -f "uvicorn" || true
	pkill -f "streamlit" || true
	@echo "✅ All services stopped"

# -------- START BOTH --------

start:
	@echo "🚀 Starting backend and dashboard..."
	@echo "🛑 Stopping any existing services..."
	@pkill -f "uvicorn.*backend.main:app" || true
	@pkill -f "streamlit.*Home.py" || true
	@sleep 1
	@echo "✅ Starting backend..."
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 & echo $$! > .backend.pid
	@echo "⏳ Waiting for backend to start..."
	@sleep 2
	@echo "✅ Starting dashboard..."
	cd frontend && $(PYTHON) -m streamlit run Home.py --server.port=8501

# -------- RESTART BOTH --------

restart:
	@echo "🔄 Restarting services..."
	@$(MAKE) kill
	@sleep 1
	@$(MAKE) start

# -------- INSTALL --------

install:
	pip install -r requirements.txt

# -------- CLEAN CACHE --------

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "🧹 Cache cleaned"

# -------- TEST --------

test:
	pytest -q

test-e2e:
	@echo "Running E2E tests with Playwright..."
	@echo "Make sure backend and frontend are running, or tests will start them automatically"
	pytest tests/e2e/ -v -m e2e

test-e2e-setup:
	@echo "Installing Playwright browsers..."
	playwright install chromium

# -------- FORMAT --------

format:
	black backend frontend tests

.PHONY: help backend dashboard start kill restart test clean

# Colors for output
BLUE=\033[0;34m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

help:
	@echo "$(BLUE)🤖 AI Agentic Compliance Assistant - Management Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Available commands:$(NC)"
	@echo "  $(YELLOW)make backend$(NC)    - Start FastAPI backend only (port 8000)"
	@echo "  $(YELLOW)make dashboard$(NC)  - Start Streamlit dashboard only (port 8501)"
	@echo "  $(YELLOW)make start$(NC)      - Start both backend and dashboard"
	@echo "  $(YELLOW)make kill$(NC)       - Kill processes on ports 8000 and 8501"
	@echo "  $(YELLOW)make restart$(NC)    - Kill and restart both services"
	@echo "  $(YELLOW)make test$(NC)       - Run test suite"
	@echo "  $(YELLOW)make clean$(NC)      - Clean up cache and temp files"
	@echo "  $(YELLOW)make migrate$(NC)    - Run Alembic upgrade to head"
	@echo "  $(YELLOW)make revision message=\"<msg>\"$(NC) - Create Alembic revision"
	@echo "  $(YELLOW)make help$(NC)       - Show this help message"
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  1. Activate virtual environment: source venv/bin/activate"
	@echo "  2. Start services: make start"
	@echo "  3. Access dashboard: http://localhost:8501"
	@echo "  4. Access API docs: http://localhost:8000/docs"

 
