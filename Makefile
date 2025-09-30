.PHONY: install run test lint

install:
python -m venv .venv
. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

run:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
pytest
