// Pitch deck for Devin Vulnerability Remediator
// Audience: VP of Engineering + senior ICs at Cognition

const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Mani Kandan";
pres.title = "Vulnerability Remediation, Autonomously";

const C = {
  bg:        "0A0E27",
  bgPanel:   "141937",
  text:      "F8FAFC",
  textMuted: "94A3B8",
  accent:    "FF6B35",
  green:     "10B981",
  divider:   "1E2547",
};

const FONT_HEAD = "Calibri";
const FONT_BODY = "Calibri";

function addFooter(slide, pageNum) {
  slide.addText("Mani Kandan  ·  Devin Vulnerability Remediator", {
    x: 0.5, y: 5.25, w: 7, h: 0.25,
    fontSize: 9, fontFace: FONT_BODY, color: C.textMuted, align: "left",
  });
  slide.addText(`${pageNum} / 4`, {
    x: 8.5, y: 5.25, w: 1, h: 0.25,
    fontSize: 9, fontFace: FONT_BODY, color: C.textMuted, align: "right",
  });
}

// ============================================================
// SLIDE 1 — THE PROBLEM
// ============================================================
const s1 = pres.addSlide();
s1.background = { color: C.bg };

s1.addText("THE PROBLEM", {
  x: 0.75, y: 0.6, w: 8.5, h: 0.4,
  fontSize: 11, fontFace: FONT_HEAD, color: C.accent, bold: true,
  charSpacing: 8, align: "left",
});

s1.addText("Every engineering org has", {
  x: 0.75, y: 1.4, w: 8.5, h: 0.7,
  fontSize: 36, fontFace: FONT_HEAD, color: C.text, bold: true, align: "left",
});
s1.addText("a security debt backlog.", {
  x: 0.75, y: 2.0, w: 8.5, h: 0.7,
  fontSize: 36, fontFace: FONT_HEAD, color: C.text, bold: true, align: "left",
});

s1.addText("Nobody is excited to work on it.", {
  x: 0.75, y: 2.9, w: 8.5, h: 0.5,
  fontSize: 20, fontFace: FONT_BODY, color: C.textMuted, italic: true, align: "left",
});

s1.addShape(pres.shapes.LINE, {
  x: 0.75, y: 3.7, w: 1.5, h: 0,
  line: { color: C.accent, width: 2 },
});

s1.addText("What if the work just… disappeared?", {
  x: 0.75, y: 3.95, w: 8.5, h: 0.7,
  fontSize: 28, fontFace: FONT_HEAD, color: C.accent, bold: true, align: "left",
});

addFooter(s1, 1);

// ============================================================
// SLIDE 2 — KNOWLEDGE WORK LOOP
// ============================================================
const s2 = pres.addSlide();
s2.background = { color: C.bg };

s2.addText("THE PATTERN", {
  x: 0.5, y: 0.4, w: 9, h: 0.35,
  fontSize: 11, fontFace: FONT_HEAD, color: C.accent, bold: true,
  charSpacing: 8, align: "left",
});

s2.addText("30%", {
  x: 0.5, y: 1.1, w: 4.5, h: 2.0,
  fontSize: 140, fontFace: FONT_HEAD, color: C.accent, bold: true,
  align: "center", valign: "middle",
});

s2.addText("of senior engineering time", {
  x: 0.5, y: 3.05, w: 4.5, h: 0.35,
  fontSize: 14, fontFace: FONT_BODY, color: C.text, align: "center",
});
s2.addText("is spent in one loop", {
  x: 0.5, y: 3.35, w: 4.5, h: 0.35,
  fontSize: 14, fontFace: FONT_BODY, color: C.text, align: "center",
});

s2.addText("INVESTIGATE  →  DECIDE  →  ACT", {
  x: 5.2, y: 1.1, w: 4.5, h: 0.5,
  fontSize: 18, fontFace: FONT_HEAD, color: C.text, bold: true,
  charSpacing: 2, align: "left",
});

const steps = [
  "Read the alert.",
  "Check the dependency tree.",
  "Confirm the fix exists.",
  "Run the tests.",
  "Open the PR.",
];
steps.forEach((step, i) => {
  s2.addText(step, {
    x: 5.2, y: 1.75 + i * 0.32, w: 4.5, h: 0.3,
    fontSize: 14, fontFace: FONT_BODY, color: C.textMuted, align: "left",
  });
});

s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 4.4, w: 9, h: 0.7,
  fill: { color: C.bgPanel },
  line: { color: C.divider, width: 0 },
});
s2.addText([
  { text: "For Apache Superset alone:  ", options: { color: C.textMuted, fontSize: 14 } },
  { text: "thousands of hours per year", options: { color: C.text, fontSize: 14, bold: true } },
  { text: "  on dependency hygiene.", options: { color: C.textMuted, fontSize: 14 } },
], {
  x: 0.5, y: 4.4, w: 9, h: 0.7,
  fontFace: FONT_BODY, align: "center", valign: "middle",
});

addFooter(s2, 2);

// ============================================================
// SLIDE 3 — WHY DEVIN + ARCHITECTURE
// ============================================================
const s3 = pres.addSlide();
s3.background = { color: C.bg };

s3.addText("THE SOLUTION", {
  x: 0.5, y: 0.35, w: 9, h: 0.35,
  fontSize: 11, fontFace: FONT_HEAD, color: C.accent, bold: true,
  charSpacing: 8, align: "left",
});

// LEFT COLUMN
s3.addText("AUTOCOMPLETE", {
  x: 0.5, y: 0.85, w: 4.3, h: 0.35,
  fontSize: 11, fontFace: FONT_HEAD, color: C.textMuted, bold: true,
  charSpacing: 4, align: "left",
});
s3.addText("Copilot, Cursor", {
  x: 0.5, y: 1.2, w: 4.3, h: 0.4,
  fontSize: 16, fontFace: FONT_BODY, color: C.text, italic: true, align: "left",
});
s3.addText("Helps a human type faster.", {
  x: 0.5, y: 1.6, w: 4.3, h: 0.35,
  fontSize: 13, fontFace: FONT_BODY, color: C.textMuted, align: "left",
});
s3.addText("Augments the keystroke.", {
  x: 0.5, y: 1.95, w: 4.3, h: 0.35,
  fontSize: 13, fontFace: FONT_BODY, color: C.textMuted, align: "left",
});

// Vertical divider
s3.addShape(pres.shapes.LINE, {
  x: 5.0, y: 0.95, w: 0, h: 1.5,
  line: { color: C.divider, width: 1 },
});

// RIGHT COLUMN
s3.addText("AGENT", {
  x: 5.3, y: 0.85, w: 4.2, h: 0.35,
  fontSize: 11, fontFace: FONT_HEAD, color: C.accent, bold: true,
  charSpacing: 4, align: "left",
});
s3.addText("Devin", {
  x: 5.3, y: 1.2, w: 4.2, h: 0.4,
  fontSize: 16, fontFace: FONT_BODY, color: C.text, italic: true, align: "left",
});
s3.addText("IS the engineer for narrow tasks.", {
  x: 5.3, y: 1.6, w: 4.2, h: 0.35,
  fontSize: 13, fontFace: FONT_BODY, color: C.text, align: "left",
});
s3.addText("Owns the end-to-end loop.", {
  x: 5.3, y: 1.95, w: 4.2, h: 0.35,
  fontSize: 13, fontFace: FONT_BODY, color: C.text, align: "left",
});

s3.addShape(pres.shapes.LINE, {
  x: 0.5, y: 2.65, w: 9, h: 0,
  line: { color: C.divider, width: 1 },
});

s3.addText("THE PIPELINE", {
  x: 0.5, y: 2.8, w: 9, h: 0.3,
  fontSize: 11, fontFace: FONT_HEAD, color: C.textMuted, bold: true,
  charSpacing: 4, align: "left",
});

const nodes = [
  { label: "Trivy",          sub: "scan" },
  { label: "GitHub",         sub: "issue" },
  { label: "Webhook",        sub: "→ FastAPI" },
  { label: "Orchestrator",   sub: "v3 API" },
  { label: "Devin",          sub: "session", highlight: true },
  { label: "Pull Request",   sub: "review", green: true },
  { label: "Dashboard",      sub: "live" },
];

const nodeW = 1.15;
const nodeH = 0.9;
const gap = 0.15;
const totalW = nodes.length * nodeW + (nodes.length - 1) * gap;
const startX = (10 - totalW) / 2;
const nodeY = 3.3;

nodes.forEach((node, i) => {
  const x = startX + i * (nodeW + gap);
  const fillColor = node.highlight ? C.accent : node.green ? C.green : C.bgPanel;
  const textColor = node.highlight || node.green ? C.bg : C.text;
  const subColor = node.highlight || node.green ? C.bg : C.textMuted;

  s3.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: x, y: nodeY, w: nodeW, h: nodeH,
    fill: { color: fillColor },
    line: { color: node.highlight || node.green ? fillColor : C.divider, width: 1 },
    rectRadius: 0.08,
  });
  s3.addText(node.label, {
    x: x, y: nodeY + 0.12, w: nodeW, h: 0.35,
    fontSize: 12, fontFace: FONT_HEAD, color: textColor, bold: true,
    align: "center", valign: "middle", margin: 0,
  });
  s3.addText(node.sub, {
    x: x, y: nodeY + 0.5, w: nodeW, h: 0.3,
    fontSize: 9, fontFace: FONT_BODY, color: subColor,
    italic: true, align: "center", valign: "middle", margin: 0,
  });

  if (i < nodes.length - 1) {
    s3.addShape(pres.shapes.RIGHT_TRIANGLE, {
      x: x + nodeW + 0.02, y: nodeY + nodeH / 2 - 0.05, w: 0.11, h: 0.1,
      fill: { color: C.textMuted },
      line: { color: C.textMuted, width: 0 },
      rotate: 90,
    });
  }
});

s3.addText("Event-driven  ·  Webhook-triggered  ·  Observable end-to-end", {
  x: 0.5, y: 4.55, w: 9, h: 0.3,
  fontSize: 10, fontFace: FONT_BODY, color: C.textMuted,
  italic: true, align: "center",
});

addFooter(s3, 3);

// ============================================================
// SLIDE 4 — THE CLOSE
// ============================================================
const s4 = pres.addSlide();
s4.background = { color: C.bg };

s4.addText("HOW AGENTS EARN PRODUCTION TRUST", {
  x: 0.5, y: 0.7, w: 9, h: 0.4,
  fontSize: 12, fontFace: FONT_HEAD, color: C.accent, bold: true,
  charSpacing: 6, align: "center",
});

const closingLines = [
  "Pick a narrow task.",
  "Add hard guardrails.",
  "Make outcomes observable.",
  "Keep humans on the decision that matters.",
];

closingLines.forEach((line, i) => {
  s4.addText(line, {
    x: 0.5, y: 1.6 + i * 0.6, w: 9, h: 0.55,
    fontSize: 26, fontFace: FONT_HEAD, color: C.text, bold: true,
    align: "center", valign: "middle",
  });
});

s4.addShape(pres.shapes.LINE, {
  x: 4.0, y: 4.25, w: 2, h: 0,
  line: { color: C.accent, width: 2 },
});

s4.addText("Thank you.", {
  x: 0.5, y: 4.45, w: 9, h: 0.5,
  fontSize: 22, fontFace: FONT_HEAD, color: C.accent,
  italic: true, align: "center",
});

addFooter(s4, 4);

pres.writeFile({ fileName: "/home/claude/pitch_deck.pptx" })
  .then((file) => console.log("Written:", file));
