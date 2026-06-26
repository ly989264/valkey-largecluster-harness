.PHONY: test validate

test:
	python3 -m pytest

validate:
	python3 -m harness.harnessctl validate --inventory "$(INVENTORY)" --scenario "$(SCENARIO)"
