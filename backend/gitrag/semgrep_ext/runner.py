from __future__ import annotations

import json
import subprocess
from pathlib import Path

from gitrag.core.exceptions import GitRAGError
from gitrag.core.logging import get_logger
from gitrag.core.types import Finding, Severity

logger = get_logger(__name__)


def run_semgrep(repo_path: str, rules_dir: str) -> list[Finding]:
    """
    Run semgrep over repo_path using rules from rules_dir.
    Returns an empty list (not an exception) if semgrep is unavailable.
    """
    if not Path(rules_dir).exists():
        logger.warning("semgrep_rules_missing", path=rules_dir)
        return []

    try:
        result = subprocess.run(
            ["semgrep", "--config", rules_dir, "--json", "--quiet", repo_path],
            capture_output = True,
            text           = True,
            timeout        = 120,
        )
    except FileNotFoundError:
        logger.warning("semgrep_not_installed")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("semgrep_timeout")
        return []

    if not result.stdout.strip():
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.warning("semgrep_parse_error")
        return []

    findings: list[Finding] = []
    for r in data.get("results", []):
        try:
            sev = Severity(r["extra"]["severity"].upper())
        except ValueError:
            sev = Severity.INFO
        findings.append(Finding(
            rule_id    = r["check_id"],
            file       = r["path"],
            start_line = r["start"]["line"],
            end_line   = r["end"]["line"],
            message    = r["extra"]["message"],
            severity   = sev,
            snippet    = r["extra"].get("lines", "").strip(),
        ))

    logger.info(
        "semgrep_complete",
        findings = len(findings),
        files    = len(set(f.file for f in findings)),
    )
    return findings
