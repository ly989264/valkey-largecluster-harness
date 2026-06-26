.PHONY: test validate plan

test:
	python3 -m pytest

validate:
	python3 -m harness.harnessctl validate --inventory "$(INVENTORY)" --scenario "$(SCENARIO)"

plan:
	python3 -m harness.harnessctl plan --inventory "$(INVENTORY)" --scenario "$(SCENARIO)" --out-dir "$(or $(OUT_DIR),artifacts/$$(basename "$(SCENARIO)" .yaml))"
