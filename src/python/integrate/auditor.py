# src/python/integrate/auditor.py
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# --- Setup import root ---
_THIS_DIR = os.path.dirname(__file__)
_PY_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
if _PY_ROOT not in sys.path:
    sys.path.insert(0, _PY_ROOT)

# --- Maturity calculation utilities ---
from src.python.extractor.Utilities import \
    get_maturity_levels  # {DomainObj: Level}
from src.python.extractor.Utilities import (  # correction based on "joker" logic; repo-level maturity (0..3); {Domain: {Level: {"Yes": [...], "No": [...]}}}
    add_joker, get_lowest_level, get_report_per_level)
# --- Core logic reuse ---
from src.python.extractor.WorkflowAnalyzer import parse_repo_workflows
from src.python.integrate.pom_bridge import analyze_pom_single_repo
from src.python.results.AutomationReporter import (
    check_and_report_automations, parse_markdown_to_domain)

# ---------- Helpers ----------


def _project_root() -> str:
    """Find project root (contains data/automations.md)."""
    candidates = [
        os.path.abspath(os.path.join(_THIS_DIR, "..", "..")),
        os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..")),
        os.path.abspath(os.path.join(_THIS_DIR, "..", "..", "..", "..")),
    ]
    for base in candidates:
        for root in (
            base,
            os.path.dirname(base),
            os.path.dirname(os.path.dirname(base)),
        ):
            data_md = os.path.join(root, "data", "automations.md")
            if os.path.exists(data_md):
                return root
    return os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))


def _write_plugins_json(plugins_map: Dict[str, List[str]]) -> str:
    """Write plugins.json compatible with AutomationReporter.py."""
    root = _project_root()
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "plugins.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plugins_map, f, ensure_ascii=False, indent=2)
    return out_path


def _discover_workflow_files(repo_path: str) -> List[str]:
    """Find all workflow .yml/.yaml files."""
    wf_dir = os.path.join(repo_path, ".github", "workflows")
    if not os.path.isdir(wf_dir):
        return []
    return [
        os.path.join(wf_dir, fn)
        for fn in os.listdir(wf_dir)
        if fn.lower().endswith((".yml", ".yaml"))
    ]


def _has_pom(repo_path: str) -> Tuple[bool, Optional[str]]:
    """Check if repo contains a pom.xml."""
    for root, _dirs, files in os.walk(repo_path):
        if "pom.xml" in files:
            return True, os.path.join(root, "pom.xml")
    return False, None


def _breakdown_by_level(
    repo_report: Dict[Any, Dict[Any, Dict[Any, str]]],
) -> Dict[str, Dict[str, int]]:
    """Count hits and totals for each maturity level."""
    stat = {
        "basic": {"hit": 0, "total": 0},
        "intermediate": {"hit": 0, "total": 0},
        "advanced": {"hit": 0, "total": 0},
    }
    for _domain, subdict in repo_report.items():
        for _subdomain, task_map in subdict.items():
            for task_obj, status in task_map.items():
                lvl = getattr(task_obj, "level", None)
                key = None
                try:
                    name = lvl.name.lower() if lvl is not None else "none"
                    if name in stat:
                        key = name
                except Exception:
                    s = str(lvl).lower()
                    if s in stat:
                        key = s
                if key:
                    stat[key]["total"] += 1
                    if status == "Yes":
                        stat[key]["hit"] += 1
    return stat


# ---------- Main ----------


def audit_repo(
    repo_path: str, pom_jar: Optional[str] = None, print_diag: bool = True
) -> Dict[str, Any]:
    """
    Analyze a local repo and compute automation maturity.
    Returns:
      {
        "repo": str,
        "maturity": {"score": float, "level": str, "method": str},
        "diagnostics": {...},
        "domain_levels": { "Artifacts": "Basic", ... },
        "level_stats": {"basic": {...}, ...},
        "report": {...}
      }
    """
    repo_path = os.path.abspath(repo_path)

    # --- Detect analyzable files ---
    wf_files = _discover_workflow_files(repo_path)
    wf_exists = len(wf_files) > 0
    pom_exists, pom_path = _has_pom(repo_path)

    # 1) Parse workflows
    workflow_dict = parse_repo_workflows(repo_path)
    wf_instances = workflow_dict.get(repo_path, [])
    wf_instance_count = len(wf_instances)

    # 2) Parse pom.xml if exists
    plugin_count = 0
    analyzed_pom = False
    if pom_jar and pom_exists:
        try:
            plugins_map = analyze_pom_single_repo(repo_path, pom_jar)
            plugin_count = len(plugins_map.get(repo_path, []))
            analyzed_pom = True
        except Exception as e:
            print(f"[WARN] PomAnalyzer failed, fallback to empty plugins. Error: {e}")
            plugins_map = {repo_path: []}
    else:
        plugins_map = {repo_path: []}
    _write_plugins_json(plugins_map)

    # 3) Load domain/task rules
    root = _project_root()
    automd = os.path.join(root, "data", "automations.md")
    domains = parse_markdown_to_domain(automd)

    # 4) Match automations (cwd for compatibility)
    old_cwd = os.getcwd()
    try:
        os.chdir(os.path.join(root, "src"))
        report = check_and_report_automations(
            [repo_path], domains, workflow_dict, print_unused=False
        )
    finally:
        os.chdir(old_cwd)

    repo_report = report.get(repo_path, {})

    # 5) Compute maturity using Utilities logic
    levels_by_domain = get_maturity_levels(repo_report)
    with_joker = add_joker(get_report_per_level(repo_report), levels_by_domain)
    overall_level_int = get_lowest_level(with_joker)
    _label_map = {0: "None", 1: "Basic", 2: "Intermediate", 3: "Advanced"}
    maturity_method = "joker+lowest"

    maturity = {
        "score": float(overall_level_int),
        "level": _label_map.get(overall_level_int, "None"),
        "method": maturity_method,
    }

    domain_levels_pretty = {
        (getattr(d, "name", str(d))): getattr(lv, "name", str(lv)).title()
        for d, lv in levels_by_domain.items()
    }

    level_stats = _breakdown_by_level(repo_report)

    # 6) Diagnostics
    diagnostics = {
        "analyzable_exists": bool(pom_exists or wf_exists),
        "pom": {
            "exists": pom_exists,
            "analyzed": analyzed_pom,
            "pom_path": pom_path,
            "plugin_count": plugin_count,
        },
        "workflows": {
            "exists": wf_exists,
            "files": wf_files,
            "instance_count": wf_instance_count,
        },
    }

    if print_diag:
        print("[DIAG] analyzable_exists:", diagnostics["analyzable_exists"])
        print(
            "[DIAG] pom.exists / analyzed / plugin_count:",
            diagnostics["pom"]["exists"],
            diagnostics["pom"]["analyzed"],
            diagnostics["pom"]["plugin_count"],
        )
        print(
            "[DIAG] workflows.exists / files / instance_count:",
            diagnostics["workflows"]["exists"],
            len(diagnostics["workflows"]["files"]),
            diagnostics["workflows"]["instance_count"],
        )

    return {
        "repo": repo_path,
        "maturity": maturity,
        "diagnostics": diagnostics,
        "domain_levels": domain_levels_pretty,
        "level_stats": level_stats,
        "report": report,
    }
