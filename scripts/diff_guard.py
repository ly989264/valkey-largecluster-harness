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


def parse_name_status(text):
    files = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") or status.startswith("C"):
            paths = parts[1:]
        else:
            paths = parts[1:2]
        for p in paths:
            if p:
                files.append({"status": status, "file": p})
    return files

def changed(phase):
    out = []
    seen = set()
    st = state() if STATE_PATH.exists() else {"phases":{}}
    base = base_ref_for(st, phase)
    if (ROOT / ".git").exists():
        if base and base != "NO_GIT":
            code, stdout, _ = run_git(["diff", "--name-status", f"{base}..HEAD"])
            if code == 0:
                out += parse_name_status(stdout)
        code, stdout, _ = run_git(["diff", "--name-status"])
        if code == 0:
            out += parse_name_status(stdout)
        code, stdout, _ = run_git(["ls-files", "--others", "--exclude-standard"])
        if code == 0:
            out += [{"status":"??", "file": x} for x in stdout.splitlines() if x.strip()]
    if not out:
        cf = ROOT / f"artifacts/phase-{phase}/changed_files.txt"
        if cf.exists():
            out += [{"status":"listed", "file": x.strip()} for x in cf.read_text(encoding="utf-8").splitlines() if x.strip()]
    dedup = []
    for item in out:
        f = item["file"].replace(os.sep, "/")
        if f in seen:
            continue
        seen.add(f); dedup.append({"status":item["status"], "file":f})
    return dedup

def cmd_changed_files(args):
    ensure_phase(manifest(), args.phase)
    emit({"status":"OK", "phase":args.phase, "changed_files":changed(args.phase)}, args.json)

def cmd_allowed_files(args):
    m = manifest(); ensure_phase(m, args.phase)
    emit({"status":"OK", "phase":args.phase, "allowed_paths":allowed_patterns(m, args.phase)}, args.json)

def cmd_check(args):
    m = manifest(); ensure_phase(m, args.phase)
    pats = allowed_patterns(m, args.phase)
    violations = []
    for item in changed(args.phase):
        f = item["file"]
        if not path_allowed(f, pats):
            violations.append({"file":f, "reason":"not in allowed_paths", "status":item["status"]})
    if violations:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"diff_guard", "violations":violations}, args.json, 2)
    emit({"status":"OK", "phase":args.phase, "changed_files":changed(args.phase), "allowed_paths":pats}, args.json)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd", required=True)
    for name in ["changed-files", "allowed-files", "check"]:
        sp=sub.add_parser(name); sp.add_argument("--phase", required=True); sp.add_argument("--json", action="store_true")
    args=p.parse_args(); globals()["cmd_"+args.cmd.replace('-', '_')](args)
if __name__ == "__main__": main()
