ifeq ($(OS),Windows_NT)
VENV_BIN = .venv/Scripts
else
VENV_BIN = .venv/bin
endif

.PHONY: setup data data-gtfs data-offline api dashboard test docker

setup:
	python -m venv .venv
	$(VENV_BIN)/pip install -r requirements.txt

data:
	$(VENV_BIN)/python scripts/bootstrap_demo.py

data-gtfs:
	$(VENV_BIN)/python scripts/bootstrap_demo.py

data-offline:
	$(VENV_BIN)/python scripts/bootstrap_demo.py --offline

api:
	$(VENV_BIN)/uvicorn backend.app.main:app --reload

dashboard:
	$(VENV_BIN)/streamlit run frontend/dashboard/app.py

test:
	$(VENV_BIN)/python -m pytest -q

docker:
	docker compose up --build
