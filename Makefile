.PHONY: test validate plan report run preflight deploy destroy docker-build

test:
	python3 -m pytest

validate:
	python3 -m harness.harnessctl validate --inventory "$(INVENTORY)" --scenario "$(SCENARIO)"

plan:
	python3 -m harness.harnessctl plan --inventory "$(INVENTORY)" --scenario "$(SCENARIO)" --out-dir "$(or $(OUT_DIR),artifacts/$$(basename "$(SCENARIO)" .yaml))"

report:
	python3 -m harness.harnessctl report --run-id "$(RUN_ID)" $(if $(ARTIFACTS_DIR),--artifacts-dir "$(ARTIFACTS_DIR)",)

run:
	python3 -m harness.harnessctl run --inventory "$(INVENTORY)" --scenario "$(SCENARIO)" --out-dir "$(or $(OUT_DIR),artifacts/$$(basename "$(SCENARIO)" .yaml))"

preflight:
	python3 -m harness.harnessctl preflight --inventory "$(INVENTORY)" --scenario "$(SCENARIO)"

deploy:
	python3 -m harness.harnessctl deploy --inventory "$(INVENTORY)" --scenario "$(SCENARIO)" --out-dir "$(or $(OUT_DIR),artifacts/$$(basename "$(SCENARIO)" .yaml))" $(if $(APPLY),--apply,--dry-run)

destroy:
	python3 -m harness.harnessctl destroy --inventory "$(INVENTORY)" --scenario "$(SCENARIO)" --out-dir "$(or $(OUT_DIR),artifacts/$$(basename "$(SCENARIO)" .yaml))" $(if $(APPLY),--apply,--dry-run)

docker-build:
	docker build -f docker/nodehost.Dockerfile -t valkey-largecluster-nodehost:local .
