.PHONY: venv install run dev fmt lint type test all

venv:
	python -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

run:
	. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 4000

dev:
	. .venv/bin/activate && uvicorn app.main:app --reload --port 4000

fmt:
	. .venv/bin/activate && black . && isort .

lint:
	. .venv/bin/activate && ruff check .

type:
	. .venv/bin/activate && mypy .

test:
	. .venv/bin/activate && pytest -q

all: fmt lint type test
