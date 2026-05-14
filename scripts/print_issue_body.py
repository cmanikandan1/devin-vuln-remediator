#!/usr/bin/env python3
"""
Print a ready-to-paste GitHub issue body for ONE HIGH/CRITICAL CVE from a
Trivy report. Useful if you want to manually file an issue (and watch the
webhook flow) without using the auto-creator script.

Usage:
    python3 scripts/print_issue_body.py ~/trivy-report.json

By default prints the first eligible finding. Pass an index to pick another:
    python3 scripts/print_issue_body.py ~/trivy-report.json 2

On macOS the body is also copied to the clipboard via pbcopy if available.
"""
import json
import shutil
import subprocess
import sys


def find_eligible(report: dict):
    seen = set()
    for result in report.get("Results", []):
        file_path = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []):
            if vuln.get("Severity") not in ("HIGH", "CRITICAL"):
                continue
            if not vuln.get("FixedVersion"):
                continue
            key = (vuln.get("VulnerabilityID"), vuln.get("PkgName"), file_path)
            if key in seen:
                continue
            seen.add(key)
            yield {
                "cve_id": vuln.get("VulnerabilityID"),
                "package": vuln.get("PkgName"),
                "current_version": vuln.get("InstalledVersion"),
                "fixed_version": vuln.get("FixedVersion"),
                "severity": vuln.get("Severity"),
                "file_path": file_path,
                "title": vuln.get("Title", vuln.get("VulnerabilityID")),
            }


def main():
    if len(sys.argv) < 2:
        print("Usage: print_issue_body.py <trivy-report.json> [index]")
        sys.exit(1)

    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    with open(sys.argv[1]) as f:
        report = json.load(f)

    findings = list(find_eligible(report))
    if not findings:
        print("No HIGH/CRITICAL findings with a fixed version found.")
        sys.exit(1)
    if idx >= len(findings):
        print(f"Index {idx} out of range — only {len(findings)} eligible findings.")
        sys.exit(1)

    v = findings[idx]
    title = f"[Security] {v['cve_id']} in {v['package']}"
    body = (
        f"**CVE ID:** {v['cve_id']}\n"
        f"**Package:** {v['package']}\n"
        f"**Current Version:** {v['current_version']}\n"
        f"**Fixed Version:** {v['fixed_version']}\n"
        f"**Severity:** {v['severity']}\n"
        f"**File:** {v['file_path']}\n\n"
        f"{v['title']}"
    )

    print("=" * 60)
    print(f"TITLE: {title}")
    print("=" * 60)
    print(body)
    print("=" * 60)
    print(f"LABEL: vuln-auto-remediate")
    print(f"({len(findings)} eligible findings total — pass an index to pick another)")

    if shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=body.encode(), check=False)
        print("\n📋 Body copied to clipboard.")


if __name__ == "__main__":
    main()
