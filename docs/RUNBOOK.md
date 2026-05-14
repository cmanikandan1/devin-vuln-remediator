# 📋 First-Run Runbook (v3)

Step-by-step setup for someone new to this stack. Follow in order.

---

## Part 1 — Tooling (30 min, once)

### 1.1 Install prerequisites

```bash
brew install git docker python@3.11 trivy
brew install --cask docker
open -a Docker      # wait until whale icon is steady
```

Verify:

```bash
docker --version
python3 --version       # should be 3.11.x
trivy --version
```

### 1.2 Get your credentials

**Devin (v3):**
- Log in to [app.devin.ai](https://app.devin.ai)
- Settings → Service Users → New service user
- Copy the API key (`cog_...`) AND the organization ID

**GitHub:**
- [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new)
- Fine-grained token, repository access = your Superset fork
- Permissions: Issues = Read & Write
- Copy the token

**Connect Devin to GitHub:**
- Devin UI → Integrations → GitHub → authorize access to your fork

---

## Part 2 — Superset fork (15 min)

### 2.1 Fork

Visit [github.com/apache/superset](https://github.com/apache/superset) → Fork → create.

### 2.2 ⚠️ Enable Issues on the fork

**This step is mandatory.** By default GitHub disables Issues on forks.

- Your fork → Settings → Features → check ✅ **Issues**

If you skip this, `create_issues_from_trivy.py` returns 410 Gone.

### 2.3 Clone shallow

```bash
cd ~
git clone --depth 1 https://github.com/YOUR_USERNAME/superset.git
```

### 2.4 Run Trivy

```bash
cd ~/superset
trivy fs --severity HIGH,CRITICAL --format json -o ~/trivy-report.json .
```

---

## Part 3 — Project setup (10 min)

### 3.1 Unzip and configure

```bash
cd ~
unzip devin-vuln-remediator.zip
cd devin-vuln-remediator
cp .env.example .env
```

Edit `.env`:

```
DEVIN_API_KEY=cog_<your_service_user_key>
DEVIN_ORG_ID=org_<your_organization_id>
GITHUB_TOKEN=<your_pat>
GITHUB_OWNER=<your_github_username>
GITHUB_REPO=superset
GITHUB_WEBHOOK_SECRET=     # leave empty for local-only demo
TRIGGER_LABEL=vuln-auto-remediate
```

### 3.2 Start the stack

```bash
docker compose up --build
```

First build: ~3 min. Subsequent: <30s.

Verify:
- `http://localhost:8000/health` → `{"status":"ok"}`
- `http://localhost:8501` → dashboard (empty)

---

## Part 4 — Set up the webhook (15 min)

The webhook must be live **before** you create any issue, otherwise the orchestrator will never see it.

### 4.1 Install ngrok

```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken <your_ngrok_token>    # free signup at ngrok.com
```

Start the tunnel in its own terminal and leave it running:

```bash
ngrok http 8000
```

Note the forwarding URL (e.g. `https://abc123.ngrok.app`). Keep this terminal open.

### 4.2 Generate a webhook secret

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Paste into `.env` as `GITHUB_WEBHOOK_SECRET=...` and restart so it's loaded:

```bash
docker compose down && docker compose up --build
```

### 4.3 Configure the GitHub webhook

Your fork → Settings → Webhooks → **Add webhook**:
- Payload URL: `https://<your-ngrok>.ngrok.app/webhook/github`
- Content type: `application/json`
- Secret: paste the same value from `.env`
- Events: "Let me select individual events" → check **Issues** only
- Active: ✅

Save. GitHub immediately fires a `ping` event. Confirm:
- ngrok terminal shows `POST /webhook/github 202`
- GitHub UI: webhook page → Recent Deliveries → green checkmark

If you see a red ✕, click the delivery to inspect the response. 401 means the secret doesn't match.

---

## Part 5 — Trigger ONE issue end-to-end (10 min)

You have two ways to create the trigger issue. Pick one.

### 5.A — Manually (recommended for first run)

Your fork → Issues → **New issue**:

**Title:** `[Security] CVE-2024-6345 in setuptools`

**Body** (copy verbatim, then edit values to match a real CVE from your Trivy report):

```
**CVE ID:** CVE-2024-6345
**Package:** setuptools
**Current Version:** 65.5.0
**Fixed Version:** 70.0.0
**Severity:** HIGH
**File:** requirements/base.txt
```

**Label:** `vuln-auto-remediate` (must already exist — created automatically by the script in 5.B, or add manually first via Issues → Labels → New)

Submit.

### 5.B — From your Trivy scan (one issue only)

If you'd rather pull a real finding from your scan, cap the script to one issue:

```bash
cd ~/devin-vuln-remediator
python3 -m venv .venv && source .venv/bin/activate
pip install httpx
export $(grep -v '^#' .env | xargs)
MAX_ISSUES=1 python3 scripts/create_issues_from_trivy.py ~/trivy-report.json
```

The script prints `✔ Created issue #N` once, then exits.

---

## Part 6 — Watch the pipeline (5–10 min)

Within seconds of issue creation:

1. **GitHub webhook fires** — Recent Deliveries shows a fresh 202
2. **ngrok terminal** — `POST /webhook/github 202`
3. **Orchestrator logs** (`docker compose logs -f orchestrator`):
   ```
   Launched Devin v3 session devin-... for issue #N (CVE-2024-...)
   ```
4. **Devin UI** — new session appears under your service user, status `running`
5. **Dashboard** (`http://localhost:8501`) — new row, status `pending` → `running`

Then 5–10 minutes pass while Devin clones, edits, tests, and pushes:

6. **Devin session** reaches terminal state — `status_detail: finished`
7. **A new PR** appears in your fork, branch `fix/cve-2024-...`
8. **The original issue** gets a 🤖 comment from the bot with the PR link
9. **Dashboard** flips the row to `completed`, MTTR column populates

If the session ends up `waiting_for_user` or `waiting_for_approval`, the dashboard shows a yellow "needs attention" warning — open the Devin UI session and resolve.

### Verifying success

```bash
# Should show one row with status=completed
curl -s http://localhost:8000/sessions | python3 -m json.tool
```

### To run a second issue

Just create another GitHub issue with the trigger label. The webhook is still live, the orchestrator is still up, and idempotency keys off `(issue_number, cve_id)` so duplicates are safe.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3` not found | macOS Sonoma+ has `python3` by default. Try `python` or `brew install python@3.11` |
| Docker build fails on pip | Check internet / corporate proxy. `docker compose build --no-cache` |
| Webhook returns 401 | `GITHUB_WEBHOOK_SECRET` set in `.env` but GitHub doesn't have the matching secret. Make sure they match. |
| Devin API returns 401 | Wrong `DEVIN_API_KEY` (must start with `cog_`) or wrong `DEVIN_ORG_ID` |
| Devin API returns 403 | Service user lacks permission. Check Devin UI → Settings → Service Users |
| `410 Gone` from GitHub Issues API | Issues not enabled on the fork. Settings → Features → ✅ Issues |
| Devin opens PR but fails to push | Devin's GitHub integration isn't authorized for your fork. Devin UI → Integrations |
| Dashboard shows no data | Both containers must share `./data` volume. `docker compose down && up --build` |
| Devin session times out | Normal for big repos. Increase `max_acu_limit` in `app/main.py` |
| Issue parsing returns all None | Issue body doesn't match `Key: value` format. Parser accepts both bold and plain — but key names must match |

---

## What gets committed

- ✅ All code, Dockerfiles, `docker-compose.yml`, README, docs
- ✅ `.env.example`
- ✅ `prompts/remediate_cve.txt`
- ✅ `deck.pptx`
- ❌ `.env` (real secrets — gitignored)
- ❌ `data/*.db`
- ❌ `trivy-report.json`
- ❌ `.venv/`

The `.gitignore` handles all exclusions automatically.
