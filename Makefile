.PHONY: install lint test check run docker-build

install:
	python -m pip install -e '.[dev]'

lint:
	ruff check .

test:
	pytest

check: lint test

run:
	uvicorn app.main:app --reload

docker-build:
	docker build --tag shelfsense:local .
