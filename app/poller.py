"""
Background poller — v3 edition.

v1 poller had to regex over message content to find PR URLs and got
confused by the ambiguous `blocked` status. v3 fixes both:
  - `pull_requests` is a first-class field on every session response
  - `status` + `status_detail` two-level enum:
      status:        new, claimed, running, exit, error, suspended, resuming
      status_detail: working, finished, waiting_for_user, etc.

Loop: poll → is_done? → extract PR → done. Clean.
"""
import asyncio
import logging

from . import db, devin_client, github_client

log = logging.getLogger("poller")
POLL_INTERVAL_SECONDS = 30


async def _poll_once() -> None:
    active = db.get_active_sessions()
    if not active:
        return
    log.info("Polling %d active session(s)", len(active))

    for row in active:
        session_id = row["devin_session_id"]
        try:
            session = devin_client.get_session(session_id)
        except Exception as e:
            log.error("Failed to fetch v3 session %s: %s", session_id, e)
            continue

        # Always check for PRs first — Devin often finishes the task and then
        # idles in `waiting_for_user` without self-terminating. If a PR exists,
        # the job is done regardless of session status.
        pr_url = devin_client.extract_pr_url(session)
        if pr_url:
            db.update_status(session_id, "completed", pr_url=pr_url)
            log.info("Session %s completed. PR: %s", session_id, pr_url)
            _notify_github(row, pr_url=pr_url, success=True)
            continue

        # Check if session needs human attention (waiting_for_user / waiting_for_approval)
        # Only treat as blocked if no PR was produced (checked above).
        if devin_client.needs_attention(session):
            status_detail = session.get("status_detail", "unknown")
            if row["status"] != "blocked":
                db.update_status(session_id, "blocked",
                                 error_message=f"Session needs attention: {status_detail}")
                log.warning("Session %s needs attention (no PR yet): %s", session_id, status_detail)
            continue

        if not devin_client.is_done(session):
            # Still working — bump pending → running on first observed poll
            if row["status"] == "pending":
                db.update_status(session_id, "running")
            continue

        # Session reached a terminal state without a PR
        status = session.get("status", "unknown")
        status_detail = session.get("status_detail", "")
        db.update_status(
            session_id,
            "failed",
            error_message=f"Session ended (status={status}, detail={status_detail}) without producing a PR",
        )
        log.warning("Session %s ended without PR (status=%s, detail=%s)",
                    session_id, status, status_detail)
        _notify_github(row, pr_url=None, success=False)


def _notify_github(session_row: dict, *, pr_url: str | None, success: bool) -> None:
    issue_number = session_row["issue_number"]
    devin_url = session_row.get("devin_session_url", "")
    if success and pr_url:
        body = (
            f"🤖 **Devin has opened a pull request to remediate this vulnerability.**\n\n"
            f"- PR: {pr_url}\n"
            f"- Devin session: {devin_url}\n\n"
            f"_Please review before merging. No code has been auto-merged._"
        )
    else:
        body = (
            f"⚠️ **Devin could not complete remediation autonomously.**\n\n"
            f"- Devin session: {devin_url}\n\n"
            f"_Human review required._"
        )
    try:
        github_client.comment_on_issue(issue_number, body)
    except Exception as e:
        log.error("Failed to post GitHub comment on issue #%s: %s", issue_number, e)


async def _poll_loop() -> None:
    while True:
        try:
            await _poll_once()
        except Exception as e:
            log.exception("Poll iteration failed: %s", e)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def start_poller() -> asyncio.Task:
    return asyncio.create_task(_poll_loop())


async def stop_poller(task: asyncio.Task) -> None:
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
