import argparse, datetime, fnmatch, hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "codex" / "phase_manifest.json"
STATE_PATH = ROOT / "codex" / "loop_state.json"

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')

def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def manifest():
    return load_json(MANIFEST_PATH)

def state():
    return load_json(STATE_PATH)

def phases(m=None):
    m = m or manifest()
    return {p["id"]: p for p in m["phases"]}

def emit(obj, as_json=True, code=0):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, sort_keys=True))
    else:
        print(obj.get("reason") or obj.get("status") or obj)
    raise SystemExit(code)

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def phase_card_path(phase):
    return ROOT / "codex" / "phase_cards" / f"{phase}.md"

def rel(path):
    p = Path(path)
    if p.is_absolute():
        return p.relative_to(ROOT).as_posix()
    return p.as_posix()

def run_git(args):
    try:
        cp = subprocess.run(["git"] + args, cwd=ROOT, text=True, capture_output=True)
    except FileNotFoundError:
        return 127, "", "git not found"
    return cp.returncode, cp.stdout, cp.stderr

def base_ref_for(st, phase):
    return st.get("phases", {}).get(phase, {}).get("base_ref")

def allowed_patterns(m, phase):
    ph = phases(m)[phase]
    out = []
    for pat in ph.get("allowed_paths", []):
        out.append(pat.replace("${PHASE}", phase))
    for pat in m.get("global_allowed_control_paths", []):
        expanded = pat.replace("${PHASE}", phase)
        if expanded not in out:
            out.append(expanded)
    return out

def path_allowed(path, patterns):
    path = path.replace(os.sep, "/")
    if path.startswith("codex_valkey_loop_md_bundle/") or path.startswith("codex_valkey_loop_md_bundle_v2_fixed/"):
        return False
    for pat in patterns:
        pat = pat.replace(os.sep, "/")
        if pat.endswith("/**"):
            prefix = pat[:-3]
            if path == prefix or path.startswith(prefix + "/"):
                return True
        if fnmatch.fnmatch(path, pat):
            return True
    return False

def ensure_phase(m, phase):
    if phase not in phases(m):
        raise ValueError(f"unknown phase {phase}")


def manifest_schema_errors(m):
    errors=[]
    if m.get("version") != 2:
        errors.append("version must be 2")
    expected = [f"P{i:02d}" for i in range(17)]
    if m.get("phase_ids") != expected:
        errors.append("phase_ids must be P00..P16")
    for ph in m.get("phases", []):
        for k in ["id","order","name","goal","allowed_paths","required_outputs","pre_gate_commands","required_artifacts","acceptance","forbidden"]:
            if k not in ph:
                errors.append(f"{ph.get('id','?')} missing {k}")
        for art in ph.get("required_artifacts", []):
            if not art.startswith(f"artifacts/phase-{ph.get('id')}/"):
                errors.append(f"{ph.get('id')} artifact outside phase dir: {art}")
        for cmd in ph.get("pre_gate_commands", []):
            if "phase_gate.py check" in cmd:
                errors.append(f"{ph.get('id')} pre_gate includes phase_gate check")
    p00 = next((p for p in m.get("phases", []) if p.get("id") == "P00"), {})
    for required in ["scripts/project_quality_gate.py", "tests/test_p00_loop_control.py"]:
        if required not in p00.get("allowed_paths", []):
            errors.append(f"P00 allowed_paths missing {required}")
    return errors

def run_guard(script, args):
    cp = subprocess.run([sys.executable, str(ROOT/"scripts"/script)] + args + ["--json"], cwd=ROOT, text=True, capture_output=True)
    if cp.returncode != 0:
        reason = cp.stdout.strip() or cp.stderr.strip()
        return False, reason
    try:
        return True, json.loads(cp.stdout)
    except Exception:
        return False, cp.stdout

def commands_exact(m, phase):
    expected = phases(m)[phase]["pre_gate_commands"]
    path = ROOT / f"artifacts/phase-{phase}/commands.jsonl"
    actual=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            obj=json.loads(line); actual.append(obj)
    cmds = [x.get("command") for x in actual]
    if cmds != expected:
        return False, {"expected":expected, "actual":cmds}
    bad = [x for x in actual if x.get("exit_code") != 0]
    if bad:
        return False, {"nonzero":bad}
    return True, {"command_count":len(actual)}

def result_coverage(m, phase):
    result = load_json(ROOT / f"artifacts/phase-{phase}/result.json")
    expected_outputs = result.get("expected_outputs", [])
    missing = [x for x in phases(m)[phase]["required_outputs"] if x not in expected_outputs]
    if missing:
        return False, {"missing_expected_outputs":missing}
    verified = result.get("verified_outputs", [])
    if not isinstance(verified, list) or not verified:
        return False, {"reason":"verified_outputs is empty"}
    return True, {"verified_count":len(verified)}

def check_phase(phase):
    m = manifest(); ensure_phase(m, phase)
    errors = manifest_schema_errors(m)
    if errors:
        return {"status":"FAIL", "phase":phase, "failed_check":"manifest_schema", "reason":"; ".join(errors)}
    checks=[]
    for script in ["status_guard.py", "artifact_guard.py", "diff_guard.py", "forbidden_guard.py"]:
        ok, payload = run_guard(script, ["check", "--phase", phase])
        checks.append({"check":script, "ok":ok, "payload":payload})
        if not ok:
            return {"status":"FAIL", "phase":phase, "failed_check":script.replace('.py',''), "reason":payload, "checks":checks}
    ok, payload = commands_exact(m, phase)
    checks.append({"check":"commands_exact", "ok":ok, "payload":payload})
    if not ok:
        return {"status":"FAIL", "phase":phase, "failed_check":"commands_exact", "reason":payload, "checks":checks}
    ok, payload = result_coverage(m, phase)
    checks.append({"check":"result_coverage", "ok":ok, "payload":payload})
    if not ok:
        return {"status":"FAIL", "phase":phase, "failed_check":"result_coverage", "reason":payload, "checks":checks}
    return {"status":"OK", "phase":phase, "checks":checks}

def cmd_check(args):
    result = check_phase(args.phase)
    gate_path = ROOT / f"artifacts/phase-{args.phase}/gate_check.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(gate_path, result)
    emit(result, args.json, 0 if result["status"] == "OK" else 2)

def cmd_list(args):
    m=manifest(); emit({"status":"OK", "phases":[{"id":p["id"], "name":p["name"], "order":p["order"]} for p in m["phases"]]}, args.json)

def cmd_explain(args):
    m=manifest(); ensure_phase(m, args.phase); emit({"status":"OK", "phase":args.phase, "phase":phases(m)[args.phase]}, args.json)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    sp=sub.add_parser("list"); sp.add_argument("--json", action="store_true")
    for name in ["check", "explain"]:
        sp=sub.add_parser(name); sp.add_argument("--phase", required=True); sp.add_argument("--json", action="store_true")
    args=p.parse_args(); globals()["cmd_"+args.cmd](args)
if __name__ == "__main__": main()
