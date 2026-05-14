# 🎨 Slide Deck — Content Reference

The actual deck is at `../deck.pptx` (4 slides, 16:9, dark theme).
This file documents what each slide contains so you can rebuild or modify it.

**Theme:** Midnight Authority
- Background: deep navy `#0A0E27`
- Text: off-white `#F5F5F7`, muted `#8B95A7`
- Accent: orange `#FF6B35`
- Panels: `#151A36`

---

## Slide 1 — The Problem

```
[shield icon]  VULNERABILITY REMEDIATION

Every engineering organization
carries a security debt backlog.

Nobody is excited to work on it.


What if the work just disappeared?

                                          Mani Kandan · Devin Take-Home · 5 min
```

Hook line ("disappeared?") is in orange. Held 0:00–0:45.

---

## Slide 2 — The Pattern

```
THE PATTERN

30%                  [INVESTIGATE] → [DECIDE] → [ACT]
of senior 
engineering          Read the alert.
time spent           Check the dependency tree.
in one loop.         Confirm the fix exists.
                     Run the tests.
                     Open the PR.

┌──────────────────────────────────────────────────┐
│ FOR APACHE SUPERSET ALONE                        │
│ Thousands of hours per year on dependency        │
│ hygiene — not features, not customers.           │
└──────────────────────────────────────────────────┘
```

Big 30% in orange on the left. Three pill boxes (INVESTIGATE → DECIDE → ACT) on the right with orange borders. Held 0:45–1:30.

---

## Slide 3 — Why Devin + Architecture

```
WHY DEVIN  ·  THE SYSTEM

AUTOCOMPLETE              │  AGENT
Copilot · Cursor          │  Devin
Helps a human type faster.│  IS the engineer for narrow tasks.

ARCHITECTURE

[Trivy]→[GitHub Issue]→[Orchestrator]→[Devin v3]→[Pull Request]
                              │
                          [Dashboard]

         Event-driven  ·  Webhook-triggered  ·  Observable end-to-end
```

Left vs right comparison up top. Architecture flow below with each box outlined in its semantic color (blue for orchestrator, orange for Devin, green for PR). Held 1:30–2:00.

---

## Slide 4 — The Close

```
HOW AGENTS EARN PRODUCTION TRUST

01    Pick a narrow task.
─────────────────────────────────────
02    Add hard guardrails.
─────────────────────────────────────
03    Make outcomes observable.
─────────────────────────────────────
04    Keep humans on the decision that matters.


              Thanks for watching.
```

Four principles, each on its own row, separated by thin dividers. Held 4:30–5:00.

---

## Rebuilding the deck

If you want to modify the deck, the source script that generated `deck.pptx` is included in this project's history. It uses Node + `pptxgenjs`. To regenerate:

```bash
npm install -g pptxgenjs react react-dom sharp react-icons
node build_deck.js
```

For most edits, just open `deck.pptx` directly in PowerPoint or Keynote — you can tweak text, colors, and positions without re-running the script.
