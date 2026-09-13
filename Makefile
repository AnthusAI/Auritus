.PHONY: check lint-python test-python lint-embed test-embed lint-console test-console build-console synth-cdk sync-embed build-embed build-site diagrams help

help:
	@echo "Auritus make targets"
	@echo "  make check       - run all local quality gates"
	@echo "  make lint-python - black --check + ruff"
	@echo "  make test-python - pytest + behave"
	@echo "  make lint-embed  - eslint"
	@echo "  make test-embed  - vitest"
	@echo "  make lint-console - eslint for console app"
	@echo "  make test-console - tsc for console app"
	@echo "  make build-console - next build for console app"
	@echo "  make synth-cdk   - cdk synth"
	@echo "  make diagrams    - render pinned D2 documentation diagrams"

check: diagrams lint-python test-python lint-embed test-embed lint-console test-console build-console synth-cdk

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

lint-console:
	cd console && npm run lint

test-console:
	cd console && npm test

build-console:
	cd console && npm run build

sync-embed: build-embed
	cp embed/dist/embed.js site/public/embed.js

build-site: sync-embed

diagrams:
	./scripts/render-diagrams.sh

synth-cdk:
	cd cdk && python3 -m pip install -q -r requirements.txt && npx --yes aws-cdk@2 synth --quiet
