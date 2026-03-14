.PHONY: dev backend frontend install

dev: ## Run backend and frontend together
	@trap 'kill 0' EXIT; \
	$(MAKE) backend & \
	$(MAKE) frontend & \
	wait

backend: ## Run backend only
	cd backend && uv run uvicorn app.main:app --reload

frontend: ## Run frontend only
	cd frontend && npm run dev

install: ## Install all dependencies
	cd backend && uv sync
	cd frontend && npm install
