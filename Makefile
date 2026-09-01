.PHONY: run test lint

run:
	streamlit run app.py

test:
	pytest

lint:
	ruff check .
