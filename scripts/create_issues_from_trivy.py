#!/usr/bin/env python3
"""
Parse a Trivy JSON report and create GitHub issues, one per HIGH/CRITICAL CVE.

Usage:
    export GITHUB_TOKEN=...
    export GITHUB_OWNER=your_username
    export GITHUB_REPO=superset
    python scripts/create_issues_from_trivy.py trivy-report.json

Requires Issues enabled on the repo (GitHub Settings → Features → Issues).
"""
import json
import os
import sys

import httpx

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER = os.environ["GITHUB_OWNER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
LABEL = os.getenv("TRIGGER_LABEL", "vuln-auto-remediate")
MAX_ISSUES = int(os.getenv("MAX_ISSUES", "5"))

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
API = "https://api.github.com"


def ensure_label() -> None:
    r = httpx.post(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/labels",
        headers=HEADERS,
        json={"name": LABEL, "color": "d93f0b", "description": "Auto-remediate via Devin"},
    )
    if r.status_code not in (201, 422):  # 422 = already exists
        r.raise_for_status()


def create_issue(title: str, body: str) -> dict:
    r = httpx.post(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
        headers=HEADERS,
        json={"title": title, "body": body, "labels": [LABEL]},
    )
    if r.status_code == 410:
        raise SystemExit(
            f"\n❌ Issues are disabled on {GITHUB_OWNER}/{GITHUB_REPO}.\n"
            f"   Enable: GitHub repo → Settings → Features → ✅ Issues\n"
        )
    r.raise_for_status()
    return r.json()


def parse_trivy(path: str):
    with open(path) as f:
        report = json.load(f)
    seen = set()
    for result in report.get("Results", []):
        file_path = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []):
            cve = vuln.get("VulnerabilityID")
            severity = vuln.get("Severity", "UNKNOWN")
            fixed = vuln.get("FixedVersion")
            if severity not in ("HIGH", "CRITICAL"):
                continue
            if not fixed:
                continue
            pkg = vuln.get("PkgName")
            current = vuln.get("InstalledVersion")
            key = (cve, pkg, file_path)
            if key in seen:
                continue
            seen.add(key)
            yield {
                "cve_id": cve,
                "package": pkg,
                "current_version": current,
                "fixed_version": fixed,
                "severity": severity,
                "file_path": file_path,
                "title": vuln.get("Title", cve),
            }


def format_body(v: dict) -> str:
    return (
        f"**CVE ID:** {v['cve_id']}\n"
        f"**Package:** {v['package']}\n"
        f"**Current Version:** {v['current_version']}\n"
        f"**Fixed Version:** {v['fixed_version']}\n"
        f"**Severity:** {v['severity']}\n"
        f"**File:** {v['file_path']}\n\n"
        f"{v['title']}"
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: create_issues_from_trivy.py <trivy-report.json>")
        sys.exit(1)
    ensure_label()
    created = 0
    for v in parse_trivy(sys.argv[1]):
        if created >= MAX_ISSUES:
            break
        title = f"[Security] {v['cve_id']} in {v['package']}"
        issue = create_issue(title, format_body(v))
        print(f"✔ Created issue #{issue['number']}: {title}")
        created += 1
    print(f"\nDone. Created {created} issue(s).")


if __name__ == "__main__":
    main()
