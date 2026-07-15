#!/usr/bin/env python3
"""Refresh the vendored Security Benchmark for Salesforce (SBS) dataset.

Clones a pinned snapshot of github.com/Salesforce-Security-Benchmark/docs-site
and regenerates:

    references/sbs/controls.json
    references/sbs/SBS_VERSION
    references/sbs/ATTRIBUTION.txt

Only structured control-metadata YAML is redistributed. The upstream
benchmark/*.md prose is NOT copied — audit responses link to the
upstream docs URL embedded per-control in `controls.json`.

CC BY-SA 4.0 attribution travels with the data via the `_license` block
at the top of `controls.json`, the LICENSE/NOTICE files alongside, and
the verbatim ATTRIBUTION.txt that SKILL.md instructs the LLM to include
in every audit response.

Usage:
    python3 scripts/fetch_sbs.py                # uses pinned SHA in SBS_VERSION
    python3 scripts/fetch_sbs.py --sha <sha>    # pin to a specific commit
    python3 scripts/fetch_sbs.py --latest       # pin to upstream main HEAD

Exit codes:
    0  success
    1  fetch / parse / validation error
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

UPSTREAM_REPO = "https://github.com/Salesforce-Security-Benchmark/docs-site.git"
UPSTREAM_URL = "https://github.com/Salesforce-Security-Benchmark/docs-site"
UPSTREAM_DOCS = "https://docs.securitybenchmark.org/"
LICENSE_URI = "https://creativecommons.org/licenses/by-sa/4.0/"
LICENSE_NAME = "CC BY-SA 4.0"

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "references" / "sbs"
CONTROLS_PATH = DATA_DIR / "controls.json"
VERSION_PATH = DATA_DIR / "SBS_VERSION"
ATTRIBUTION_PATH = DATA_DIR / "ATTRIBUTION.txt"

CATEGORY_NAMES = {
    "ACS": "Access Controls",
    "AUTH": "Authentication",
    "CODE": "Code Security",
    "CPORTAL": "Customer Portals",
    "DATA": "Data Security",
    "DEP": "Deployments",
    "FDNS": "Foundations",
    "FILE": "File Security",
    "INT": "Integrations",
    "MON": "Event Monitoring",
    "OAUTH": "OAuth Security",
    "SECCONF": "Security Configuration",
}

CATEGORY_TO_DOC_SLUG = {
    "ACS": "access-controls",
    "AUTH": "authentication",
    "CODE": "code-security",
    "CPORTAL": "customer-portals",
    "DATA": "data-security",
    "DEP": "deployments",
    "FDNS": "foundations",
    "FILE": "file-security",
    "INT": "integrations",
    "MON": "event-monitoring",
    "OAUTH": "oauth-security",
    "SECCONF": "security-configuration",
}

VALID_RISK = {"Critical", "High", "Moderate"}
VALID_SCOPE = {"org", "entity", "mechanism", "inventory"}

CONTROL_ID_RE = re.compile(r"^SBS-([A-Z]+)-\d+$")


def _category_from_id(control_id: str) -> str:
    m = CONTROL_ID_RE.match(control_id)
    if not m:
        raise SystemExit(f"Malformed control_id: {control_id!r}")
    return m.group(1)


def _doc_url(control_id: str) -> str:
    cat = _category_from_id(control_id)
    slug = CATEGORY_TO_DOC_SLUG.get(cat)
    if not slug:
        raise SystemExit(f"Unknown SBS category code: {cat} (control {control_id})")
    return f"{UPSTREAM_DOCS}benchmark/{slug}.html#{control_id.lower()}"


def _read_pinned_sha() -> str | None:
    if not VERSION_PATH.exists():
        return None
    for line in VERSION_PATH.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^upstream_sha:\s*([0-9a-f]{40})\b", line)
        if m:
            return m.group(1)
    return None


def _clone(sha: str | None) -> tuple[Path, str]:
    tmp = Path(tempfile.mkdtemp(prefix="sbs-"))
    subprocess.run(
        ["git", "clone", "--no-checkout", "--filter=blob:none", UPSTREAM_REPO, str(tmp)],
        check=True,
        capture_output=True,
    )
    if sha:
        try:
            subprocess.run(
                ["git", "-C", str(tmp), "fetch", "--depth=1", "origin", sha],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # Some hosts disallow arbitrary-SHA shallow fetch; fall back.
            subprocess.run(
                ["git", "-C", str(tmp), "fetch", "--unshallow"],
                check=True,
                capture_output=True,
            )
        subprocess.run(
            ["git", "-C", str(tmp), "checkout", sha], check=True, capture_output=True
        )
    else:
        subprocess.run(
            ["git", "-C", str(tmp), "checkout", "main"], check=True, capture_output=True
        )
    resolved = subprocess.run(
        ["git", "-C", str(tmp), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return tmp, resolved


def _read_controls(repo_dir: Path) -> list[dict]:
    meta_dir = repo_dir / "control-metadata"
    if not meta_dir.is_dir():
        raise SystemExit(f"control-metadata/ missing at {meta_dir}")

    controls: list[dict] = []
    for path in sorted(meta_dir.iterdir()):
        if path.suffix not in {".yaml", ".yml"}:
            continue
        raw = path.read_text(encoding="utf-8")
        try:
            doc = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise SystemExit(f"Failed to parse {path.name}: {e}") from e
        if not isinstance(doc, dict):
            raise SystemExit(f"Empty/invalid YAML: {path.name}")

        control_id = doc.get("control_id")
        risk_level = doc.get("risk_level")
        remediation = doc.get("remediation")
        task = doc.get("task")

        if not isinstance(control_id, str) or not control_id:
            raise SystemExit(f"Missing control_id in {path.name}")
        if path.name not in {f"{control_id}.yaml", f"{control_id}.yml"}:
            raise SystemExit(f"File {path.name} does not match control_id {control_id}")
        # risk_level is documented as required upstream but at least one
        # current control (SBS-AUTH-004) omits it. Treat it as optional.
        if risk_level is not None and risk_level not in VALID_RISK:
            raise SystemExit(f"Invalid risk_level in {path.name}: {risk_level!r}")
        if not isinstance(remediation, dict):
            raise SystemExit(f"Missing remediation block in {path.name}")
        scope = remediation.get("scope")
        if scope not in VALID_SCOPE:
            raise SystemExit(f"Invalid remediation.scope in {path.name}: {scope!r}")
        entity_type = remediation.get("entity_type")
        if scope == "entity" and not entity_type:
            raise SystemExit(
                f"remediation.entity_type required for entity-scoped {path.name}"
            )
        if scope != "entity" and entity_type:
            raise SystemExit(
                f"remediation.entity_type forbidden for non-entity scope in {path.name}"
            )

        category = _category_from_id(control_id)
        out: dict = {
            "control_id": control_id,
            "category": category,
            "category_name": CATEGORY_NAMES.get(category, category),
            "risk_level": risk_level,
            "remediation": {"scope": scope},
            "doc_url": _doc_url(control_id),
        }
        if entity_type:
            out["remediation"]["entity_type"] = entity_type
        if isinstance(task, dict) and isinstance(task.get("title_template"), str):
            template = task["title_template"]
            if template:
                out["task"] = {"title_template": template}
        controls.append(out)

    controls.sort(key=lambda c: c["control_id"])
    return controls


def _license_block(sha: str, fetched_at: str) -> dict:
    return {
        "source": UPSTREAM_URL,
        "docs": UPSTREAM_DOCS,
        "upstream_commit": sha,
        "fetched_at": fetched_at,
        "license": LICENSE_NAME,
        "license_uri": LICENSE_URI,
        "attribution": (
            "Based on Security Benchmark for Salesforce (SBS) with modifications. "
            "Subset extracted from control-metadata/ and converted from YAML to JSON. "
            "See references/sbs/NOTICE for details."
        ),
        "notice": "This file is generated by scripts/fetch_sbs.py. Do not edit by hand.",
    }


def _write_outputs(controls: list[dict], sha: str, fetched_at: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "_license": _license_block(sha, fetched_at),
        "schema_version": 1,
        "controls": controls,
    }
    CONTROLS_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    VERSION_PATH.write_text(
        (
            f"upstream_repo: {UPSTREAM_REPO}\n"
            f"upstream_sha: {sha}\n"
            f"fetched_at: {fetched_at}\n"
            f"license: {LICENSE_NAME}\n"
            f"license_uri: {LICENSE_URI}\n"
        ),
        encoding="utf-8",
    )

    # ATTRIBUTION.txt is the canonical block SKILL.md instructs the LLM
    # to render verbatim at the end of every audit response. Regenerated
    # alongside the dataset so the upstream commit stays in sync.
    ATTRIBUTION_PATH.write_text(
        (
            "Based on Security Benchmark for Salesforce (SBS) with modifications.\n"
            f"Original work: {UPSTREAM_URL}\n"
            f"Documentation: {UPSTREAM_DOCS}\n"
            f"Licensed under {LICENSE_NAME}: {LICENSE_URI}\n"
            f"Upstream commit: {sha}\n"
            "Subset extracted from control-metadata; YAML converted to JSON; "
            "no upstream prose redistributed.\n"
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sha", help="Pin to a specific upstream commit SHA")
    group.add_argument(
        "--latest",
        action="store_true",
        help="Pin to the current upstream main HEAD",
    )
    args = parser.parse_args()

    if args.sha:
        sha: str | None = args.sha
    elif args.latest:
        sha = None  # resolve from HEAD after clone
    else:
        sha = _read_pinned_sha()
        if not sha:
            sys.stderr.write(
                "No pinned SBS_VERSION found and --latest not passed. "
                "Use --latest to bootstrap or --sha to pin a specific commit.\n"
            )
            return 1

    repo_dir, resolved_sha = _clone(sha)
    fetched_at = _dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    controls = _read_controls(repo_dir)
    if not controls:
        sys.stderr.write(
            "No controls parsed; aborting to avoid clobbering controls.json with empty data.\n"
        )
        return 1
    _write_outputs(controls, resolved_sha, fetched_at)
    sys.stdout.write(
        f"Wrote {len(controls)} controls from {resolved_sha[:12]} to references/sbs/.\n"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"fetch_sbs failed: {e}\n")
        sys.exit(1)
