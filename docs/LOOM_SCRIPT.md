# 🎬 Loom Recording Script — 5:00 exact

**Audience:** VP of Engineering + senior ICs at Cognition
**Deck:** `deck.pptx` (4 slides)
**Goal:** High-energy, confident, declarative. Land the pitch.

---

## Timing budget

| Time | Section | Slide |
|---|---|---|
| 0:00 – 0:45 | The problem hook | Slide 1 |
| 0:45 – 1:30 | Knowledge work pattern | Slide 2 |
| 1:30 – 2:00 | Why Devin + architecture | Slide 3 |
| 2:00 – 4:00 | LIVE DEMO (no slides) | — |
| 4:00 – 4:30 | Engineering story (git history) | — |
| 4:30 – 5:00 | The close | Slide 4 |

Total: 5:00. Target ~770 words at 155 wpm.

---

## 0:00 – 0:45  →  SLIDE 1

> **"Every engineering organization I work with has a security debt backlog. And nobody is excited to work on it."**
>
> *(beat — 1 second)*
>
> **"In the next five minutes, I'm going to show you a system where that work just... disappears."**

**Delivery:** Slow, confident. Pause on the beat. Land "disappears" hard.

→ Click to Slide 2

---

## 0:45 – 1:30  →  SLIDE 2

> **"Knowledge workers spend up to thirty percent of their time in a single loop. Investigate. Decide. Act."**
>
> *(small pause)*
>
> **"Read the alert. Check the dependency tree. Confirm the fix. Run the tests. Open the PR. That's the loop."**
>
> **"In every customer engagement I have at AWS, this loop is what consumes senior engineering time. For Apache Superset specifically — it's thousands of hours per year on dependency hygiene alone. Not features. Not customers. Hygiene."**

**Delivery:** Accelerate through the five micro-tasks (treat them as one list). Drop pace on "thousands of hours" and "hygiene."

→ Click to Slide 3

---

## 1:30 – 2:00  →  SLIDE 3

> **"This is why I built on Devin and not on Copilot or Cursor. Autocomplete helps a human type faster. Devin IS the engineer for tasks like this — it owns the full loop end-to-end, in a sandbox, with real environment access."**
>
> *(pause — gesture to the diagram)*
>
> **"Here's the system. Trivy scans the repo. Vulnerabilities become GitHub issues. New issues fire webhooks. My orchestrator dispatches Devin v3 sessions, tracks every one to completion, and surfaces it all in a live dashboard. Let me show you."**

**Delivery:** Hit "IS" with emphasis. Then transition crisply to the demo.

→ Stop sharing slides. Switch to browser.

---

## 2:00 – 4:00  →  LIVE DEMO

### Window layout (set up BEFORE recording)

- **Tab 1:** Your Superset fork on the **New Issue** page, issue body on your clipboard
- **Tab 2:** Devin web UI, logged in, sessions list visible
- **Tab 3:** Dashboard at `localhost:8501` (showing some session history)
- **Tab 4:** A pre-prepared completed PR from an earlier successful run
- **Terminal:** Tailing `docker compose logs -f orchestrator`

### 2:00 – 2:25  →  Create the issue + show webhook

*[On New Issue tab]*

> **"I'm in my Superset fork. I'll create a real issue right now — not a simulated payload."**

*Paste issue body, add `vuln-auto-remediate` label, click Submit.*

> **"The moment I click Submit, GitHub fires a webhook to my orchestrator over ngrok."**

*Switch to terminal.*

> **"There it is in the logs. Webhook received. Signature verified. Issue body parsed. Devin v3 session created — ACU budget capped at ten, repo scope locked to this fork."**

### 2:25 – 2:55  →  Show Devin working

*Switch to Devin UI.*

> **"And here's Devin, already working in its sandbox. Cloning the repo. Checking out a new branch. Editing the lockfile. Running the test suite. I never touched a terminal. I never touched git. This is the agent owning the seven steps I showed you."**

### 2:55 – 3:20  →  Dashboard live

*Switch to dashboard.*

> **"My dashboard, live. Active session count just incremented. The dashboard reads from the same SQLite file the orchestrator writes to — zero HTTP coupling, the bus is a shared volume."**

### 3:20 – 4:00  →  Show the completed PR

*Switch to pre-prepared completed PR tab.*

> **"Here's a PR from a session that completed earlier. One file changed. Clean diff — only the vulnerable version bumped, nothing else touched. PR description references the original issue. Tests passing."**
>
> *(beat)*
>
> **"And critically — not merged. The prompt explicitly forbids auto-merge. Humans review every merge. That's the line."**

*Switch to original GitHub issue, scroll to bot comment.*

> **"And here's the original issue, with a comment from my orchestrator linking to the PR. The loop closed itself. A human picks it up from here."**

---

## 4:00 – 4:30  →  Engineering story

*Switch to terminal, run `git log --oneline -3`*

> **"One last thing. This wasn't a clean-room demo."**
>
> *(point to commit 1)*
>
> **"First commit — initial scaffold on the Devin v1 API. It worked, but my dashboard reported false failures because v1's session statuses were ambiguous around completion."**
>
> *(point to commit 2)*
>
> **"Second commit — migrated to v3. The v3 response gives me pull requests as a first-class field on the session. PR tracking became a single lookup. Cleaner code, real bug fix."**
>
> *(point to commit 3)*
>
> **"Third commit — refined the prompt to handle JavaScript lockfiles versus Python requirements differently. Caught when Devin sensibly pushed back on running pip install against a yarn.lock. That's the exact behavior I want from a production agent — pushback, not blind compliance."**

---

## 4:30 – 5:00  →  SLIDE 4

*Switch back to deck, slide 4.*

> **"Four principles."**
>
> *(pause)*
>
> **"Pick a narrow task."**
>
> *(beat)*
>
> **"Add hard guardrails."**
>
> *(beat)*
>
> **"Make outcomes observable."**
>
> *(beat)*
>
> **"And keep humans on the decision that actually matters."**
>
> *(longer pause — let it sit)*
>
> **"That's how agents earn production trust. Thanks for watching."**

**Delivery:** Very slow on the four principles. Beat between each. Eye contact with camera. Smile once — only after "watching."

→ Stop recording within 1 second.

---

## Seven lines to memorize cold

These seven sentences carry the pitch. Everything else you can riff.

1. *"...where that work just disappears."* (end of Slide 1)
2. *"Investigate. Decide. Act."* (Slide 2)
3. *"Not features. Not customers. Hygiene."* (Slide 2)
4. *"Devin IS the engineer for tasks like this."* (Slide 3)
5. *"Humans review every merge. That's the line."* (during demo)
6. *"Pushback, not blind compliance."* (git history)
7. *"That's how agents earn production trust."* (close)

---

## Delivery rules

**Vocabulary purge — these words do NOT appear in your recording:**

- "I think" / "I believe" — just state the claim
- "kind of" / "sort of" — cut
- "basically" / "essentially" — cut
- "really" (filler) — cut
- "just" (as in "I just wanted to") — cut
- "you know" — cut
- "um" / "uh" — re-record if these creep in

**Pace:**
- Slide 1 → slow, confident
- Slide 2 → accelerate through lists, slow on punchlines
- Slide 3 → crisp, transitional
- Demo → conversational
- Git history → engineer-to-engineer, peer-level
- Slide 4 → very slow, deliberate

**Body:**
- Sit up straight. Camera at eye level. Look at the LENS, not your screen.
- Hands visible if on camera — they add expressiveness
- Smile ONCE — at the very end
- Never apologize, preface, or backtrack

**Audio:**
- External mic if available. Phone earbuds beat a laptop mic.
- Do a 30-second test recording first. Listen back.
- Record in a soft-furnished room (less echo)

---

## Pre-recording checklist

**Stack:**
- [ ] `docker compose up -d` healthy
- [ ] ngrok running, webhook configured in GitHub
- [ ] `.env` has DEVIN_API_KEY (cog_) and DEVIN_ORG_ID
- [ ] One full end-to-end practice run today that worked

**Browser tabs (in order, left to right):**
- [ ] Slide deck (Slide 1 visible)
- [ ] GitHub fork — New Issue page
- [ ] Devin UI
- [ ] Dashboard
- [ ] Pre-completed PR
- [ ] Terminal tailing logs

**Git:**
- [ ] `git log --oneline -3` shows the 3 clean commits

**Environment:**
- [ ] Phone on Do Not Disturb
- [ ] Mac Focus mode on
- [ ] Slack, email, calendar quit
- [ ] Browser bookmarks hidden (`Cmd+Shift+B`)
- [ ] Loom at 1080p, system audio on, mic on

**Performance:**
- [ ] Read the script aloud, with stopwatch, twice
- [ ] Hit 4:55 – 5:05 in practice → record
- [ ] One take if possible; restart only if you flub in first 30 seconds

---

You've built the system. You've got the deck. You've got the script.

5 minutes. One take. Go land it.
