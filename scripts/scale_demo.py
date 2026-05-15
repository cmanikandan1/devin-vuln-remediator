#!/usr/bin/env python3
"""
Scale demo — fire N GitHub issues at the same time to show parallelism.

The whole point of this script: instead of creating 5 issues serially over
30 seconds (which makes the demo look sequential), we open 5 issues in
parallel using a thread pool. GitHub fires 5 webhooks back-to-back, the
orchestrator launches 5 Devin sessions almost simultaneously, and the
dashboard shows 5 concurrent bars on the timeline.

Usage:
    export $(grep -v '^#' .env | xargs)
    python3 scripts/scale_demo.py [N]              # default N=5
    python3 scripts/scale_demo.py 10 --report ~/trivy-report.json
    python3 scripts/scale_demo.py 5 --synthetic    # use built-in fake CVEs

Reads up to N unfiled HIGH/CRITICAL CVEs from the Trivy report. Falls
back to synthetic CVEs if no report is given.
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
from pathlib import Path

import httpx

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER = os.environ["GITHUB_OWNER"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
LABEL = os.getenv("TRIGGER_LABEL", "vuln-auto-remediate")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
API = "https://api.github.com"
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)

# Built-in synthetic CVEs — used with --synthetic when no real report is available.
# These are real CVEs but the file paths are pointed at common Superset locations.
SYNTHETIC = [
    {
        "cve_id": "CVE-2024-DEMO-0001", "package": "requests",
        "current_version": "2.28.0", "fixed_version": "2.31.0",
        "severity": "HIGH", "file_path": "requirements/base.txt",
        "title": "Requests library SSL bypass vulnerability (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0002", "package": "cryptography",
        "current_version": "41.0.1", "fixed_version": "42.0.4",
        "severity": "CRITICAL", "file_path": "requirements/base.txt",
        "title": "Cryptography null pointer dereference (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0003", "package": "urllib3",
        "current_version": "1.26.5", "fixed_version": "2.2.2",
        "severity": "HIGH", "file_path": "requirements/base.txt",
        "title": "urllib3 redirect to incorrect proxy (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0004", "package": "jinja2",
        "current_version": "3.1.2", "fixed_version": "3.1.4",
        "severity": "HIGH", "file_path": "requirements/base.txt",
        "title": "Jinja2 server-side template injection (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0005", "package": "werkzeug",
        "current_version": "2.3.7", "fixed_version": "3.0.3",
        "severity": "HIGH", "file_path": "requirements/base.txt",
        "title": "Werkzeug debugger remote code execution (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0006", "package": "lodash",
        "current_version": "4.17.20", "fixed_version": "4.17.21",
        "severity": "HIGH", "file_path": "docs/yarn.lock",
        "title": "Lodash prototype pollution (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0007", "package": "axios",
        "current_version": "1.5.0", "fixed_version": "1.6.0",
        "severity": "HIGH", "file_path": "docs/yarn.lock",
        "title": "Axios SSRF vulnerability (synthetic)",
    },
    {
        "cve_id": "CVE-2024-DEMO-0008", "package": "pyyaml",
        "current_version": "5.4.1", "fixed_version": "6.0.1",
        "severity": "HIGH", "file_path": "requirements/base.txt",
        "title": "PyYAML arbitrary code execution (synthetic)",
    },
]


def ensure_label() -> None:
    httpx.post(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/labels",
        headers=HEADERS,
        json={"name": LABEL, "color": "d93f0b", "description": "Auto-remediate via Devin"},
    )


def existing_cves() -> set[str]:
    seen: set[str] = set()
    page = 1
    while True:
        r = httpx.get(
            f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
            headers=HEADERS,
            params={"labels": LABEL, "state": "all", "per_page": 100, "page": page},
        )
        r.raise_for_status()
        issues = r.json()
        if not issues:
            break
        for issue in issues:
            if "pull_request" in issue:
                continue
            haystack = (issue.get("title") or "") + "\n" + (issue.get("body") or "")
            for m in CVE_RE.findall(haystack):
                seen.add(m.upper())
        if len(issues) < 100:
            break
        page += 1
    return seen


def parse_trivy(path: str):
    with open(path) as f:
        report = json.load(f)
    seen_keys = set()
    for result in report.get("Results", []):
        file_path = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []):
            if vuln.get("Severity") not in ("HIGH", "CRITICAL"):
                continue
            if not vuln.get("FixedVersion"):
                continue
            key = (vuln.get("VulnerabilityID"), vuln.get("PkgName"), file_path)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            yield {
                "cve_id": vuln.get("VulnerabilityID"),
                "package": vuln.get("PkgName"),
                "current_version": vuln.get("InstalledVersion"),
                "fixed_version": vuln.get("FixedVersion"),
                "severity": vuln.get("Severity"),
                "file_path": file_path,
                "title": vuln.get("Title", vuln.get("VulnerabilityID")),
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


def create_issue(v: dict) -> dict:
    title = f"[Security] {v['cve_id']} in {v['package']}"
    r = httpx.post(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
        headers=HEADERS,
        json={"title": title, "body": format_body(v), "labels": [LABEL]},
        timeout=15.0,
    )
    if r.status_code == 410:
        raise SystemExit("Issues are disabled on the repo. Enable: Settings → Features → ✅ Issues")
    r.raise_for_status()
    return r.json()


def pick_findings(n: int, *, report: str | None, synthetic: bool) -> list[dict]:
    already = existing_cves()
    if synthetic:
        candidates = SYNTHETIC
    elif report:
        candidates = list(parse_trivy(report))
    else:
        # No report given — fall back to synthetic so the demo always works
        print("(no --report provided, using synthetic CVEs)")
        candidates = SYNTHETIC

    chosen: list[dict] = []
    for v in candidates:
        if v["cve_id"].upper() in already:
            continue
        chosen.append(v)
        if len(chosen) >= n:
            break

    if not chosen:
        print("⚠ All eligible CVEs are already filed. Use --synthetic to file demo CVEs anyway.")
        sys.exit(0)
    return chosen


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("n", nargs="?", type=int, default=5, help="number of issues to file in parallel (default 5)")
    p.add_argument("--report", help="Path to a Trivy JSON report")
    p.add_argument("--synthetic", action="store_true", help="Use built-in synthetic CVEs")
    p.add_argument("--workers", type=int, default=10, help="Parallel HTTP workers (default 10)")
    args = p.parse_args()

    ensure_label()
    findings = pick_findings(args.n, report=args.report, synthetic=args.synthetic)

    print(f"\n🚀 Firing {len(findings)} issues in parallel ({args.workers} workers)...\n")
    t0 = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(create_issue, v): v for v in findings}
        for fut in concurrent.futures.as_completed(futures):
            v = futures[fut]
            try:
                issue = fut.result()
                print(f"  ✔ #{issue['number']:>3}  {v['cve_id']:<25}  {v['package']}")
            except Exception as e:
                print(f"  ✗      {v['cve_id']:<25}  failed: {e}")

    elapsed = time.time() - t0
    print(f"\n✅ {len(findings)} issues filed in {elapsed:.1f}s.")
    print(f"   → Watch the dashboard: http://localhost:8501")
    print(f"   → Watch the orchestrator: docker compose logs -f orchestrator")


if __name__ == "__main__":
    main()
