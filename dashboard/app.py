"""
Streamlit dashboard — built to show ONE thing clearly:
   how many Devins are working in parallel, RIGHT NOW.

Layout:
  Top row: KPIs that scale tells (peak concurrency, hours saved, throughput)
  Middle:  Live concurrency timeline (Gantt chart of overlapping sessions)
  Bottom:  Session table (drill-down)
"""
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "/data/sessions.db")
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "5"))
HUMAN_MINUTES_PER_CVE = int(os.getenv("HUMAN_MINUTES_PER_CVE", "30"))

st.set_page_config(
    page_title="Vuln Remediation Pipeline",
    page_icon="🛡️",
    layout="wide",
)


def load_sessions() -> pd.DataFrame:
    if not Path(DB_PATH).exists():
        return pd.DataFrame()
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT * FROM sessions ORDER BY created_at DESC", conn
        )


def compute_mttr_minutes(df: pd.DataFrame) -> float | None:
    done = df[df["status"] == "completed"].copy()
    if done.empty:
        return None
    done["created_at"] = pd.to_datetime(done["created_at"])
    done["completed_at"] = pd.to_datetime(done["completed_at"])
    minutes = (done["completed_at"] - done["created_at"]).dt.total_seconds() / 60
    return float(minutes.mean())


def compute_peak_concurrency(df: pd.DataFrame) -> int:
    """Walk the timeline of session start/end events and find the max overlap."""
    if df.empty:
        return 0
    events: list[tuple[pd.Timestamp, int]] = []
    for _, r in df.iterrows():
        start = pd.to_datetime(r["created_at"])
        end_str = r.get("completed_at")
        end = pd.to_datetime(end_str) if pd.notna(end_str) and end_str else pd.Timestamp.now(tz="UTC")
        events.append((start, +1))
        events.append((end, -1))
    events.sort()
    peak = running = 0
    for _, delta in events:
        running += delta
        peak = max(peak, running)
    return peak


def render_timeline(df: pd.DataFrame):
    """Gantt-style timeline showing overlapping sessions = parallelism."""
    if df.empty:
        st.info("No sessions yet. The timeline will populate once webhooks fire.")
        return

    timeline_df = df.copy()
    timeline_df["start"] = pd.to_datetime(timeline_df["created_at"])
    now_utc = pd.Timestamp.now(tz="UTC")
    timeline_df["finish"] = timeline_df["completed_at"].apply(
        lambda x: pd.to_datetime(x) if pd.notna(x) and x else now_utc
    )
    # Ensure tz alignment
    if timeline_df["start"].dt.tz is None:
        timeline_df["start"] = timeline_df["start"].dt.tz_localize("UTC")
    if timeline_df["finish"].dt.tz is None:
        timeline_df["finish"] = timeline_df["finish"].dt.tz_localize("UTC")

    timeline_df["label"] = timeline_df["cve_id"] + " · " + timeline_df["package"].fillna("?")

    # Sort newest first so the most recent sessions are at the top
    timeline_df = timeline_df.sort_values("start", ascending=False)

    color_map = {
        "completed": "#22c55e",
        "running":   "#3b82f6",
        "pending":   "#a78bfa",
        "blocked":   "#f59e0b",
        "failed":    "#ef4444",
    }

    fig = px.timeline(
        timeline_df,
        x_start="start",
        x_end="finish",
        y="label",
        color="status",
        color_discrete_map=color_map,
        hover_data=["cve_id", "package", "fixed_version", "severity", "issue_number"],
    )
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_xaxes(title=None)
    fig.update_layout(
        height=max(220, 35 * len(timeline_df) + 80),
        margin=dict(l=10, r=10, t=20, b=10),
        legend_title_text="Status",
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─── HEADER ───────────────────────────────────────────────────────────────
st.title("🛡️ Vulnerability Remediation Pipeline")
st.caption("Multiple Devins working in parallel — autonomy at scale")

df = load_sessions()

# ─── KPI ROW (the parallelism story) ──────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

if df.empty:
    col1.metric("Active Now", 0)
    col2.metric("Peak Concurrency", 0)
    col3.metric("Completed PRs", 0)
    col4.metric("Hours Saved", "—")
    col5.metric("Avg MTTR", "—")
else:
    active = int((df["status"].isin(["pending", "running"])).sum())
    blocked = int((df["status"] == "blocked").sum())
    completed = int((df["status"] == "completed").sum())
    failed = int((df["status"] == "failed").sum())
    peak = compute_peak_concurrency(df)
    hours_saved = (completed * HUMAN_MINUTES_PER_CVE) / 60
    mttr = compute_mttr_minutes(df)

    col1.metric(
        "Active Now",
        active,
        help="Sessions currently pending or running",
    )
    col2.metric(
        "Peak Concurrency",
        peak,
        help="Max simultaneous Devin sessions observed — the scale story",
    )
    col3.metric("Completed PRs", completed)
    col4.metric(
        "Hours Saved",
        f"{hours_saved:.1f}",
        help=f"Completed PRs × {HUMAN_MINUTES_PER_CVE} min human estimate",
    )
    col5.metric(
        "Avg MTTR",
        f"{mttr:.1f} min" if mttr is not None else "—",
        help="Mean time from issue created to PR opened",
    )

    if blocked:
        st.warning(f"⚠️ {blocked} session(s) need human attention (waiting for user/approval).")

st.divider()

# ─── PARALLELISM TIMELINE ─────────────────────────────────────────────────
st.subheader("⚡ Concurrency timeline")
st.caption("Overlapping bars = Devins working at the same time.")
render_timeline(df)

st.divider()

# ─── SESSION TABLE ────────────────────────────────────────────────────────
st.subheader("📋 Session history")
if df.empty:
    st.info(
        "No sessions yet. Run `python3 scripts/scale_demo.py 5` to fire 5 issues "
        "in parallel, or create a single GitHub issue with the "
        "`vuln-auto-remediate` label."
    )
else:
    display = df.copy()
    display["pr_url"] = display["pr_url"].fillna("")
    display["completed_at"] = display["completed_at"].fillna("")
    display["duration_min"] = ""
    mask = display["completed_at"] != ""
    if mask.any():
        start = pd.to_datetime(display.loc[mask, "created_at"])
        end = pd.to_datetime(display.loc[mask, "completed_at"])
        display.loc[mask, "duration_min"] = (
            ((end - start).dt.total_seconds() / 60).round(1).astype(str)
        )

    st.dataframe(
        display[[
            "cve_id", "package", "fixed_version", "severity", "status",
            "issue_number", "pr_url", "devin_session_url",
            "created_at", "duration_min",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "pr_url": st.column_config.LinkColumn("PR", display_text="View PR"),
            "devin_session_url": st.column_config.LinkColumn(
                "Devin", display_text="Open"
            ),
            "issue_number": st.column_config.NumberColumn("Issue #"),
            "duration_min": st.column_config.TextColumn("Duration (min)"),
        },
    )

st.caption(f"Auto-refreshes every {REFRESH_SECONDS}s.")

time.sleep(REFRESH_SECONDS)
st.rerun()
