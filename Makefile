.PHONY: check lint-python test-python lint-embed test-embed synth-cdk help

help:
	@echo "Auritus make targets"
	@echo "  make check       - run all local quality gates"
	@echo "  make lint-python - black --check + ruff"
	@echo "  make test-python - pytest + behave"
	@echo "  make lint-embed  - eslint"
	@echo "  make test-embed  - vitest"
	@echo "  make synth-cdk   - cdk synth"

check: lint-python test-python lint-embed test-embed synth-cdk

lint-python:
	cd cli && python3 -m black --check src tests ../features/steps ../worker-image/src
	cd cli && python3 -m ruff check src tests ../features/steps ../worker-image/src

test-python:
	cd cli && python3 -m pytest -q
	cd cli && python3 -m behave ../features

lint-embed:
	cd embed && npm run lint

test-embed:
	cd embed && npm test

synth-cdk:
	cd cdk && python3 -m pip install -q -r requirements.txt && npx --yes aws-cdk@2 synth --quiet
