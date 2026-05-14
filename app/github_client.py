"""Minimal GitHub REST client — used only for commenting back on issues.

Devin opens PRs through its own GitHub integration; this module only
handles the feedback loop comment.
"""
import logging
import os

import httpx

log = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")


def _headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not set")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def comment_on_issue(issue_number: int, body: str) -> None:
    if not (GITHUB_OWNER and GITHUB_REPO):
        log.warning("GITHUB_OWNER/REPO not set; skipping comment")
        return
    url = (
        f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/issues/{issue_number}/comments"
    )
    with httpx.Client(timeout=15.0) as client:
        r = client.post(url, headers=_headers(), json={"body": body})
        if r.status_code >= 400:
            log.error("GitHub comment failed: %s %s", r.status_code, r.text)
        r.raise_for_status()
    log.info("Commented on issue #%s", issue_number)
