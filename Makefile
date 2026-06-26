.PHONY: test validate plan report docker-build

test:
	python3 -m pytest

validate:
	python3 -m harness.harnessctl validate --inventory "$(INVENTORY)" --scenario "$(SCENARIO)"

plan:
	python3 -m harness.harnessctl plan --inventory "$(INVENTORY)" --scenario "$(SCENARIO)" --out-dir "$(or $(OUT_DIR),artifacts/$$(basename "$(SCENARIO)" .yaml))"

report:
	python3 -m harness.harnessctl report --run-id "$(RUN_ID)" $(if $(ARTIFACTS_DIR),--artifacts-dir "$(ARTIFACTS_DIR)",)

docker-build:
	docker build -f docker/nodehost.Dockerfile -t valkey-largecluster-nodehost:local .
