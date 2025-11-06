import argparse
import json

from src.python.integrate.auditor import audit_repo


def main():
    p = argparse.ArgumentParser("automation-level")
    p.add_argument("repo", help="local repo path")
    p.add_argument("--pom-jar", required=True, help="path to PomAnalyzer.jar")
    p.add_argument("--out", help="write full json result to file")
    args = p.parse_args()
    res = audit_repo(args.repo, args.pom_jar)
    print(json.dumps(res["maturity"], ensure_ascii=False, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
