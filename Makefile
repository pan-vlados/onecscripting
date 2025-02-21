.ONESHERLL:


PYTHON = venv/bin/python3
PIP = venv/bin/pip
package = $(shell basename $(CURDIR))


venv/bin/activate:
	@python -m venv venv
	@chmod +x $@
	@. ./$@
	@$(PIP) install --upgrade pip
	@$(PIP) install --only-binary :all: .[dev]
venv: venv/bin/activate
	@. ./$<

test: venv tests
	@$(PYTHON) -m unittest discover -v -s $(word 2,$^) -t . -p test_*.py
mypy-check: venv pyproject.toml src/$(package)
	@$(PYTHON) -m mypy $(word 3,$^)/*.py
ruff-check: venv pyproject.toml src/$(package)
	@$(PYTHON) -m ruff check $(word 3,$^)/*.py
ruff-fix: venv pyproject.toml src/$(package)
	@$(PYTHON) -m ruff check --fix $(word 3,$^)/*.py

build: venv pyproject.toml src/$(package)
	@$(PIP) install build twine
	@$(PYTHON) -m build

unzip: build
	@unzip $(wildcard dist/$(package)*.whl) -d dist/$(package)-whl

test_publish: venv pyproject.toml src/$(package)
	@make build
	@make unzip
	tree dist/$(package)-whl
	@rm -rf dist/$(package)-whl
	@$(PYTHON) -m twine check dist/*
	@$(PYTHON) -m twine upload -r testpypi dist/* --verbose
	@$(PIP) install $(package) --index-url https://test.pypi.org/simple/
	$(PIP) list | grep $(package)

publish: venv pyproject.toml src/$(package)
	@make build
	@$(PYTHON) -m twine upload dist/* --verbose
	@make clean

clean:
	@find . -name __pycache__ -exec rm -rf {} +
	@rm -rf src/$(package).egg-info
	@rm -rf dist

clean-all:
	@make clean
	@rm -rf venv
	@echo all cleanuped
