#!/usr/bin/env python3
"""
Reset the demo state — both the local dashboard DB and the remote GitHub fork.

Default behavior: DRY RUN. Nothing is deleted unless you pass --apply.

Examples:
    # See what would be cleaned, change nothing
    python3 scripts/cleanup.py

    # Clean local dashboard DB only
    python3 scripts/cleanup.py --apply --local

    # Clean GitHub fork only (close labeled issues, close & delete fix/cve-* PRs/branches)
    python3 scripts/cleanup.py --apply --remote

    # Full reset — local DB + remote fork
    python3 scripts/cleanup.py --apply --all

Required env vars (loaded from .env):
    GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, TRIGGER_LABEL (optional, defaults to vuln-auto-remediate)
"""
import argparse
import os
import sys
from pathlib import Path

import httpx

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")
LABEL = os.getenv("TRIGGER_LABEL", "vuln-auto-remediate")
DB_PATH = Path(os.getenv("DB_PATH", "data/sessions.db"))
BRANCH_PREFIX = os.getenv("CLEANUP_BRANCH_PREFIX", "fix/cve-")

API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def ok(msg: str) -> None:
    print(f"  ✔ {msg}")


def info(msg: str) -> None:
    print(f"  • {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠ {msg}")


# ──────────── LOCAL ────────────

def clean_local(apply: bool) -> None:
    print("\n📦 LOCAL — dashboard DB")
    if not DB_PATH.exists():
        info(f"{DB_PATH} does not exist — nothing to do.")
        return
    size_kb = DB_PATH.stat().st_size / 1024
    print(f"  Found {DB_PATH} ({size_kb:.1f} KB)")
    if apply:
        DB_PATH.unlink()
        ok(f"Deleted {DB_PATH}. Dashboard will be empty on next refresh.")
        # Also wipe the journal file if it exists
        journal = DB_PATH.with_suffix(DB_PATH.suffix + "-journal")
        if journal.exists():
            journal.unlink()
            ok(f"Deleted {journal}")
    else:
        info("Would delete on --apply")


# ──────────── REMOTE ────────────

def list_labeled_issues() -> list[dict]:
    """Open issues with the trigger label (excludes PRs)."""
    out: list[dict] = []
    page = 1
    while True:
        r = httpx.get(
            f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
            headers=HEADERS,
            params={"labels": LABEL, "state": "open", "per_page": 100, "page": page},
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        for issue in items:
            if "pull_request" in issue:
                continue
            out.append(issue)
        if len(items) < 100:
            break
        page += 1
    return out


def list_fix_prs() -> list[dict]:
    """Open PRs whose branch matches the fix/cve-* prefix."""
    out: list[dict] = []
    page = 1
    while True:
        r = httpx.get(
            f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pulls",
            headers=HEADERS,
            params={"state": "open", "per_page": 100, "page": page},
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        for pr in items:
            ref = (pr.get("head") or {}).get("ref", "")
            if ref.startswith(BRANCH_PREFIX):
                out.append(pr)
        if len(items) < 100:
            break
        page += 1
    return out


def list_fix_branches() -> list[str]:
    """All branches matching the fix/cve-* prefix (open or merged)."""
    out: list[str] = []
    page = 1
    while True:
        r = httpx.get(
            f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/branches",
            headers=HEADERS,
            params={"per_page": 100, "page": page},
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        for b in items:
            name = b.get("name", "")
            if name.startswith(BRANCH_PREFIX):
                out.append(name)
        if len(items) < 100:
            break
        page += 1
    return out


def close_issue(num: int) -> None:
    httpx.patch(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/issues/{num}",
        headers=HEADERS,
        json={"state": "closed", "state_reason": "not_planned"},
        timeout=15.0,
    ).raise_for_status()


def close_pr(num: int) -> None:
    httpx.patch(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/pulls/{num}",
        headers=HEADERS,
        json={"state": "closed"},
        timeout=15.0,
    ).raise_for_status()


def delete_branch(name: str) -> None:
    r = httpx.delete(
        f"{API}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/git/refs/heads/{name}",
        headers=HEADERS,
        timeout=15.0,
    )
    if r.status_code not in (204, 422):  # 422 = already deleted
        r.raise_for_status()


def clean_remote(apply: bool) -> None:
    print(f"\n🌐 REMOTE — github.com/{GITHUB_OWNER}/{GITHUB_REPO}")
    if not (GITHUB_TOKEN and GITHUB_OWNER and GITHUB_REPO):
        warn("GITHUB_TOKEN/OWNER/REPO not set — skipping remote cleanup.")
        return

    issues = list_labeled_issues()
    prs = list_fix_prs()
    branches = list_fix_branches()

    print(f"  Found:")
    print(f"    {len(issues):>3} open issue(s) with label '{LABEL}'")
    print(f"    {len(prs):>3} open PR(s) on branches '{BRANCH_PREFIX}*'")
    print(f"    {len(branches):>3} branch(es) matching '{BRANCH_PREFIX}*'")

    if not (issues or prs or branches):
        info("Nothing to clean.")
        return

    if not apply:
        info("Would close issues, close PRs, and delete branches on --apply")
        if issues:
            print(f"    Issues: {[i['number'] for i in issues]}")
        if prs:
            print(f"    PRs:    {[p['number'] for p in prs]}")
        if branches:
            print(f"    Branches: {branches}")
        return

    # Close issues
    for issue in issues:
        try:
            close_issue(issue["number"])
            ok(f"Closed issue #{issue['number']}: {issue['title']}")
        except Exception as e:
            warn(f"Could not close issue #{issue['number']}: {e}")

    # Close PRs (do this BEFORE branch delete, otherwise PR auto-closes anyway)
    for pr in prs:
        try:
            close_pr(pr["number"])
            ok(f"Closed PR #{pr['number']}: {pr['title']}")
        except Exception as e:
            warn(f"Could not close PR #{pr['number']}: {e}")

    # Delete branches
    for name in branches:
        try:
            delete_branch(name)
            ok(f"Deleted branch {name}")
        except Exception as e:
            warn(f"Could not delete branch {name}: {e}")


# ──────────── MAIN ────────────

def main():
    p = argparse.ArgumentParser(
        description="Reset demo state (local DB and/or remote GitHub fork).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--apply", action="store_true",
                   help="Actually perform the cleanup. Without this it's a dry run.")
    p.add_argument("--local", action="store_true", help="Clean local dashboard DB")
    p.add_argument("--remote", action="store_true", help="Clean remote GitHub fork")
    p.add_argument("--all", action="store_true", help="Clean both local and remote")
    args = p.parse_args()

    if not (args.local or args.remote or args.all):
        # Default: show plan for everything, dry-run
        args.all = True

    do_local = args.local or args.all
    do_remote = args.remote or args.all

    print("=" * 60)
    print(f"  CLEANUP {'(DRY RUN — pass --apply to execute)' if not args.apply else '(APPLYING)'}")
    print("=" * 60)

    if do_local:
        clean_local(args.apply)
    if do_remote:
        clean_remote(args.apply)

    print()
    if not args.apply:
        print("→ Re-run with --apply to perform the cleanup.")
    else:
        print("✅ Cleanup complete.")


if __name__ == "__main__":
    main()
