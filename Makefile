.PHONY: test gate lint-lite

test:
	python3 -m unittest discover -s tests

lint-lite:
	python3 -m py_compile harness/__init__.py harness/harnessctl.py harness/errors.py harness/jsonio.py

gate: lint-lite test
