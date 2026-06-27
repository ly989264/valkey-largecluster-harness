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


def files_to_scan():
    skip_dirs = {".git", "__pycache__"}
    roots = [ROOT]
    for base in roots:
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            relp = p.relative_to(ROOT).as_posix()
            parts = set(relp.split("/"))
            if parts & skip_dirs:
                continue
            if relp.startswith("artifacts/") or relp.startswith("codex_valkey_loop_md_bundle/"):
                continue
            if relp == "codex/phase_manifest.json" or relp.startswith("codex/phase_cards/"):
                continue
            if relp == "scripts/forbidden_guard.py":
                continue
            if p.suffix not in {".py", ".sh", ".yaml", ".yml", ".json", ".md", ".toml", ""}:
                continue
            yield relp, p

def scan_patterns():
    return [
        ("docker" + ":dind", "Docker-in-Docker image is forbidden"),
        ("DOCKER_HOST" + "=tcp://", "remote dockerd dependency is forbidden"),
        ("privileged" + " dockerd", "privileged dockerd is forbidden"),
        ("assert" + " True", "fake assertion pass is forbidden"),
        ("pytest.skip(", "pytest skip requires explicit SKIPPED_RESOURCE explanation"),
    ]

def scan_all():
    violations=[]
    for relp, path in files_to_scan():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, 1):
            for pat, reason in scan_patterns():
                if pat in line:
                    if relp.startswith("tests/") and pat in {"assert True", "pytest.skip("}:
                        continue
                    violations.append({"file":relp, "line":lineno, "pattern":pat, "reason":reason})
            if "docker run" in line and "for " in line and "node" in line:
                violations.append({"file":relp, "line":lineno, "pattern":"one-node-one-container", "reason":"possible docker run per node loop"})
            if ("127.0.0.1" in line or "localhost" in line) and relp.endswith(".py") and not relp.startswith("tests/") and "single-mac" not in relp:
                violations.append({"file":relp, "line":lineno, "pattern":"hard-coded-host", "reason":"hard-coded host/IP outside tests or samples"})
    code, out, _ = run_git(["status", "--short", "codex_valkey_loop_md_bundle"])
    if code == 0 and out.strip():
        violations.append({"file":"codex_valkey_loop_md_bundle", "line":0, "pattern":"spec-mutation", "reason":"Markdown spec bundle has git changes"})
    return violations

def cmd_scan(args):
    v=scan_all(); emit({"status":"OK" if not v else "FAIL", "violations":v}, args.json, 0 if not v else 2)

def cmd_check(args):
    ensure_phase(manifest(), args.phase)
    v=scan_all()
    if v:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"forbidden_guard", "violations":v}, args.json, 2)
    emit({"status":"OK", "phase":args.phase, "violations":[]}, args.json)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    sp=sub.add_parser("scan"); sp.add_argument("--json", action="store_true")
    sp=sub.add_parser("check"); sp.add_argument("--phase", required=True); sp.add_argument("--json", action="store_true")
    args=p.parse_args(); globals()["cmd_"+args.cmd](args)
if __name__ == "__main__": main()
