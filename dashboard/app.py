"""Streamlit dashboard — answers 'how do I know this is working?' for a VP."""
import os
import sqlite3
import time
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = os.getenv("DB_PATH", "/data/sessions.db")
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "10"))

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


st.title("🛡️ Vulnerability Remediation Pipeline")
st.caption("Event-driven CVE remediation via Devin v3")

df = load_sessions()

col1, col2, col3, col4 = st.columns(4)
if df.empty:
    col1.metric("Active Sessions", 0)
    col2.metric("Completed PRs", 0)
    col3.metric("Success Rate", "—")
    col4.metric("Avg MTTR", "—")
else:
    active = int((df["status"].isin(["pending", "running"])).sum())
    blocked = int((df["status"] == "blocked").sum())
    completed = int((df["status"] == "completed").sum())
    failed = int((df["status"] == "failed").sum())
    total_done = completed + failed
    success_rate = (completed / total_done * 100) if total_done else 0
    mttr = compute_mttr_minutes(df)

    col1.metric("Active Sessions", active, help="Pending + running sessions")
    col2.metric("Completed PRs", completed)
    col3.metric(
        "Success Rate",
        f"{success_rate:.0f}%" if total_done else "—",
        help="Completed ÷ (completed + failed)",
    )
    col4.metric(
        "Avg MTTR",
        f"{mttr:.1f} min" if mttr is not None else "—",
        help="Mean time from issue created to PR opened",
    )

    if blocked:
        st.warning(f"⚠️ {blocked} session(s) need human attention (waiting for user/approval).")

st.divider()

st.subheader("Session History")
if df.empty:
    st.info(
        "No sessions yet. Create a GitHub issue with the "
        "`vuln-auto-remediate` label in your Superset fork to trigger the pipeline."
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
