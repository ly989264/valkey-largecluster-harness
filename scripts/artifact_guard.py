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


def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines()

def check_result(m, phase, result):
    required = m.get("artifact_contract", {}).get("result_json_required_fields", [])
    missing = [k for k in required if k not in result]
    if missing:
        return f"result.json missing fields {missing}"
    if result.get("phase") != phase:
        return "result.json phase mismatch"
    if result.get("status") != "PASS":
        return "result.json status is not PASS"
    if result.get("manifest_sha256") != sha256_file(MANIFEST_PATH):
        return "manifest_sha256 mismatch"
    if result.get("phase_card_sha256") != sha256_file(phase_card_path(phase)):
        return "phase_card_sha256 mismatch"
    return None

def cmd_check(args):
    m = manifest(); ensure_phase(m, args.phase)
    missing = []
    for p in phases(m)[args.phase]["required_artifacts"]:
        path = ROOT / p
        if not path.exists() or path.stat().st_size == 0:
            missing.append(p)
    if missing:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"artifact_guard", "reason":"missing or empty artifacts", "missing":missing}, args.json, 2)
    result_path = ROOT / f"artifacts/phase-{args.phase}/result.json"
    try:
        result = load_json(result_path)
    except Exception as e:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"artifact_guard", "reason":f"invalid result.json: {e}"}, args.json, 2)
    err = check_result(m, args.phase, result)
    if err:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"artifact_guard", "reason":err}, args.json, 2)
    cmd_path = ROOT / f"artifacts/phase-{args.phase}/commands.jsonl"
    commands = []
    try:
        for i, line in enumerate(read_lines(cmd_path), 1):
            if not line.strip():
                continue
            obj = json.loads(line)
            for field in m["artifact_contract"]["commands_jsonl_schema"]["required_fields"]:
                if field not in obj:
                    raise ValueError(f"line {i} missing {field}")
            if obj.get("phase") != args.phase:
                raise ValueError(f"line {i} phase mismatch")
            commands.append(obj)
    except Exception as e:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"artifact_guard", "reason":f"invalid commands.jsonl: {e}"}, args.json, 2)
    notes = (ROOT / f"artifacts/phase-{args.phase}/notes.md").read_text(encoding="utf-8")
    for heading in ["已验证", "未验证或不确定", "风险"]:
        if heading not in notes:
            emit({"status":"FAIL", "phase":args.phase, "failed_check":"artifact_guard", "reason":f"notes.md missing {heading}"}, args.json, 2)
    changed_path = ROOT / f"artifacts/phase-{args.phase}/changed_files.txt"
    pats = allowed_patterns(m, args.phase)
    bad = [x.strip() for x in changed_path.read_text(encoding="utf-8").splitlines() if x.strip() and not path_allowed(x.strip(), pats)]
    if bad:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"artifact_guard", "reason":"changed_files.txt lists files outside allowed paths", "violations":bad}, args.json, 2)
    emit({"status":"OK", "phase":args.phase, "artifact_count":len(phases(m)[args.phase]["required_artifacts"]), "command_count":len(commands)}, args.json)

def cmd_explain(args):
    m=manifest(); ensure_phase(m, args.phase)
    emit({"status":"OK", "phase":args.phase, "required_artifacts":phases(m)[args.phase]["required_artifacts"]}, args.json)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    for name in ["check", "explain"]:
        sp=sub.add_parser(name); sp.add_argument("--phase", required=True); sp.add_argument("--json", action="store_true")
    args=p.parse_args(); globals()["cmd_"+args.cmd](args)
if __name__ == "__main__": main()
