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
	@echo "  $(YELLOW)make help$(NC)       - Show this help message"
	@echo ""
	@echo "$(BLUE)Quick Start:$(NC)"
	@echo "  1. Activate virtual environment: source venv/bin/activate"
	@echo "  2. Start services: make start"
	@echo "  3. Access dashboard: http://localhost:8501"
	@echo "  4. Access API docs: http://localhost:8000/docs"

backend:
	@echo "$(GREEN)🚀 Starting FastAPI backend on port 8000...$(NC)"
	@python3 main.py

dashboard:
	@echo "$(GREEN)🎨 Starting Streamlit dashboard on port 8501...$(NC)"
	@cd dashboard && python3 -m streamlit run Home.py --server.port=8501

start:
	@echo "$(GREEN)🚀 Starting backend and dashboard...$(NC)"
	@echo "$(YELLOW)Note: Backend will start in background, dashboard in foreground$(NC)"
	@echo ""
	@python3 main.py > backend.log 2>&1 & echo $$! > .backend.pid
	@sleep 3
	@echo "$(GREEN)✅ Backend started (PID: $$(cat .backend.pid))$(NC)"
	@echo "$(GREEN)📊 Starting dashboard...$(NC)"
	@echo ""
	@cd dashboard && python3 -m streamlit run Home.py --server.port=8501

kill:
	@echo "$(YELLOW)🛑 Stopping services...$(NC)"
	@if [ -f .backend.pid ]; then \
		kill $$(cat .backend.pid) 2>/dev/null || true; \
		rm -f .backend.pid; \
		echo "$(GREEN)✅ Backend stopped$(NC)"; \
	fi
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "$(YELLOW)No process on port 8000$(NC)"
	@lsof -ti:8501 | xargs kill -9 2>/dev/null || echo "$(YELLOW)No process on port 8501$(NC)"
	@echo "$(GREEN)✅ All services stopped$(NC)"

restart:
	@echo "$(YELLOW)🔄 Restarting services...$(NC)"
	@$(MAKE) kill
	@echo "$(YELLOW)⏳ Waiting for ports to release...$(NC)"
	@sleep 2
	@$(MAKE) start

test:
	@echo "$(GREEN)🧪 Running test suite...$(NC)"
	@python3 -m pytest tests/backend/ --cov=src --cov-report=html --cov-report=term
	@echo ""
	@echo "$(YELLOW)Note: Dashboard tests can be run separately with: pytest tests/dashboard/$(NC)"

clean:
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -f .backend.pid backend.log dashboard.log 2>/dev/null || true
	@echo "$(GREEN)✅ Cleanup complete$(NC)"
