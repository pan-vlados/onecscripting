.ONESHERLL:


PYTHON = venv/bin/python3
PIP = venv/bin/pip
package = $(shell basename $(CURDIR))


venv/bin/activate:
	python -m venv venv
	chmod +x venv/bin/activate
	. ./venv/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install mypy ruff
ifneq ("$(wildcard ./requirements.txt)", "")
	$(PIP) install -r requirements.txt
endif
venv: venv/bin/activate
	. ./venv/bin/activate
test: venv tests
	$(PYTHON) -m unittest -v tests/test*.py
check: venv pyproject.toml src
	$(PYTHON) -m mypy src/$(package)/*.py
	$(PYTHON) -m ruff check src/$(package)/*.py
build: venv pyproject.toml src
	$(PIP) install build twine
	$(PYTHON) -m build
unzip: build
	unzip $(wildcard dist/$(package)*.whl) -d dist/$(package)-whl
test_publish: venv pyproject.toml src
	make build
	make unzip
	tree dist/$(package)-whl
	rm -rf dist/$(package)-whl
	$(PYTHON) -m twine check dist/*
	$(PYTHON) -m twine upload -r testpypi dist/* --verbose
	$(PIP) install $(package) --index-url https://test.pypi.org/simple/
	$(PIP) list | grep $(package)
	# deactivate
publish: venv pyproject.toml src
	make build
	$(PYTHON) -m twine upload dist/* --verbose
	make clean
clean:
	find . -name __pycache__ -exec rm -rf {} +
	rm -rf src/$(package).egg-info
	rm -rf dist
clean_all:
	make clean
	rm -rf venv
