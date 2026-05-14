"""
FastAPI orchestrator.

Pipeline:
  1. POST /webhook/github receives an issue.opened event from GitHub
  2. Verify HMAC signature (skipped if GITHUB_WEBHOOK_SECRET is empty)
  3. Filter to label `vuln-auto-remediate`
  4. Parse CVE fields from the issue body
  5. Idempotency check
  6. Build a prompt, launch a Devin v3 session, persist to SQLite
  7. Background poller reconciles status every 30s
"""
import hashlib
import hmac
import logging
import os
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

from . import db, devin_client
from . import parser as issue_parser
from . import prompt_builder
from .poller import start_poller, stop_poller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
log = logging.getLogger("orchestrator")

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_OWNER = os.getenv("GITHUB_OWNER", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
TRIGGER_LABEL = os.getenv("TRIGGER_LABEL", "vuln-auto-remediate")
REPO_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    log.info("Database initialized at %s", db.DB_PATH)
    poller_task = await start_poller()
    log.info("Poller started (interval=30s)")
    try:
        yield
    finally:
        await stop_poller(poller_task)
        log.info("Poller stopped")


app = FastAPI(
    title="Devin Vulnerability Remediator",
    description="Event-driven CVE remediation via Devin v3",
    version="1.0.0",
    lifespan=lifespan,
)


def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/sessions")
def list_sessions() -> dict:
    return {"sessions": db.get_all_sessions()}


@app.post("/webhook/github", status_code=202)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str | None = Header(default=None),
):
    raw = await request.body()

    if GITHUB_WEBHOOK_SECRET:
        if not verify_signature(GITHUB_WEBHOOK_SECRET, raw, x_hub_signature_256):
            log.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")
    else:
        log.info("GITHUB_WEBHOOK_SECRET empty — signature check skipped")

    if x_github_event != "issues":
        return {"ignored": f"event={x_github_event}"}

    payload = await request.json()
    if payload.get("action") != "opened":
        return {"ignored": f"action={payload.get('action')}"}

    issue = payload.get("issue", {})
    labels = [lab.get("name") for lab in issue.get("labels", [])]
    if TRIGGER_LABEL not in labels:
        return {"ignored": f"label {TRIGGER_LABEL!r} not present"}

    fields = issue_parser.parse_issue_body(issue.get("body", ""))
    if not issue_parser.all_fields_present(fields):
        log.warning("Issue #%s missing required fields: %s", issue.get("number"), fields)
        return {"ignored": "missing required CVE fields"}

    if db.session_exists_for_issue(issue["number"], fields["cve_id"]):
        log.info("Session already exists for issue #%s, skipping", issue["number"])
        return {"ignored": "already processed"}

    background_tasks.add_task(_launch_devin, issue, fields)
    return {
        "accepted": True,
        "issue": issue["number"],
        "cve": fields["cve_id"],
        "package": fields["package"],
    }


def _launch_devin(issue: dict, fields: dict) -> None:
    """Build prompt, call Devin v3, persist DB row."""
    try:
        prompt = prompt_builder.build_prompt(
            fields, issue_number=issue["number"], repo_url=REPO_URL
        )
        session = devin_client.create_session(
            prompt=prompt,
            title=f"Remediate {fields['cve_id']} in {fields['package']}",
            tags=[
                "vuln-remediation",
                fields["cve_id"],
                fields.get("severity", "UNKNOWN"),
            ],
            max_acu_limit=10,
            repos=[f"{GITHUB_OWNER}/{GITHUB_REPO}"] if GITHUB_OWNER and GITHUB_REPO else None,
        )
        db.insert_session(
            issue_number=issue["number"],
            cve_id=fields["cve_id"],
            package=fields["package"],
            fixed_version=fields["fixed_version"],
            severity=fields.get("severity", "UNKNOWN"),
            devin_session_id=session["session_id"],
            devin_session_url=session.get("url", ""),
        )
        log.info(
            "Launched Devin v3 session %s for issue #%s (%s)",
            session["session_id"], issue["number"], fields["cve_id"],
        )
    except Exception as e:
        log.exception("Failed to launch Devin session: %s", e)
