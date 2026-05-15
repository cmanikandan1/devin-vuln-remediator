"""
Devin v3 API client.

v3 is org-scoped and uses service user credentials (keys prefixed `cog_`).

Why v3 over v1:
  1. Native pull_requests array on session responses — no message parsing
  2. max_acu_limit budget cap per session — production-safe
  3. repos scoping — sandbox isolation per session

Status model (two-level):
  status:        new, claimed, running, exit, error, suspended, resuming
  status_detail: working, finished, waiting_for_user, waiting_for_approval,
                 inactivity, user_request, usage_limit_exceeded, out_of_credits,
                 out_of_quota, no_quota_allocation, payment_declined,
                 org_usage_limit_exceeded, total_session_limit_exceeded, error

Required env vars:
  DEVIN_API_KEY   — service user key (cog_...)
  DEVIN_ORG_ID    — find at Devin UI → Settings → Service Users
"""
import logging
import os

import httpx

log = logging.getLogger(__name__)

DEVIN_API_BASE = os.getenv("DEVIN_API_BASE", "https://api.devin.ai/v3")
DEVIN_API_KEY = os.getenv("DEVIN_API_KEY")
DEVIN_ORG_ID = os.getenv("DEVIN_ORG_ID")
GITHUB_TOKEN_FOR_DEVIN = os.getenv("GITHUB_TOKEN")  # Injected into Devin's VM as a session secret

# Belt-and-braces: we read PR URLs from `pull_requests` natively, but also
# ask Devin to emit a structured output as a fallback.
REMEDIATION_SCHEMA = {
    "type": "object",
    "properties": {
        "pr_url":        {"type": "string"},
        "branch_name":   {"type": "string"},
        "tests_passed":  {"type": "boolean"},
        "files_changed": {"type": "array", "items": {"type": "string"}},
        "summary":       {"type": "string"},
    },
    "required": ["pr_url"],
}


def _headers() -> dict[str, str]:
    if not DEVIN_API_KEY:
        raise RuntimeError(
            "DEVIN_API_KEY not set. v3 keys start with `cog_` — "
            "create one at Devin UI → Settings → Service Users."
        )
    if not DEVIN_ORG_ID:
        raise RuntimeError(
            "DEVIN_ORG_ID not set. Find it at Devin UI → Settings → Service Users."
        )
    return {
        "Authorization": f"Bearer {DEVIN_API_KEY}",
        "Content-Type": "application/json",
    }


def _sessions_url() -> str:
    return f"{DEVIN_API_BASE}/organizations/{DEVIN_ORG_ID}/sessions"


def create_session(
    *,
    prompt: str,
    title: str,
    tags: list[str] | None = None,
    max_acu_limit: int = 10,
    repos: list[str] | None = None,
) -> dict:
    """Create a v3 Devin session. Returns the full session response."""
    payload: dict = {
        "prompt": prompt,
        "title": title,
        "tags": tags or [],
        "max_acu_limit": max_acu_limit,
        "structured_output_schema": REMEDIATION_SCHEMA,
    }
    if repos:
        payload["repos"] = repos

    # Inject GitHub token as a session secret so Devin can push branches
    # and open PRs without the GitHub Integration being installed.
    # If the integration IS installed, Devin uses that instead (preferred).
    if GITHUB_TOKEN_FOR_DEVIN:
        payload["session_secrets"] = [
            {"key": "GITHUB_PAT", "value": GITHUB_TOKEN_FOR_DEVIN, "sensitive": True}
        ]

    log.info("Creating v3 Devin session: %s (max_acu=%s)", title, max_acu_limit)
    with httpx.Client(timeout=30.0) as client:
        r = client.post(_sessions_url(), headers=_headers(), json=payload)
        if r.status_code >= 400:
            log.error("v3 create_session failed: %s %s", r.status_code, r.text)
        r.raise_for_status()
        data = r.json()
    log.info("v3 session created: %s", data.get("session_id"))
    return data


def get_session(session_id: str) -> dict:
    """Fetch a v3 session by ID."""
    url = f"{_sessions_url()}/{session_id}"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(url, headers=_headers())
        r.raise_for_status()
        return r.json()


# Back-compat alias
get_session_status = get_session


def extract_pr_url(session_data: dict) -> str | None:
    """Pull the first PR URL from a v3 session response.

    v3 native source: `pull_requests[].pr_url`. Falls back to structured_output.
    """
    prs = session_data.get("pull_requests") or []
    for pr in prs:
        url = pr.get("pr_url")
        if url:
            return url
    return (session_data.get("structured_output") or {}).get("pr_url")


def is_done(session_data: dict) -> bool:
    """Has the session reached a terminal state?

    Current v3 status model uses two levels:
      status:        new, claimed, running, exit, error, suspended, resuming
      status_detail: working, waiting_for_user, waiting_for_approval, finished,
                     inactivity, user_request, usage_limit_exceeded, out_of_credits,
                     out_of_quota, no_quota_allocation, payment_declined,
                     org_usage_limit_exceeded, total_session_limit_exceeded, error

    Terminal statuses: exit, error, suspended.
    A running session with status_detail 'finished' is also done.
    """
    status = (session_data.get("status") or "").lower()
    if status in {"exit", "error", "suspended"}:
        return True
    # A session can be 'running' but with status_detail 'finished' meaning
    # the task is complete and Devin is idle.
    status_detail = (session_data.get("status_detail") or "").lower()
    if status_detail == "finished":
        return True
    return False


def is_successful(session_data: dict) -> bool:
    """Did the session finish its task successfully?

    A session is successful when status_detail is 'finished' (regardless of
    top-level status). Sessions that end with status 'error' or are suspended
    due to limits/inactivity are not successful.
    """
    status_detail = (session_data.get("status_detail") or "").lower()
    return status_detail == "finished"


def needs_attention(session_data: dict) -> bool:
    """Is the session waiting for human input or approval?

    These sessions are not terminal but cannot progress without intervention.
    """
    status_detail = (session_data.get("status_detail") or "").lower()
    return status_detail in {"waiting_for_user", "waiting_for_approval"}
