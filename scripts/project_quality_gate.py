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


def main():
    p=argparse.ArgumentParser(); p.add_argument("--candidate-phase", required=True); p.add_argument("--json", action="store_true")
    args=p.parse_args(); m=manifest()
    if args.candidate_phase not in phases(m):
        emit({"status":"FAIL", "phase":args.candidate_phase, "failed_check":"project_quality_gate", "reason":"unknown candidate phase"}, args.json, 2)
    # P00 strict stub: verifies control-plane manifest is present and candidate exists. P16 finalizes project-wide checks.
    emit({"status":"OK", "candidate_phase":args.candidate_phase, "checks":["manifest-load", "candidate-phase-exists"], "note":"strict P00 stub; final project checks are completed in P16"}, args.json)
if __name__ == "__main__": main()
