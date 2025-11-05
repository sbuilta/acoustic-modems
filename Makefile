PYTHON ?= python
PIP ?= $(PYTHON) -m pip

.PHONY: install gui test lint format typecheck build

install:
	$(PIP) install -e .[dev]

gui:
	$(PYTHON) -m amw.gui

test:
	pytest -q

lint:
	ruff check src tests

format:
	black src tests

typecheck:
	mypy src/amw

build:
	$(PYTHON) -m build
