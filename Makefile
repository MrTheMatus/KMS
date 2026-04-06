.PHONY: test lint self-check plugin-build smoke all

test:
	python -m pytest tests/ -v

lint:
	ruff check kms/ tests/ scripts/
	ruff format --check kms/ tests/

self-check:
	python -m kms.scripts.verify_integrity --self-check --json

plugin-build:
	cd example-vault/.obsidian/plugins/kms-review && npm run build

smoke:
	cp -n kms/config/config.example.yaml kms/config/config.yaml || true
	python -m kms.scripts.verify_integrity --json

all: lint test self-check plugin-build smoke
	@echo "\n✓ All checks passed"
