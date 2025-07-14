# Makefile for permit-fastmcp project

.PHONY: all format lint typecheck security test publish

all: format lint typecheck security test

format:
	black .

lint:
	.venv/bin/flake8 permit_fastmcp tests

 typecheck:
	@echo "[typecheck] Add your type checker (e.g., mypy) here."

security:
	@echo "[security] Add your security scanner (e.g., bandit) here."

test:
	PYTHONPATH=. .venv/bin/pytest

publish:
	uv build
	@if [ -n "$$UV_PYPI_TOKEN" ]; then \
	  uv publish --token $$UV_PYPI_TOKEN; \
	else \
	  TOKEN=$$(awk '/\[pypi\]/{flag=1;next}/\[/{flag=0}flag&&/password/{print $$3}' $$HOME/.pypirc); \
	  if [ -z "$$TOKEN" ]; then echo "No PyPI token found in ~/.pypirc"; exit 1; fi; \
	  uv publish --token $$TOKEN; \
	fi 