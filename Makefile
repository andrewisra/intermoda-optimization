.PHONY: setup bootstrap train api dashboard test clean

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

bootstrap:
	python scripts/bootstrap_demo.py

train:
	python scripts/train_models.py

api:
	uvicorn backend.app.main:app --reload

dashboard:
	streamlit run frontend/dashboard/app.py

test:
	pytest

clean:
	rm -rf data/raw/*.csv data/processed/*.csv models/*.joblib .pytest_cache __pycache__
