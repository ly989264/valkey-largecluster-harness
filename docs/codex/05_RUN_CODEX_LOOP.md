# 如何拉起 Codex Loop 自动运行

本文件告诉使用者如何把这些契约文件放进仓库，并启动一个依赖仓库状态机和 harness 的 Codex loop。核心思路：Codex 每轮只读取仓库状态，不依赖聊天上下文；每轮只推进当前 phase；失败时写 artifact 与状态，再继续修复当前 phase；mandatory gate 通过后自动推进下一 phase。

自动 loop 是主路径。交互式 Codex 只作为可选 smoke check，不是 P00-P02 的默认推进方式。

```text
准备仓库
  -> 复制 7 个 md 到 docs/codex/
  -> 创建 artifacts/runs、artifacts/baselines、state、audits、scripts
  -> 运行 scripts/run_codex_loop.sh
  -> wrapper 调用 codex exec
  -> Codex 读取状态机
  -> 执行当前 phase
  -> 生成 gate result + artifact + cleanup evidence + audit
  -> wrapper 做语义级 postcheck
  -> PASS 自动进入下一 phase
  -> 直到 ALL_PHASES_PASS / BLOCKED_ENV / BLOCKED_RESOURCE / SAFETY_BLOCKED / BLOCKED_PROGRESS
```

## 1. 准备仓库

在目标仓库根目录执行：

```bash
mkdir -p docs/codex
cp 00_CODEX_MASTER_CONTRACT.md docs/codex/
cp 01_PHASES_AND_GATES.md docs/codex/
cp 02_HARNESS_AND_AUDIT.md docs/codex/
cp 03_ARTIFACT_SCHEMA_AND_METRICS.md docs/codex/
cp 04_STATE_MACHINE_AND_MEMORY.md docs/codex/
cp 05_RUN_CODEX_LOOP.md docs/codex/
cp 06_CODEX_BOOTSTRAP_PROMPT.md docs/codex/
```

然后初始化 Git 与项目根目录：

```bash
git init
mkdir -p artifacts/runs artifacts/baselines state audits scripts
```

默认自动主路径是 local-only：单机 Mac 或单机 Linux 上的 Docker/container namespace sandbox。多机能力必须通过配置显式开启；没有真实多机配置时，只能记录 capability-level `SKIPPED_WITH_REASON`，最终报告不得声明 `multi-host ready`。

## 2. 安装与检查 Codex CLI

先安装并登录 Codex CLI，再运行诊断：

```bash
codex login
codex doctor
```

不要直接启用无 sandbox 的危险模式。自动 loop 默认使用 `workspace-write` sandbox，并且不请求人工 approval。

## 3. 自动主路径：非交互 loop

自动 loop 使用 `codex exec`。核心要求：每轮 Codex 都重新读取仓库状态机，因此即使是多次独立 `codex exec`，也能继续当前 phase。

最小单轮命令：

```bash
codex exec \
  --cd "$PWD" \
  --sandbox workspace-write \
  --ask-for-approval never \
  --output-last-message artifacts/codex_last_message.md \
  - < docs/codex/06_CODEX_BOOTSTRAP_PROMPT.md
```

说明：

- `--cd "$PWD"` 限定工作目录。
- `--sandbox workspace-write` 限制写入工作区。
- `--ask-for-approval never` 适合非交互运行，但必须配合本项目 safety gate。
- 不要使用 `--dangerously-bypass-approvals-and-sandbox`，除非整个机器本身就是一次性隔离 runner。

## 4. 自动循环包装器

把下面内容保存为 `scripts/run_codex_loop.sh`。wrapper 不只读取 `phase_status`，也不只检查文件是否存在；每轮 `codex exec` 后都必须做语义级 postcheck：状态文件、phase、run_id、`expected_gate_results`、gate result JSON、audit decision、artifact index、cleanup result、cleanup registry 必须互相指向一致。

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-$PWD}"
PROMPT="$REPO/docs/codex/06_CODEX_BOOTSTRAP_PROMPT.md"
LOG_DIR="$REPO/artifacts/codex_loop"
MAX_ATTEMPTS_PER_PHASE="${MAX_ATTEMPTS_PER_PHASE:-8}"
MAX_NO_PROGRESS="${MAX_NO_PROGRESS:-3}"

mkdir -p "$LOG_DIR" "$REPO/state" "$REPO/audits" "$REPO/artifacts/runs" "$REPO/artifacts/baselines" "$REPO/scripts"

if [ ! -f "$PROMPT" ]; then
  echo "missing bootstrap prompt: $PROMPT" >&2
  exit 2
fi

postcheck() {
  python3 - "$REPO" "$MAX_ATTEMPTS_PER_PHASE" "$MAX_NO_PROGRESS" <<'PY'
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1])
max_attempts = int(sys.argv[2])
max_no_progress = int(sys.argv[3])
now = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

PHASES = [f"P{i:02d}" for i in range(14)]
TERMINAL_STATUS = {"ALL_PHASES_PASS", "BLOCKED_ENV", "BLOCKED_RESOURCE", "SAFETY_BLOCKED", "BLOCKED_PROGRESS"}
VALID_STATE_STATUS = {
    "NOT_STARTED", "IN_PROGRESS", "GATE_RUNNING", "PASS", "FAIL", "FIXING", "ROLLED_BACK",
    "BLOCKED_ENV", "BLOCKED_RESOURCE", "SAFETY_BLOCKED", "BLOCKED_PROGRESS", "ALL_PHASES_PASS",
}
VALID_GATE_STATUS = {"PASS", "FAIL", "BLOCKED_ENV", "BLOCKED_RESOURCE", "SAFETY_BLOCKED", "BLOCKED_PROGRESS", "SKIPPED_WITH_REASON", "MISSING"}
VALID_AUDIT_DECISION = {"PASS", "FAIL", "BLOCKED_ENV", "BLOCKED_RESOURCE", "SAFETY_BLOCKED", "BLOCKED_PROGRESS"}
REAL_GATE_TYPES = {"REAL_VALKEY_E2E", "REAL_VALKEY_FAULT", "REAL_VALKEY_SCALE"}
REAL_GATE_FIELDS = [
    "valkey_version", "node_count", "cluster_state", "slot_coverage",
    "client_port_reachability", "cluster_bus_reachability",
    "runtime_mode", "uses_host_port_mapping",
]

state_path = repo / "state" / "codex_state.json"
cleanup_registry_path = repo / "state" / "cleanup_registry.json"
required_docs = [
    repo / "docs" / "codex" / "RUNBOOK_STATE.md",
    repo / "docs" / "codex" / "PHASE_LEDGER.md",
    repo / "docs" / "codex" / "DECISION_LOG.md",
    repo / "docs" / "codex" / "RISK_REGISTER.md",
    repo / "docs" / "codex" / "ARTIFACT_INDEX.md",
    repo / "docs" / "codex" / "HANDOFF.md",
]
errors = []

def rel(path):
    try:
        return str(Path(path).relative_to(repo))
    except Exception:
        return str(path)

def read_text(path):
    return path.read_text(errors="replace") if path.exists() else ""

def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"invalid json {rel(path)}: {exc}")
        return None

def sha_file(path):
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def phase_number(phase):
    m = re.fullmatch(r"P(\d{2})", str(phase or ""))
    return int(m.group(1)) if m else None

def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]

def normalize_gate_spec(spec, default_phase=None):
    if isinstance(spec, str):
        return {"gate_id": Path(spec).stem, "path": spec, "phase_id": default_phase, "required": True}
    if not isinstance(spec, dict):
        return {"invalid_spec": repr(spec), "phase_id": default_phase, "required": True}
    out = dict(spec)
    out.setdefault("phase_id", default_phase)
    out.setdefault("required", True)
    for src in ("gate_result_path", "artifact", "result_path"):
        if src in out and "path" not in out:
            out["path"] = out[src]
    return out

def expected_specs_for_phase(state, phase):
    raw = state.get("expected_gate_results")
    specs = []
    if isinstance(raw, dict):
        by_phase = raw.get("by_phase") if isinstance(raw.get("by_phase"), dict) else raw
        phase_raw = by_phase.get(phase)
        if phase_raw is not None:
            specs.extend(as_list(phase_raw))
        elif raw.get("phase_id") == phase:
            specs.append(raw)
    elif isinstance(raw, list):
        matching = [x for x in raw if isinstance(x, dict) and x.get("phase_id") == phase]
        if matching:
            specs.extend(matching)
        elif state.get("current_phase") == phase:
            specs.extend(raw)
    if not specs and state.get("last_completed_phase") == phase:
        last = state.get("last_completed_gate_results")
        if isinstance(last, dict):
            specs.extend(as_list(last.get(phase) or last.get("gates")))
        else:
            specs.extend(as_list(last))
    return [normalize_gate_spec(x, phase) for x in specs]

def iter_artifact_refs(value):
    for item in as_list(value):
        if isinstance(item, str):
            yield item
        elif isinstance(item, dict):
            for key in ("path", "artifact", "ref", "href"):
                if item.get(key):
                    yield str(item[key])
                    break

def resolve_ref(run_dir, ref):
    if not ref or re.match(r"^[a-zA-Z]+://", ref):
        return None
    p = Path(ref)
    if p.is_absolute():
        return p
    if str(ref).startswith(("artifacts/", "audits/", "docs/", "state/")):
        return repo / p
    return run_dir / p

def find_gate_file(spec, phase, run_id=None):
    candidates = []
    path = spec.get("path") or spec.get("gate_result_path")
    if path:
        p = Path(path)
        candidates.append(p if p.is_absolute() else repo / p)
    search_roots = []
    if run_id:
        search_roots.append(repo / "artifacts" / "runs" / run_id / "gate_results")
    search_roots.extend(sorted((repo / "artifacts" / "runs").glob("*/gate_results")))
    gate_id = spec.get("gate_id")
    for root in search_roots:
        if not root.exists():
            continue
        if gate_id:
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(gate_id))
            candidates.extend(root.glob(f"*{safe}*.json"))
        candidates.extend(root.glob("*.json"))
    seen = set()
    for c in candidates:
        if c in seen or not c.exists():
            continue
        seen.add(c)
        data = load_json(c)
        if not isinstance(data, dict):
            continue
        if data.get("phase_id") != phase:
            continue
        if gate_id and data.get("gate_id") not in {gate_id, None} and c.stem != gate_id:
            continue
        if run_id and data.get("run_id") not in {run_id, None}:
            continue
        return c, data
    return None, None

def missing_like(value):
    if value in (None, ""):
        return True
    if isinstance(value, str) and value in {"MISSING", "SKIPPED_WITH_REASON", "BLOCKED_ENV", "BLOCKED_RESOURCE", "SAFETY_BLOCKED", "BLOCKED_PROGRESS"}:
        return True
    if isinstance(value, dict) and value.get("status") in {"MISSING", "SKIPPED_WITH_REASON", "BLOCKED_ENV", "BLOCKED_RESOURCE", "SAFETY_BLOCKED", "BLOCKED_PROGRESS"}:
        return True
    return False

def validate_gate_json(path, data, phase, expected_run_id, spec, require_pass):
    local_errors = []
    gate_id = data.get("gate_id") or spec.get("gate_id") or path.stem
    for field in ["schema_version", "phase_id", "run_id", "gate_type", "required", "status", "started_at"]:
        if field not in data:
            local_errors.append(f"{rel(path)} missing required field {field}")
    if not (data.get("finished_at") or data.get("ended_at") or data.get("completed_at")):
        local_errors.append(f"{rel(path)} missing finished_at/ended_at/completed_at")
    if data.get("phase_id") != phase:
        local_errors.append(f"{rel(path)} phase_id={data.get('phase_id')!r} expected {phase!r}")
    if expected_run_id and data.get("run_id") != expected_run_id:
        local_errors.append(f"{rel(path)} run_id={data.get('run_id')!r} expected {expected_run_id!r}")
    if data.get("required") is not True or spec.get("required") is not True:
        local_errors.append(f"{rel(path)} mandatory gate must have required=true")
    status = data.get("status")
    if status not in VALID_GATE_STATUS:
        local_errors.append(f"{rel(path)} invalid status {status!r}")
    if require_pass and status != "PASS":
        local_errors.append(f"{rel(path)} mandatory gate {gate_id} status is {status!r}, expected PASS")
    if data.get("gate_type") == "FAKE_INTEGRATION" and phase_number(phase) is not None and phase_number(phase) >= 3 and require_pass:
        local_errors.append(f"{rel(path)} fake gate cannot satisfy P03+ mandatory gate")
    artifacts = list(iter_artifact_refs(data.get("artifacts")))
    evidence = data.get("evidence")
    if not artifacts:
        local_errors.append(f"{rel(path)} missing artifact references")
    if not isinstance(evidence, dict) or not evidence:
        local_errors.append(f"{rel(path)} missing evidence object")
    run_dir = repo / "artifacts" / "runs" / str(data.get("run_id"))
    for ref in artifacts:
        rp = resolve_ref(run_dir, ref)
        if rp is not None and not rp.exists():
            local_errors.append(f"{rel(path)} references missing artifact {ref}")
    for item in as_list(data.get("missing")):
        if isinstance(item, dict):
            if item.get("status") == "MISSING" and not (item.get("reason") or item.get("missing_reason")):
                local_errors.append(f"{rel(path)} missing item lacks reason/missing_reason")
            if require_pass and item.get("status") == "MISSING" and item.get("whether_blocks_phase", item.get("required", True)) is not False:
                local_errors.append(f"{rel(path)} has blocking missing field while status PASS")
        elif require_pass:
            local_errors.append(f"{rel(path)} missing list item is not structured")
    gate_type = str(data.get("gate_type") or "")
    if gate_type in REAL_GATE_TYPES or gate_type.startswith("REAL_VALKEY"):
        if not isinstance(evidence, dict):
            evidence = {}
        if evidence.get("real_valkey") is False:
            local_errors.append(f"{rel(path)} real gate has evidence.real_valkey=false")
        if phase_number(phase) is not None and phase_number(phase) >= 3:
            for field in REAL_GATE_FIELDS:
                value = evidence.get(field, data.get(field))
                if missing_like(value):
                    local_errors.append(f"{rel(path)} missing real Valkey field {field}")
            uses_mapping = evidence.get("uses_host_port_mapping", data.get("uses_host_port_mapping"))
            if uses_mapping is True and require_pass:
                local_errors.append(f"{rel(path)} uses_host_port_mapping=true cannot PASS real Valkey Cluster gate")
            runtime_mode = str(evidence.get("runtime_mode", data.get("runtime_mode", ""))).lower()
            if runtime_mode in {"host_network", "host-port-mapping", "docker_port_mapping", "nat"} and require_pass:
                local_errors.append(f"{rel(path)} runtime_mode={runtime_mode!r} cannot prove real Valkey Cluster gate")
    return local_errors

def parse_audit_decision(text):
    m = re.search(r"(?im)^\s*Decision\s*:\s*(PASS|FAIL|BLOCKED_ENV|BLOCKED_RESOURCE|SAFETY_BLOCKED|BLOCKED_PROGRESS)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"(?is)^##\s*Decision\s*\n\s*(PASS|FAIL|BLOCKED_ENV|BLOCKED_RESOURCE|SAFETY_BLOCKED|BLOCKED_PROGRESS)\b", text)
    return m.group(1) if m else None

def audit_path_for_phase(phase):
    expected = state.get("expected_audit") if isinstance(state.get("expected_audit"), str) else None
    candidates = []
    if expected and phase in expected:
        candidates.append(repo / expected)
    if phase == "P13":
        candidates.append(repo / "audits" / "P13_final_release.md")
    candidates.append(repo / "audits" / f"{phase}.md")
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

def validate_audit(phase, run_ids, gate_paths, require_pass=True):
    path = audit_path_for_phase(phase)
    if not path.exists():
        return [f"missing audit file {rel(path)}"], None, path
    text = read_text(path)
    local_errors = []
    decision = parse_audit_decision(text)
    if decision not in VALID_AUDIT_DECISION:
        local_errors.append(f"{rel(path)} missing valid Decision field")
    elif require_pass and decision != "PASS":
        local_errors.append(f"{rel(path)} decision={decision!r}, expected PASS")
    if f"Phase: {phase}" not in text and phase not in text:
        local_errors.append(f"{rel(path)} does not identify phase {phase}")
    for section in ["Gate Results", "Artifact Evidence", "Cleanup Evidence", "Reasons"]:
        if section not in text:
            local_errors.append(f"{rel(path)} missing section {section}")
    for rid in sorted(set(filter(None, run_ids))):
        if rid not in text:
            local_errors.append(f"{rel(path)} does not reference run_id {rid}")
    for gp in gate_paths:
        if rel(gp) not in text and gp.name not in text:
            local_errors.append(f"{rel(path)} does not reference gate result {rel(gp)}")
    if "cleanup_result" not in text and "cleanup/cleanup_result.json" not in text:
        local_errors.append(f"{rel(path)} does not reference cleanup evidence")
    return local_errors, decision, path

def validate_cleanup_for_run(run_id, require_pass=True):
    if not run_id:
        return ["missing run_id for cleanup validation"]
    path = repo / "artifacts" / "runs" / run_id / "cleanup" / "cleanup_result.json"
    if not path.exists():
        return [f"missing cleanup evidence {rel(path)}"]
    data = load_json(path)
    if not isinstance(data, dict):
        return [f"invalid cleanup evidence {rel(path)}"]
    status = data.get("status") or data.get("cleanup_status") or data.get("result")
    no_resources = data.get("no_resources_to_cleanup") is True or data.get("active_resources_after_cleanup") == 0
    active = data.get("active_resources") or data.get("remaining_resources") or []
    local_errors = []
    if require_pass and status != "PASS" and not no_resources:
        local_errors.append(f"{rel(path)} cleanup status={status!r}, expected PASS or no_resources_to_cleanup=true")
    if require_pass and active:
        local_errors.append(f"{rel(path)} has active resources after cleanup")
    return local_errors

def validate_phase_pass(phase, run_id=None):
    local_errors = []
    specs = expected_specs_for_phase(state, phase)
    if not specs:
        local_errors.append(f"expected_gate_results missing mandatory gates for {phase}")
        return local_errors, [], [], []
    gate_paths = []
    gate_data = []
    real_gate_seen = False
    for spec in specs:
        if spec.get("required") is not True:
            local_errors.append(f"{phase} expected gate {spec.get('gate_id')} must be required=true")
        gp, data = find_gate_file(spec, phase, run_id)
        if gp is None or data is None:
            local_errors.append(f"missing gate result for {phase} expected gate {spec.get('gate_id') or spec.get('path')}")
            continue
        gate_paths.append(gp)
        gate_data.append(data)
        local_errors.extend(validate_gate_json(gp, data, phase, run_id, spec, require_pass=True))
        gtype = str(data.get("gate_type") or "")
        if gtype in REAL_GATE_TYPES or gtype.startswith("REAL_VALKEY"):
            real_gate_seen = True
    n = phase_number(phase)
    if n is not None and 3 <= n <= 12 and not real_gate_seen:
        local_errors.append(f"{phase} has no REAL_VALKEY_* gate result; P03-P12 cannot be fake-only")
    run_ids = sorted({str(d.get("run_id")) for d in gate_data if d.get("run_id")})
    for rid in run_ids:
        local_errors.extend(validate_cleanup_for_run(rid, require_pass=True))
    audit_errors, _, _ = validate_audit(phase, run_ids or ([run_id] if run_id else []), gate_paths, require_pass=True)
    local_errors.extend(audit_errors)
    return local_errors, gate_paths, gate_data, run_ids

def validate_final_release():
    local_errors = []
    ledger_text = read_text(repo / "docs" / "codex" / "PHASE_LEDGER.md")
    for ph in PHASES:
        if not re.search(rf"\b{ph}\b.*\bPASS\b", ledger_text):
            local_errors.append(f"PHASE_LEDGER.md lacks PASS record for {ph}")
        phase_errors, _, _, _ = validate_phase_pass(ph, None)
        local_errors.extend(phase_errors)
    final_audit_errors, final_decision, final_audit = validate_audit("P13", [], [], require_pass=True)
    local_errors.extend(final_audit_errors)
    if final_decision != "PASS":
        local_errors.append(f"final release audit {rel(final_audit)} is not PASS")
    return local_errors

if not state_path.exists():
    print("POSTCHECK_FAIL missing state/codex_state.json", file=sys.stderr)
    sys.exit(2)

try:
    state = json.loads(state_path.read_text())
except Exception as exc:
    print(f"POSTCHECK_FAIL invalid codex_state.json: {exc}", file=sys.stderr)
    sys.exit(2)

for p in required_docs:
    if not p.exists():
        errors.append(f"missing required state doc: {rel(p)}")
if not cleanup_registry_path.exists():
    errors.append("missing state/cleanup_registry.json")

phase = state.get("current_phase")
status = state.get("phase_status") or state.get("status")
last_completed = state.get("last_completed_phase")
active_run_id = state.get("active_run_id")
completed_run_id = state.get("last_completed_run_id") or active_run_id
last_gate_status = state.get("last_gate_status")
next_action = state.get("next_action")

if status not in VALID_STATE_STATUS:
    errors.append(f"invalid phase_status: {status!r}")
if status == "PASS":
    errors.append("phase_status=PASS is not a stable loop state; after PASS Codex must advance current_phase or write ALL_PHASES_PASS")
if not phase and status != "ALL_PHASES_PASS":
    errors.append("current_phase missing")
if phase and status != "ALL_PHASES_PASS" and phase not in PHASES:
    errors.append(f"invalid current_phase {phase!r}")
if not next_action and status not in TERMINAL_STATUS:
    errors.append("next_action missing for non-terminal state")

ledger = repo / "docs" / "codex" / "PHASE_LEDGER.md"
runbook = repo / "docs" / "codex" / "RUNBOOK_STATE.md"
artifact_index = repo / "docs" / "codex" / "ARTIFACT_INDEX.md"
artifact_index_text = read_text(artifact_index)
if ledger.exists() and phase and status != "ALL_PHASES_PASS" and phase not in read_text(ledger):
    errors.append(f"PHASE_LEDGER.md does not mention current_phase {phase}")
if runbook.exists() and phase and status != "ALL_PHASES_PASS" and phase not in read_text(runbook):
    errors.append(f"RUNBOOK_STATE.md does not mention current_phase {phase}")
for rid_name, rid in (("active_run_id", active_run_id), ("last_completed_run_id", state.get("last_completed_run_id"))):
    if rid:
        run_dir = repo / "artifacts" / "runs" / rid
        if not run_dir.exists():
            errors.append(f"{rid_name} has no run directory: artifacts/runs/{rid}")
        if rid not in artifact_index_text:
            errors.append(f"ARTIFACT_INDEX.md does not index {rid_name} {rid}")

if status != "ALL_PHASES_PASS" and phase and status not in TERMINAL_STATUS:
    current_specs = expected_specs_for_phase(state, phase)
    if not current_specs:
        errors.append(f"expected_gate_results missing declaration for current_phase {phase}")

validated_gate_paths = []
audit_decision = None
if last_gate_status == "PASS" and last_completed:
    pass_errors, gate_paths, gate_data, run_ids = validate_phase_pass(last_completed, completed_run_id)
    errors.extend(pass_errors)
    validated_gate_paths = gate_paths
    audit_errors, audit_decision, _ = validate_audit(last_completed, run_ids or ([completed_run_id] if completed_run_id else []), gate_paths, require_pass=True)

if status == "ALL_PHASES_PASS":
    errors.extend(validate_final_release())

if cleanup_registry_path.exists():
    cleanup = load_json(cleanup_registry_path)
    if isinstance(cleanup, dict):
        active = cleanup.get("active_resources") or cleanup.get("resources") or []
        if (last_gate_status == "PASS" or status == "ALL_PHASES_PASS") and active:
            errors.append("cleanup_registry has active resources after PASS")

for gp in validated_gate_paths:
    if rel(gp) not in artifact_index_text and gp.name not in artifact_index_text:
        errors.append(f"ARTIFACT_INDEX.md does not index gate result {rel(gp)}")

if errors:
    for e in errors:
        print("POSTCHECK_FAIL " + e, file=sys.stderr)
    sys.exit(2)

expected_status_summary = {}
for ph in PHASES:
    phase_summary = []
    for spec in expected_specs_for_phase(state, ph):
        gp, data = find_gate_file(spec, ph, None)
        phase_summary.append({
            "gate_id": spec.get("gate_id") or (data or {}).get("gate_id"),
            "gate_type": spec.get("gate_type") or (data or {}).get("gate_type"),
            "path": rel(gp) if gp else spec.get("path"),
            "status": (data or {}).get("status", "MISSING"),
        })
    if phase_summary:
        expected_status_summary[ph] = phase_summary

fingerprint_run_id = active_run_id or completed_run_id
cleanup_hash = "MISSING"
if fingerprint_run_id:
    cleanup_result = repo / "artifacts" / "runs" / fingerprint_run_id / "cleanup" / "cleanup_result.json"
    cleanup_hash = sha_file(cleanup_result)

signature_payload = json.dumps({
    "current_phase": phase,
    "phase_status": status,
    "last_completed_phase": last_completed,
    "active_run_id": active_run_id,
    "last_completed_run_id": state.get("last_completed_run_id"),
    "expected_gate_statuses": expected_status_summary,
    "audit_decision": audit_decision,
    "artifact_index_tail_hash": hashlib.sha256(artifact_index_text[-4000:].encode()).hexdigest(),
    "cleanup_result_hash": cleanup_hash,
}, sort_keys=True)
signature = hashlib.sha256(signature_payload.encode()).hexdigest()

loop = state.setdefault("loop_control", {})
attempts_by_phase = loop.setdefault("attempts_by_phase", {})
if phase:
    attempts_by_phase[phase] = int(attempts_by_phase.get(phase, 0)) + 1

if loop.get("last_progress_signature") == signature:
    loop["consecutive_no_progress"] = int(loop.get("consecutive_no_progress", 0)) + 1
else:
    loop["last_progress_signature"] = signature
    loop["consecutive_no_progress"] = 0
    loop["last_progress_at"] = now
    loop["last_progress_summary"] = (
        f"phase={phase} status={status} last_completed={last_completed} "
        f"active_run={active_run_id} completed_run={state.get('last_completed_run_id')} "
        f"gate_statuses={expected_status_summary.get(last_completed or phase, [])} "
        f"audit={audit_decision} cleanup_hash={cleanup_hash}"
    )

loop["max_attempts_per_phase"] = max_attempts
loop["max_consecutive_no_progress"] = max_no_progress
loop["updated_at"] = now

if status not in TERMINAL_STATUS and phase:
    attempt_count = int(attempts_by_phase.get(phase, 0))
    no_progress = int(loop.get("consecutive_no_progress", 0))
    if attempt_count > max_attempts:
        state["blocked"] = True
        state["blocker_type"] = "MAX_ATTEMPTS_EXCEEDED"
        state["phase_status"] = "BLOCKED_PROGRESS"
        state["next_action"] = f"Automation stopped after {attempt_count} attempts in {phase}; inspect gate results, audit, cleanup evidence and HANDOFF."
        state["updated_at"] = now
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        print(f"POSTCHECK_BLOCKED MAX_ATTEMPTS_EXCEEDED phase={phase} attempts={attempt_count}")
        sys.exit(10)
    if no_progress >= max_no_progress:
        state["blocked"] = True
        state["blocker_type"] = "NO_PROGRESS"
        state["phase_status"] = "BLOCKED_PROGRESS"
        state["next_action"] = f"Automation stopped after {no_progress} consecutive no-progress semantic checks in {phase}; inspect HANDOFF and latest gate result."
        state["updated_at"] = now
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        print(f"POSTCHECK_BLOCKED NO_PROGRESS phase={phase} consecutive={no_progress}")
        sys.exit(10)

state["updated_at"] = state.get("updated_at") or now
state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")

if status in TERMINAL_STATUS or state.get("blocked") is True:
    print(f"POSTCHECK_STOP status={status} blocker={state.get('blocker_type')}")
    sys.exit(10)

print(f"POSTCHECK_CONTINUE phase={phase} status={status} run_id={fingerprint_run_id}")
sys.exit(0)
PY
}

while true; do
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  set +e
  codex exec \
    --cd "$REPO" \
    --sandbox workspace-write \
    --ask-for-approval never \
    --output-last-message "$LOG_DIR/last_message_$ts.md" \
    - < "$PROMPT" \
    | tee "$LOG_DIR/codex_exec_$ts.log"
  codex_rc=${PIPESTATUS[0]}
  set -e

  if [ "$codex_rc" -ne 0 ]; then
    echo "codex exec failed with exit code $codex_rc; inspect $LOG_DIR/codex_exec_$ts.log" >&2
    exit "$codex_rc"
  fi

  set +e
  postcheck
  check_rc=$?
  set -e

  case "$check_rc" in
    0)
      continue
      ;;
    10)
      echo "Codex loop stopped by terminal/blocker state."
      exit 0
      ;;
    *)
      echo "Codex loop stopped because semantic postcheck failed. Fix state/artifact/gate/audit/cleanup inconsistency before retrying." >&2
      exit "$check_rc"
      ;;
  esac
done
```

wrapper 的 postcheck 接受 PASS 的最低条件是：`expected_gate_results` 全部可解析且 PASS，gate JSON 字段完整，P03+ 真实 Valkey gate 没有 host port mapping/NAT 伪证据，audit 固定格式且 `Decision: PASS`，`cleanup/cleanup_result.json` PASS 或结构化无资源说明，`ARTIFACT_INDEX.md` 索引 run_id 与 gate result。

`ALL_PHASES_PASS` 还会触发 final release postcheck：P00-P13 必须全部在 `PHASE_LEDGER.md` 中有 PASS 记录，并且对应 audit/gate/artifact/cleanup 证据完整；否则 wrapper 失败停止。

执行：

```bash
chmod +x scripts/run_codex_loop.sh
./scripts/run_codex_loop.sh "$PWD"
```

可调阈值：

```bash
MAX_ATTEMPTS_PER_PHASE=10 MAX_NO_PROGRESS=4 ./scripts/run_codex_loop.sh "$PWD"
```

## 5. 可选 smoke check：交互式启动

交互式启动只用于检查 Codex 能否读取仓库、理解契约、运行非常小的 smoke，不作为主路径。

```bash
codex --cd "$PWD" --sandbox workspace-write --ask-for-approval on-request
```

进入后，可以把 `docs/codex/06_CODEX_BOOTSTRAP_PROMPT.md` 的内容作为任务 prompt。smoke check 结束后仍应回到 `scripts/run_codex_loop.sh`。

## 6. Docker 与真实 Valkey gate 的前置条件

P03 之后需要真实 Docker/Valkey gate。自动 loop 前建议人工确认：

```bash
docker version
docker info
```

如果需要避免自动 loop 中发生网络拉取提示，可以提前拉取目标 Valkey 镜像，或在环境中准备本地镜像。Codex 仍必须在 artifact 中记录实际镜像 digest 或 source tag。

如果 Docker、Valkey 镜像或真实资源缺失，Codex 必须写 `BLOCKED_ENV` 或 `BLOCKED_RESOURCE`。不得用 fake gate 代替 P03 之后的真实 Valkey gate。

## 7. 多机环境怎么拉起

默认主路径是 local-only，不要求多机配置。多机能力必须通过配置显式开启；未开启时，相关 capability 只能写 `SKIPPED_WITH_REASON`，最终报告不得声明 `multi-host ready`。

显式多机配置示例路径：

```text
configs/hosts/local.yaml
configs/hosts/multi_host.example.yaml
```

每台机器需要满足：

- Docker 可用；
- 项目工作目录或远端 agent 工作目录明确；
- 不需要 sudo 修改 host 网络；
- 允许按 run_id 清理项目资源；
- host capacity 可被 preflight 读取或配置。

真实多机 gate 只有在实际提供至少两台 host 时才能 PASS；否则只能记录 capability-level `SKIPPED_WITH_REASON` 或在用户显式要求多机 gate 时记录 `BLOCKED_ENV`。

## 8. 运行时如何观察进度

看这些文件，不看聊天记忆：

```bash
cat docs/codex/RUNBOOK_STATE.md
cat docs/codex/PHASE_LEDGER.md
cat docs/codex/HANDOFF.md
cat state/codex_state.json
find artifacts/runs -maxdepth 2 -type f | sort | tail -50
```

每个 phase 的审计文件在：

```text
audits/Pxx.md
```

每个 run 的证据在：

```text
artifacts/runs/<run_id>/
```

## 9. 停止与恢复

停止 loop 后，不需要依赖上次聊天。重新运行 `scripts/run_codex_loop.sh` 即可。Codex 会读取 `state/codex_state.json`、`RUNBOOK_STATE.md`、`PHASE_LEDGER.md`、artifact index，然后继续当前 phase。

wrapper 会在以下情况下停止：

- `ALL_PHASES_PASS`；
- `SAFETY_BLOCKED`；
- `BLOCKED_RESOURCE`；
- `BLOCKED_ENV`；
- `blocked=true` 且 `blocker_type=MAX_ATTEMPTS_EXCEEDED|NO_PROGRESS`；
- 状态、audit、artifact、gate result 不一致。

停止不代表通过。除 `ALL_PHASES_PASS` 外，所有停止都必须按状态文件与 artifact 继续排查。

## 10. 什么时候必须人工介入

以下状态必须人工查看：

- `SAFETY_BLOCKED`：可能触及物理机安全边界。
- `BLOCKED_RESOURCE`：当前机器资源不足。
- `BLOCKED_ENV`：缺 Docker、镜像、远端 host 或权限。
- `MAX_ATTEMPTS_EXCEEDED` / `NO_PROGRESS`：同一 phase 超过自动尝试次数，或连续多轮没有 phase、run_id、gate、artifact 或 next action 的实质变化。
- 语义级 postcheck 失败：可能是 Codex 写了不完整状态、空 gate JSON、伪 PASS、audit 未引用证据、cleanup evidence 缺失，或 `ALL_PHASES_PASS` 没有完整 P00-P13 证据链。

人工介入也必须通过状态文件记录，不要只在聊天里告诉 Codex。

## 11. 不推荐做法

- 不要用一个超长聊天上下文让 Codex“记住全部”。
- 不要跳过 state/harness，直接让 Codex 继续写代码。
- 不要用 fake gate 替代 P03 之后的真实 gate。
- 不要把 `--dangerously-bypass-approvals-and-sandbox` 用在日常开发机。
- 不要在没有 run_id/cleanup 的情况下让 Codex 启动容器或进程。
