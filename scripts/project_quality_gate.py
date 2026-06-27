import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from harness.project_quality import run_project_quality


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-phase", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_project_quality(candidate_phase=args.candidate_phase, run_tests=True)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(result["status"])
    return 0 if result["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
