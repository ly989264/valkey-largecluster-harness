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


def ensure_state_shape(st, m):
    st.setdefault("version", 2)
    st.setdefault("current_phase", "P00")
    st.setdefault("blocked", False)
    st.setdefault("blocked_reason", None)
    st.setdefault("complete", False)
    st.setdefault("phases", {})
    for ph in m["phases"]:
        st["phases"].setdefault(ph["id"], {
            "status": "PENDING", "attempts": 0,
            "result_path": f"artifacts/phase-{ph['id']}/result.json",
            "phase_card_path": f"codex/phase_cards/{ph['id']}.md",
        })
    return st

def next_phase(st, m):
    if st.get("blocked"):
        return None, "BLOCKED"
    if st.get("complete"):
        return None, "COMPLETE"
    for pid in m["phase_ids"]:
        if st["phases"].get(pid, {}).get("status") in {"CLAIMED", "IN_PROGRESS"}:
            return pid, "OK"
    for pid in m["phase_ids"]:
        if st["phases"].get(pid, {}).get("status") != "PASS":
            return pid, "OK"
    return None, "COMPLETE"

def contract(m, phase):
    ph = phases(m)[phase]
    return {
        "id": phase,
        "order": ph["order"],
        "name": ph["name"],
        "goal": ph["goal"],
        "allowed_paths": allowed_patterns(m, phase),
        "pre_gate_commands": ph["pre_gate_commands"],
        "required_artifacts": ph["required_artifacts"],
        "required_outputs": ph["required_outputs"],
        "acceptance": ph["acceptance"],
        "forbidden": ph["forbidden"],
        "manifest_sha256": sha256_file(MANIFEST_PATH),
        "phase_card_sha256": sha256_file(phase_card_path(phase)),
    }

def write_contract_files(m, phase):
    c = contract(m, phase)
    write_json(ROOT / "codex" / "current_phase_contract.json", c)
    md = [f"# Current Phase Contract: {phase}", "", f"## Name\n{c['name']}", "", f"## Goal\n{c['goal']}", "", "## Allowed Paths"]
    md += [f"- `{p}`" for p in c["allowed_paths"]]
    md += ["", "## Pre-Gate Commands"] + [f"- `{x}`" for x in c["pre_gate_commands"]]
    md += ["", "## Required Artifacts"] + [f"- `{x}`" for x in c["required_artifacts"]]
    (ROOT / "codex" / "current_phase_contract.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return c

def git_head():
    code, out, _ = run_git(["rev-parse", "HEAD"])
    return out.strip() if code == 0 and out.strip() else "NO_GIT"

def cmd_status(args):
    m = manifest(); st = ensure_state_shape(state(), m)
    pid, nstatus = next_phase(st, m)
    emit({"status":"OK", "loop_status": nstatus, "current_phase": st.get("current_phase"), "next": pid, "blocked": st.get("blocked"), "complete": st.get("complete"), "phases": st.get("phases")}, args.json)

def cmd_next(args):
    m = manifest(); st = ensure_state_shape(state(), m)
    pid, nstatus = next_phase(st, m)
    if nstatus != "OK":
        emit({"status": nstatus, "next": None, "reason": st.get("blocked_reason")}, args.json, 0 if nstatus == "COMPLETE" else 1)
    emit({"status":"OK", "next": pid, "phase_contract": contract(m, pid), "must_reread":[f"codex/phase_cards/{pid}.md", "codex/current_phase_contract.md", "codex_valkey_loop_md_bundle/03_Codex长循环防遗忘规约.md"]}, args.json)

def cmd_claim(args):
    m = manifest(); st = ensure_state_shape(state(), m); ensure_phase(m, args.phase)
    pid, nstatus = next_phase(st, m)
    if nstatus != "OK" or pid != args.phase:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"claim", "reason":f"next phase is {pid or nstatus}"}, args.json, 2)
    entry = st["phases"][args.phase]
    if entry.get("status") == "PASS":
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"claim", "reason":"phase already PASS"}, args.json, 2)
    attempts = int(entry.get("attempts", 0)) + 1
    if attempts > phases(m)[args.phase].get("max_repair_attempts", 3):
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"claim", "reason":"max repair attempts exceeded"}, args.json, 2)
    entry.update({"status":"CLAIMED", "attempts":attempts, "base_ref": git_head(), "claimed_at":utcnow(), "updated_at":utcnow(), "result_path":f"artifacts/phase-{args.phase}/result.json", "phase_card_path":f"codex/phase_cards/{args.phase}.md"})
    st["current_phase"] = args.phase
    write_json(STATE_PATH, st)
    c = write_contract_files(m, args.phase)
    emit({"status":"OK", "phase":args.phase, "attempt":attempts, "phase_contract":c}, args.json)

def cmd_progress(args):
    m = manifest(); st = ensure_state_shape(state(), m); ensure_phase(m, args.phase)
    ent = st["phases"][args.phase]
    if ent.get("status") not in {"CLAIMED", "IN_PROGRESS", "FAIL"}:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"progress", "reason":f"invalid status {ent.get('status')}"}, args.json, 2)
    ent["status"] = "IN_PROGRESS"; ent["updated_at"] = utcnow(); st["current_phase"] = args.phase
    write_json(STATE_PATH, st); write_contract_files(m, args.phase)
    emit({"status":"OK", "phase":args.phase, "phase_status":"IN_PROGRESS"}, args.json)

def cmd_pass(args):
    m = manifest(); st = ensure_state_shape(state(), m); ensure_phase(m, args.phase)
    cp = subprocess.run([sys.executable, str(ROOT/"scripts/phase_gate.py"), "check", "--phase", args.phase, "--json"], cwd=ROOT, text=True, capture_output=True)
    if cp.returncode != 0:
        emit({"status":"FAIL", "phase":args.phase, "failed_check":"phase_gate", "reason":cp.stdout.strip() or cp.stderr.strip(), "exit_code":cp.returncode}, args.json, 2)
    st = ensure_state_shape(state(), m)
    ent = st["phases"][args.phase]
    ent["status"] = "PASS"; ent["passed_at"] = utcnow(); ent["updated_at"] = utcnow()
    ids = m["phase_ids"]
    if args.phase == ids[-1] and all(st["phases"][p].get("status") == "PASS" for p in ids):
        st["complete"] = True
    else:
        for pid in ids:
            if st["phases"][pid].get("status") != "PASS":
                st["current_phase"] = pid; break
    write_json(STATE_PATH, st)
    emit({"status":"OK", "phase":args.phase, "gate":json.loads(cp.stdout), "complete":st.get("complete", False)}, args.json)

def cmd_fail(args):
    m = manifest(); st = ensure_state_shape(state(), m); ensure_phase(m, args.phase)
    ent = st["phases"][args.phase]
    ent["status"] = "FAIL"; ent["updated_at"] = utcnow(); write_json(STATE_PATH, st)
    emit({"status":"OK", "phase":args.phase, "phase_status":"FAIL"}, args.json)

def cmd_block(args):
    m = manifest(); st = ensure_state_shape(state(), m); ensure_phase(m, args.phase)
    st["blocked"] = True; st["blocked_reason"] = args.reason; st["current_phase"] = args.phase
    st["phases"][args.phase]["status"] = "BLOCKED"; st["phases"][args.phase]["updated_at"] = utcnow()
    write_json(STATE_PATH, st)
    emit({"status":"BLOCKED", "phase":args.phase, "reason":args.reason}, args.json, 1)

def cmd_explain(args):
    m = manifest(); ensure_phase(m, args.phase)
    emit({"status":"OK", "phase":args.phase, "phase_contract":contract(m, args.phase)}, args.json)

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ["status", "next"]:
        sp = sub.add_parser(name); sp.add_argument("--json", action="store_true")
    for name in ["claim", "progress", "pass", "fail", "explain"]:
        sp = sub.add_parser(name); sp.add_argument("--phase", required=True); sp.add_argument("--json", action="store_true")
    sp = sub.add_parser("block"); sp.add_argument("--phase", required=True); sp.add_argument("--reason", required=True); sp.add_argument("--json", action="store_true")
    args = p.parse_args()
    globals()["cmd_" + args.cmd.replace('-', '_')](args)
if __name__ == "__main__":
    main()
